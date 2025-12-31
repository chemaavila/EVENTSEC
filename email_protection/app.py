import asyncio
import base64
import json
import os
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse
import msal
from google.auth.transport.requests import Request as GAuthRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

load_dotenv()

APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8100")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", APP_BASE_URL)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", f"{APP_BASE_URL}/auth/google/callback")
GMAIL_PUBSUB_TOPIC = os.getenv("GMAIL_PUBSUB_TOPIC", "")

MS_CLIENT_ID = os.getenv("MS_CLIENT_ID", "")
MS_CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET", "")
MS_TENANT = os.getenv("MS_TENANT", "common")
MS_REDIRECT_URI = os.getenv("MS_REDIRECT_URI", f"{APP_BASE_URL}/auth/microsoft/callback")

DB_PATH = os.getenv("TOKEN_DB_PATH", "tokens.db")

GOOGLE_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
MS_SCOPES = ["offline_access", "User.Read", "Mail.Read"]

OAUTH_STATE_TTL_SECONDS = int(os.getenv("OAUTH_STATE_TTL_SECONDS", "600"))
OAUTH_STATE_CLEANUP_INTERVAL_SECONDS = int(os.getenv("OAUTH_STATE_CLEANUP_INTERVAL_SECONDS", "300"))
# TODO: Consider moving OAuth state storage to persistent backend (Redis/DB) to survive restarts.
OAUTH_STATE: Dict[str, Dict[str, Any]] = {}

def _oauth_state_expired(entry: Dict[str, Any], now: Optional[datetime] = None) -> bool:
    created_at = entry.get("created_at")
    if not isinstance(created_at, datetime):
        return True
    now = now or datetime.now(timezone.utc)
    return now - created_at > timedelta(seconds=OAUTH_STATE_TTL_SECONDS)

def _purge_expired_oauth_state(now: Optional[datetime] = None) -> int:
    now = now or datetime.now(timezone.utc)
    expired = [key for key, entry in OAUTH_STATE.items() if _oauth_state_expired(entry, now)]
    for key in expired:
        OAUTH_STATE.pop(key, None)
    return len(expired)

def _get_oauth_state(state: str) -> Optional[Dict[str, Any]]:
    entry = OAUTH_STATE.get(state)
    if not entry:
        return None
    if _oauth_state_expired(entry):
        OAUTH_STATE.pop(state, None)
        return None
    return entry

async def _oauth_state_cleanup_loop() -> None:
    while True:
        await asyncio.sleep(OAUTH_STATE_CLEANUP_INTERVAL_SECONDS)
        _purge_expired_oauth_state()

app = FastAPI(title="Email Protection Connectors & Analyzer")

def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    conn = db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tokens (
            provider TEXT NOT NULL,
            mailbox  TEXT NOT NULL,
            token_json TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (provider, mailbox)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS kv (
            k TEXT PRIMARY KEY,
            v TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()

def set_token(provider: str, mailbox: str, token_json: str) -> None:
    conn = db()
    conn.execute(
        "INSERT OR REPLACE INTO tokens(provider, mailbox, token_json, updated_at) VALUES (?,?,?,?)",
        (provider, mailbox, token_json, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()

def get_token(provider: str, mailbox: str) -> Optional[str]:
    conn = db()
    row = conn.execute(
        "SELECT token_json FROM tokens WHERE provider=? AND mailbox=?",
        (provider, mailbox),
    ).fetchone()
    conn.close()
    return row["token_json"] if row else None

def set_kv(k: str, v: str) -> None:
    conn = db()
    conn.execute("INSERT OR REPLACE INTO kv(k, v) VALUES (?,?)", (k, v))
    conn.commit()
    conn.close()

def get_kv(k: str) -> Optional[str]:
    conn = db()
    row = conn.execute("SELECT v FROM kv WHERE k=?", (k,)).fetchone()
    conn.close()
    return row["v"] if row else None

URL_RE = re.compile(r"(https?://[^\s<>\"]+)", re.IGNORECASE)
DANGEROUS_EXT = {
    ".exe", ".scr", ".js", ".vbs", ".vbe", ".ps1", ".bat", ".cmd", ".lnk",
    ".iso", ".img", ".hta", ".msi", ".jar", ".wsf",
}
URL_SHORTENERS = {
    "bit.ly", "t.co", "tinyurl.com", "goo.gl", "ow.ly", "is.gd", "cutt.ly",
    "rebrand.ly",
}

def domain_from_email(addr: str) -> str:
    m = re.search(r"@([A-Za-z0-9\.\-]+)", (addr or "").strip())
    return (m.group(1) if m else "").lower()

def domain_from_url(url: str) -> str:
    try:
        no_proto = url.split("://", 1)[1]
        host = no_proto.split("/", 1)[0]
        host = host.split(":", 1)[0]
        return host.lower()
    except Exception:
        return ""

def extract_urls(text: str) -> List[str]:
    if not text:
        return []
    return list({u.rstrip(").,]\"'") for u in URL_RE.findall(text)})

def analyze_message(
    provider: str,
    mailbox: str,
    msg_id: str,
    subject: str,
    from_addr: str,
    reply_to: str,
    body_text: str,
    attachment_names: List[str],
) -> Dict[str, Any]:
    findings: List[str] = []
    score = 0

    from_domain = domain_from_email(from_addr)
    reply_domain = domain_from_email(reply_to) if reply_to else ""

    if reply_to and reply_domain and from_domain and reply_domain != from_domain:
        findings.append(f"Reply-To mismatch ({reply_domain} vs {from_domain})")
        score += 2

    if "xn--" in from_domain:
        findings.append("Sender domain uses punycode")
        score += 2

    urls = extract_urls(body_text or "")
    url_domains = [domain_from_url(u) for u in urls]
    for d in url_domains:
        if "xn--" in d:
            findings.append("URL contains punycode")
            score += 2
        if d in URL_SHORTENERS:
            findings.append(f"Shortened URL detected ({d})")
            score += 1

    for name in attachment_names:
        lower = (name or "").lower()
        for ext in DANGEROUS_EXT:
            if lower.endswith(ext):
                findings.append(f"Attachment with dangerous extension ({ext}): {name}")
                score += 3
                break

    if subject and re.search(
        r"\b(urgent|verify|password|invoice|pay|blocked|suspend)\b", subject, re.IGNORECASE
    ):
        findings.append("Subject includes phishing keywords")
        score += 1

    verdict = "low"
    if score >= 5:
        verdict = "high"
    elif score >= 2:
        verdict = "medium"

    return {
        "provider": provider,
        "mailbox": mailbox,
        "message_id": msg_id,
        "subject": subject,
        "from": from_addr,
        "reply_to": reply_to,
        "urls": urls,
        "attachments": attachment_names,
        "score": score,
        "verdict": verdict,
        "findings": findings,
    }

def google_flow() -> Flow:
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(500, "Missing GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET")
    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [GOOGLE_REDIRECT_URI],
        }
    }
    return Flow.from_client_config(client_config, scopes=GOOGLE_SCOPES, redirect_uri=GOOGLE_REDIRECT_URI)

def gmail_service_from_stored(mailbox: str) -> Any:
    token_json = get_token("google", mailbox)
    if not token_json:
        raise HTTPException(404, f"No Google token for mailbox={mailbox}")
    creds = Credentials.from_authorized_user_info(json.loads(token_json), scopes=GOOGLE_SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(GAuthRequest())
        set_token("google", mailbox, creds.to_json())
    return build("gmail", "v1", credentials=creds, cache_discovery=False)

def gmail_decode_part(data_b64url: str) -> str:
    if not data_b64url:
        return ""
    padded = data_b64url + "=" * (-len(data_b64url) % 4)
    raw = base64.urlsafe_b64decode(padded.encode("utf-8"))
    try:
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return raw.decode("latin-1", errors="replace")

def gmail_extract_body(payload: Dict[str, Any]) -> str:
    if not payload:
        return ""
    parts = payload.get("parts", [])
    body = payload.get("body", {}) or {}
    if body.get("data"):
        return gmail_decode_part(body["data"])
    stack = list(parts)
    best_html = ""
    best_text = ""
    while stack:
        p = stack.pop()
        mime = (p.get("mimeType") or "").lower()
        b = p.get("body", {}) or {}
        if mime == "text/plain" and b.get("data"):
            best_text = gmail_decode_part(b["data"])
        if mime == "text/html" and b.get("data"):
            best_html = gmail_decode_part(b["data"])
        for ch in (p.get("parts") or []):
            stack.append(ch)
    return best_text or best_html or ""

def msal_app(cache: Optional[msal.SerializableTokenCache] = None) -> msal.ConfidentialClientApplication:
    if not MS_CLIENT_ID or not MS_CLIENT_SECRET:
        raise HTTPException(500, "Missing MS_CLIENT_ID/MS_CLIENT_SECRET")
    authority = f"https://login.microsoftonline.com/{MS_TENANT}"
    return msal.ConfidentialClientApplication(
        client_id=MS_CLIENT_ID,
        client_credential=MS_CLIENT_SECRET,
        authority=authority,
        token_cache=cache,
    )

def graph_get_access_token(mailbox: str) -> str:
    raw = get_token("microsoft", mailbox)
    if not raw:
        raise HTTPException(404, f"No Microsoft token for mailbox={mailbox}")
    cache = msal.SerializableTokenCache()
    cache.deserialize(raw)
    app_ = msal_app(cache)
    accounts = app_.get_accounts()
    if not accounts:
        raise HTTPException(401, "No account in MSAL cache")
    result = app_.acquire_token_silent(MS_SCOPES, account=accounts[0])
    if not result or "access_token" not in result:
        raise HTTPException(401, "Unable to acquire silent token")
    if cache.has_state_changed:
        set_token("microsoft", mailbox, cache.serialize())
    return result["access_token"]

def graph_get_me(access_token: str) -> Dict[str, Any]:
    r = requests.get(
        "https://graph.microsoft.com/v1.0/me?$select=id,displayName,mail,userPrincipalName",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()

def graph_list_inbox_messages(access_token: str, top: int = 10) -> List[Dict[str, Any]]:
    url = "https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages"
    params = {
        "$top": str(top),
        "$select": "id,subject,from,replyTo,receivedDateTime,bodyPreview,hasAttachments,internetMessageId",
        "$orderby": "receivedDateTime desc",
    }
    r = requests.get(url, headers={"Authorization": f"Bearer {access_token}"}, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("value", [])

def graph_list_attachments(access_token: str, message_id: str) -> List[str]:
    url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments"
    params = {"$select": "name,contentType,size,isInline"}
    r = requests.get(url, headers={"Authorization": f"Bearer {access_token}"}, params=params, timeout=30)
    if r.status_code == 404:
        return []
    r.raise_for_status()
    items = r.json().get("value", [])
    names: List[str] = []
    for it in items:
        name = it.get("name") or ""
        if name:
            names.append(name)
    return names

@app.on_event("startup")
def _startup():
    init_db()
    asyncio.create_task(_oauth_state_cleanup_loop())

@app.get("/health")
def health():
    return {"ok": True, "time": datetime.now(timezone.utc).isoformat()}

@app.get("/auth/google/start")
def google_start():
    flow = google_flow()
    state = secrets.token_urlsafe(24)
    flow.state = state
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    _purge_expired_oauth_state()
    OAUTH_STATE[state] = {"provider": "google", "created_at": datetime.now(timezone.utc)}
    return RedirectResponse(auth_url)

@app.get("/auth/google/callback")
def google_callback(request: Request):
    state = request.query_params.get("state")
    code = request.query_params.get("code")
    if not state or not _get_oauth_state(state):
        raise HTTPException(400, "Invalid state")
    OAUTH_STATE.pop(state, None)
    if not code:
        raise HTTPException(400, "Missing code")
    flow = google_flow()
    flow.fetch_token(code=code)
    creds = flow.credentials
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    profile = service.users().getProfile(userId="me").execute()
    mailbox = profile.get("emailAddress", "me")
    set_token("google", mailbox, creds.to_json())
    if profile.get("historyId"):
        set_kv(f"gmail_history:{mailbox}", str(profile["historyId"]))
    return JSONResponse({"linked": True, "provider": "google", "mailbox": mailbox})

@app.get("/auth/microsoft/start")
def microsoft_start():
    state = secrets.token_urlsafe(24)
    cache = msal.SerializableTokenCache()
    app_ = msal_app(cache)
    auth_url = app_.get_authorization_request_url(
        scopes=MS_SCOPES,
        redirect_uri=MS_REDIRECT_URI,
        state=state,
        prompt="select_account",
    )
    _purge_expired_oauth_state()
    OAUTH_STATE[state] = {"provider": "microsoft", "created_at": datetime.now(timezone.utc)}
    return RedirectResponse(auth_url)

@app.get("/auth/microsoft/callback")
def microsoft_callback(request: Request):
    state = request.query_params.get("state")
    code = request.query_params.get("code")
    if not state or not _get_oauth_state(state):
        raise HTTPException(400, "Invalid state")
    OAUTH_STATE.pop(state, None)
    if not code:
        raise HTTPException(400, "Missing code")
    cache = msal.SerializableTokenCache()
    app_ = msal_app(cache)
    result = app_.acquire_token_by_authorization_code(
        code=code,
        scopes=MS_SCOPES,
        redirect_uri=MS_REDIRECT_URI,
    )
    if "access_token" not in result:
        raise HTTPException(400, f"MSAL error: {result.get('error')} {result.get('error_description')}")
    me = graph_get_me(result["access_token"])
    mailbox = (me.get("mail") or me.get("userPrincipalName") or me.get("id") or "me")
    set_token("microsoft", mailbox, cache.serialize())
    return JSONResponse({"linked": True, "provider": "microsoft", "mailbox": mailbox, "me": me})

@app.post("/sync/google")
def sync_google(mailbox: str, top: int = 10):
    service = gmail_service_from_stored(mailbox)
    resp = service.users().messages().list(
        userId="me",
        labelIds=["INBOX"],
        maxResults=top,
    ).execute()
    msgs = resp.get("messages", [])
    out: List[Dict[str, Any]] = []
    for m in msgs:
        mid = m["id"]
        full = service.users().messages().get(userId="me", id=mid, format="full").execute()
        payload = full.get("payload", {}) or {}
        headers = payload.get("headers", []) or []
        h = {x.get("name", "").lower(): x.get("value", "") for x in headers}
        subject = h.get("subject", "")
        from_addr = h.get("from", "")
        reply_to = h.get("reply-to", "")
        body = gmail_extract_body(payload)
        attachment_names: List[str] = []
        stack = list(payload.get("parts", []) or [])
        while stack:
            p = stack.pop()
            filename = p.get("filename") or ""
            if filename:
                attachment_names.append(filename)
            for ch in (p.get("parts") or []):
                stack.append(ch)
        out.append(
            analyze_message(
                provider="google",
                mailbox=mailbox,
                msg_id=mid,
                subject=subject,
                from_addr=from_addr,
                reply_to=reply_to,
                body_text=body,
                attachment_names=attachment_names,
            )
        )
    return {"count": len(out), "results": out}

@app.post("/sync/microsoft")
def sync_microsoft(mailbox: str, top: int = 10, fetch_attachments: bool = True):
    access_token = graph_get_access_token(mailbox)
    msgs = graph_list_inbox_messages(access_token, top=top)
    out: List[Dict[str, Any]] = []
    for m in msgs:
        mid = m.get("id", "")
        subject = m.get("subject", "")
        from_addr = (m.get("from", {}) or {}).get("emailAddress", {}).get("address", "") or ""
        reply_to_list = m.get("replyTo") or []
        reply_to = ""
        if reply_to_list:
            reply_to = (reply_to_list[0].get("emailAddress", {}) or {}).get("address", "") or ""
        body_text = m.get("bodyPreview", "") or ""
        attachment_names: List[str] = []
        if fetch_attachments and m.get("hasAttachments") and mid:
            attachment_names = graph_list_attachments(access_token, mid)
        out.append(
            analyze_message(
                provider="microsoft",
                mailbox=mailbox,
                msg_id=mid,
                subject=subject,
                from_addr=from_addr,
                reply_to=reply_to,
                body_text=body_text,
                attachment_names=attachment_names,
            )
        )
    return {"count": len(out), "results": out}

@app.get("/webhook/microsoft")
@app.post("/webhook/microsoft")
async def webhook_microsoft(request: Request):
    vt = request.query_params.get("validationToken")
    if vt:
        return PlainTextResponse(vt, status_code=200)
    body = await request.json()
    notifications = body.get("value", [])
    return {"ok": True, "received": len(notifications), "sample": notifications[:1]}

@app.post("/subscribe/microsoft")
def subscribe_microsoft(mailbox: str):
    access_token = graph_get_access_token(mailbox)
    notification_url = f"{PUBLIC_BASE_URL}/webhook/microsoft"
    expiration = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    payload = {
        "changeType": "created,updated",
        "notificationUrl": notification_url,
        "resource": "me/mailFolders('Inbox')/messages",
        "expirationDateTime": expiration,
        "clientState": secrets.token_urlsafe(16),
    }
    r = requests.post(
        "https://graph.microsoft.com/v1.0/subscriptions",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    if r.status_code >= 400:
        raise HTTPException(r.status_code, f"Graph error: {r.text}")
    return r.json()

@app.post("/subscribe/google_watch")
def subscribe_google_watch(mailbox: str, label_ids: List[str] = ["INBOX"]):
    if not GMAIL_PUBSUB_TOPIC:
        raise HTTPException(500, "Missing GMAIL_PUBSUB_TOPIC")
    service = gmail_service_from_stored(mailbox)
    body = {"topicName": GMAIL_PUBSUB_TOPIC, "labelIds": label_ids}
    resp = service.users().watch(userId="me", body=body).execute()
    if "historyId" in resp:
        set_kv(f"gmail_history:{mailbox}", str(resp["historyId"]))
    return resp

@app.post("/webhook/google_pubsub")
async def webhook_google_pubsub(request: Request):
    body = await request.json()
    msg = body.get("message", {})
    data_b64 = msg.get("data", "")
    if not data_b64:
        return {"ok": True, "note": "no data"}
    raw = base64.b64decode(data_b64).decode("utf-8", errors="replace")
    payload = json.loads(raw)
    mailbox = payload.get("emailAddress") or "me"
    new_history_id = str(payload.get("historyId") or "")
    service = gmail_service_from_stored(mailbox)
    last = get_kv(f"gmail_history:{mailbox}")
    if not last:
        if new_history_id:
            set_kv(f"gmail_history:{mailbox}", new_history_id)
        return {"ok": True, "note": "no previous historyId"}
    hist = service.users().history().list(
        userId="me",
        startHistoryId=last,
        historyTypes=["messageAdded"],
    ).execute()
    changed: List[str] = []
    for h in (hist.get("history") or []):
        for added in (h.get("messagesAdded") or []):
            mid = (added.get("message") or {}).get("id")
            if mid:
                changed.append(mid)
    results: List[Dict[str, Any]] = []
    for mid in changed[:20]:
        full = service.users().messages().get(userId="me", id=mid, format="full").execute()
        payload2 = full.get("payload", {}) or {}
        headers = payload2.get("headers", []) or []
        hh = {x.get("name", "").lower(): x.get("value", "") for x in headers}
        subject = hh.get("subject", "")
        from_addr = hh.get("from", "")
        reply_to = hh.get("reply-to", "")
        body_text = gmail_extract_body(payload2)
        attachment_names: List[str] = []
        stack = list(payload2.get("parts", []) or [])
        while stack:
            p = stack.pop()
            filename = p.get("filename") or ""
            if filename:
                attachment_names.append(filename)
            for ch in (p.get("parts") or []):
                stack.append(ch)
        results.append(
            analyze_message(
                provider="google",
                mailbox=mailbox,
                msg_id=mid,
                subject=subject,
                from_addr=from_addr,
                reply_to=reply_to,
                body_text=body_text,
                attachment_names=attachment_names,
            )
        )
    if new_history_id:
        set_kv(f"gmail_history:{mailbox}", new_history_id)
    return {"ok": True, "processed": len(results), "results": results}

