import asyncio
import base64
import csv
import io
import json
import os
import re
import secrets
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from email.utils import getaddresses
from typing import Any, Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse
import msal
from pydantic import BaseModel, Field, ConfigDict
from google.auth.transport.requests import Request as GAuthRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from email_security import email_security_router, init_email_security_db

load_dotenv()

def _env(primary: str, fallback: str | None = None, default: str = "") -> str:
    value = os.getenv(primary)
    if value:
        return value
    if fallback:
        fallback_value = os.getenv(fallback)
        if fallback_value:
            return fallback_value
    return default

APP_BASE_URL = _env("APP_BASE_URL", "EMAIL_PROTECT_APP_BASE_URL", "http://localhost:8100")
PUBLIC_BASE_URL = _env("PUBLIC_BASE_URL", "EMAIL_PROTECT_PUBLIC_BASE_URL", APP_BASE_URL)

GOOGLE_CLIENT_ID = _env("GOOGLE_CLIENT_ID", "EMAIL_PROTECT_GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = _env("GOOGLE_CLIENT_SECRET", "EMAIL_PROTECT_GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = _env(
    "GOOGLE_REDIRECT_URI",
    "EMAIL_PROTECT_GOOGLE_REDIRECT_URI",
    f"{APP_BASE_URL}/auth/google/callback",
)
GMAIL_PUBSUB_TOPIC = _env("GMAIL_PUBSUB_TOPIC", "EMAIL_PROTECT_GMAIL_PUBSUB_TOPIC")

MS_CLIENT_ID = _env("MS_CLIENT_ID", "EMAIL_PROTECT_MS_CLIENT_ID")
MS_CLIENT_SECRET = _env("MS_CLIENT_SECRET", "EMAIL_PROTECT_MS_CLIENT_SECRET")
MS_TENANT = _env("MS_TENANT", "EMAIL_PROTECT_MS_TENANT", "common")
MS_REDIRECT_URI = _env(
    "MS_REDIRECT_URI",
    "EMAIL_PROTECT_MS_REDIRECT_URI",
    f"{APP_BASE_URL}/auth/microsoft/callback",
)

DB_PATH = _env("TOKEN_DB_PATH", "EMAIL_PROTECT_TOKEN_DB_PATH", "tokens.db")

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
app.include_router(email_security_router)

class EmailParty(BaseModel):
    name: Optional[str] = None
    email: str
    domain: Optional[str] = None

class EmailAttachment(BaseModel):
    filename: str
    size: Optional[int] = None
    sha256: Optional[str] = None
    mime: Optional[str] = None
    is_archive: Optional[bool] = None

class EmailUrl(BaseModel):
    url: str
    domain: Optional[str] = None
    is_shortener: Optional[bool] = None
    reputation: Optional[str] = None

class EmailAuthResults(BaseModel):
    spf: Optional[str] = None
    dkim: Optional[str] = None
    dmarc: Optional[str] = None

class EmailMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    provider: str
    mailbox: str
    thread_id: Optional[str] = None
    received_at: datetime
    from_: EmailParty = Field(..., alias="from")
    to: List[EmailParty]
    cc: Optional[List[EmailParty]] = None
    bcc: Optional[List[EmailParty]] = None
    subject: str
    snippet: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    auth_results: Optional[EmailAuthResults] = None
    attachments: List[EmailAttachment] = Field(default_factory=list)
    urls: List[EmailUrl] = Field(default_factory=list)
    observables: List[str] = Field(default_factory=list)

class MatchedIoc(BaseModel):
    type: str
    value: str
    source: Optional[str] = None

class EmailThreatAssessment(BaseModel):
    message_id: str
    score: int
    verdict: str
    reasons: List[str] = Field(default_factory=list)
    matched_iocs: List[MatchedIoc] = Field(default_factory=list)
    action_recommended: str

class EmailAction(BaseModel):
    id: str
    message_id: str
    action: str
    requested_by: str
    requested_at: datetime
    status: str
    error: Optional[str] = None
    provider_receipt: Optional[Dict[str, Any]] = None

class MailboxIntegrationState(BaseModel):
    mailbox: str
    provider: str
    connected: bool
    last_sync_at: Optional[datetime] = None
    last_sync_ok: Optional[bool] = None
    last_error: Optional[str] = None

class SenderPolicyRequest(BaseModel):
    mailbox: str
    sender_email: Optional[str] = None
    sender_domain: Optional[str] = None
    reason: Optional[str] = None

class SenderAllowRequest(BaseModel):
    mailbox: str
    sender_email: Optional[str] = None
    sender_domain: Optional[str] = None

class BlockSenderRequest(BaseModel):
    mailbox: str
    sender: str

class BlockUrlRequest(BaseModel):
    mailbox: str
    url: str

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
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS email_messages (
            message_id TEXT PRIMARY KEY,
            provider TEXT NOT NULL,
            mailbox TEXT NOT NULL,
            received_at TEXT NOT NULL,
            data_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS email_assessments (
            message_id TEXT PRIMARY KEY,
            score INTEGER NOT NULL,
            verdict TEXT NOT NULL,
            reasons_json TEXT NOT NULL,
            matched_iocs_json TEXT NOT NULL,
            action_recommended TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(message_id) REFERENCES email_messages(message_id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS email_actions (
            id TEXT PRIMARY KEY,
            message_id TEXT,
            action TEXT NOT NULL,
            requested_by TEXT NOT NULL,
            requested_at TEXT NOT NULL,
            status TEXT NOT NULL,
            error TEXT,
            provider_receipt_json TEXT,
            FOREIGN KEY(message_id) REFERENCES email_messages(message_id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS mailbox_integration (
            provider TEXT NOT NULL,
            mailbox TEXT NOT NULL,
            connected INTEGER NOT NULL,
            last_sync_at TEXT,
            last_sync_ok INTEGER,
            last_error TEXT,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (provider, mailbox)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS threat_intel_audit (
            id TEXT PRIMARY KEY,
            mailbox TEXT NOT NULL,
            provider TEXT,
            action TEXT NOT NULL,
            target TEXT,
            status TEXT NOT NULL,
            mock_mode INTEGER NOT NULL,
            requested_by TEXT NOT NULL,
            requested_at TEXT NOT NULL,
            message_id TEXT,
            detail_json TEXT
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

def upsert_email_message(message: EmailMessage) -> None:
    now = datetime.now(timezone.utc).isoformat()
    payload = message.model_dump(by_alias=True)
    payload["received_at"] = message.received_at.isoformat()
    conn = db()
    conn.execute(
        """
        INSERT OR REPLACE INTO email_messages(
            message_id, provider, mailbox, received_at, data_json, created_at, updated_at
        ) VALUES (?,?,?,?,?,?,?)
        """,
        (
            message.id,
            message.provider,
            message.mailbox,
            message.received_at.isoformat(),
            json.dumps(payload),
            now,
            now,
        ),
    )
    conn.commit()
    conn.close()

def upsert_email_assessment(assessment: EmailThreatAssessment) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn = db()
    conn.execute(
        """
        INSERT OR REPLACE INTO email_assessments(
            message_id, score, verdict, reasons_json, matched_iocs_json, action_recommended, updated_at
        ) VALUES (?,?,?,?,?,?,?)
        """,
        (
            assessment.message_id,
            assessment.score,
            assessment.verdict,
            json.dumps(assessment.reasons),
            json.dumps([m.model_dump() for m in assessment.matched_iocs]),
            assessment.action_recommended,
            now,
        ),
    )
    conn.commit()
    conn.close()

def get_email_message_record(message_id: str) -> Optional[Dict[str, Any]]:
    conn = db()
    row = conn.execute(
        """
        SELECT m.data_json, a.score, a.verdict, a.reasons_json, a.matched_iocs_json,
               a.action_recommended
        FROM email_messages m
        LEFT JOIN email_assessments a ON m.message_id = a.message_id
        WHERE m.message_id = ?
        """,
        (message_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    data = json.loads(row["data_json"])
    assessment = None
    if row["score"] is not None:
        assessment = {
            "message_id": message_id,
            "score": row["score"],
            "verdict": row["verdict"],
            "reasons": json.loads(row["reasons_json"]),
            "matched_iocs": json.loads(row["matched_iocs_json"]),
            "action_recommended": row["action_recommended"],
        }
    return {"message": data, "assessment": assessment}

def list_email_messages(
    mailbox: str,
    provider: Optional[str],
    q: Optional[str],
    score_gte: Optional[int],
    verdict: Optional[str],
    limit: int,
    offset: int,
) -> Tuple[List[Dict[str, Any]], Optional[int]]:
    conn = db()
    where = ["m.mailbox = ?"]
    params: List[Any] = [mailbox]
    if provider:
        where.append("m.provider = ?")
        params.append(provider)
    if score_gte is not None:
        where.append("a.score >= ?")
        params.append(score_gte)
    if verdict:
        where.append("a.verdict = ?")
        params.append(verdict)
    if q:
        where.append("LOWER(m.data_json) LIKE ?")
        params.append(f"%{q.lower()}%")
    where_sql = " AND ".join(where)
    rows = conn.execute(
        f"""
        SELECT m.data_json, a.score, a.verdict, a.reasons_json, a.matched_iocs_json,
               a.action_recommended
        FROM email_messages m
        LEFT JOIN email_assessments a ON m.message_id = a.message_id
        WHERE {where_sql}
        ORDER BY m.received_at DESC
        LIMIT ? OFFSET ?
        """,
        (*params, limit, offset),
    ).fetchall()
    total_row = conn.execute(
        f"""
        SELECT COUNT(1) as total
        FROM email_messages m
        LEFT JOIN email_assessments a ON m.message_id = a.message_id
        WHERE {where_sql}
        """,
        params,
    ).fetchone()
    conn.close()
    items: List[Dict[str, Any]] = []
    for row in rows:
        message = json.loads(row["data_json"])
        assessment = None
        if row["score"] is not None:
            assessment = {
                "message_id": message["id"],
                "score": row["score"],
                "verdict": row["verdict"],
                "reasons": json.loads(row["reasons_json"]),
                "matched_iocs": json.loads(row["matched_iocs_json"]),
                "action_recommended": row["action_recommended"],
            }
        items.append({"message": message, "assessment": assessment})
    return items, (total_row["total"] if total_row else None)

def fetch_threat_records(mailbox: str, provider: Optional[str]) -> List[Dict[str, Any]]:
    conn = db()
    params: List[Any] = [mailbox]
    where = ["m.mailbox = ?"]
    if provider:
        where.append("m.provider = ?")
        params.append(provider)
    where_sql = " AND ".join(where)
    rows = conn.execute(
        f"""
        SELECT m.data_json, a.score, a.verdict, a.reasons_json, a.matched_iocs_json,
               a.action_recommended
        FROM email_messages m
        LEFT JOIN email_assessments a ON m.message_id = a.message_id
        WHERE {where_sql}
        ORDER BY m.received_at DESC
        """,
        params,
    ).fetchall()
    conn.close()
    records: List[Dict[str, Any]] = []
    for row in rows:
        message = json.loads(row["data_json"])
        assessment = None
        if row["score"] is not None:
            assessment = {
                "message_id": message["id"],
                "score": row["score"],
                "verdict": row["verdict"],
                "reasons": json.loads(row["reasons_json"]),
                "matched_iocs": json.loads(row["matched_iocs_json"]),
                "action_recommended": row["action_recommended"],
            }
        records.append({"message": message, "assessment": assessment})
    return records

def upsert_mailbox_state(
    mailbox: str,
    provider: str,
    connected: bool,
    last_sync_at: Optional[datetime],
    last_sync_ok: Optional[bool],
    last_error: Optional[str],
) -> None:
    conn = db()
    conn.execute(
        """
        INSERT OR REPLACE INTO mailbox_integration(
            provider, mailbox, connected, last_sync_at, last_sync_ok, last_error, updated_at
        ) VALUES (?,?,?,?,?,?,?)
        """,
        (
            provider,
            mailbox,
            1 if connected else 0,
            last_sync_at.isoformat() if last_sync_at else None,
            1 if last_sync_ok else 0 if last_sync_ok is not None else None,
            last_error,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()

def list_mailbox_states(mailbox: Optional[str] = None) -> List[MailboxIntegrationState]:
    conn = db()
    if mailbox:
        rows = conn.execute(
            "SELECT * FROM mailbox_integration WHERE mailbox=?",
            (mailbox,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM mailbox_integration").fetchall()
    conn.close()
    states: List[MailboxIntegrationState] = []
    for row in rows:
        states.append(
            MailboxIntegrationState(
                mailbox=row["mailbox"],
                provider=row["provider"],
                connected=bool(row["connected"]),
                last_sync_at=datetime.fromisoformat(row["last_sync_at"])
                if row["last_sync_at"]
                else None,
                last_sync_ok=bool(row["last_sync_ok"]) if row["last_sync_ok"] is not None else None,
                last_error=row["last_error"],
            )
        )
    return states

def record_email_action(
    message_id: Optional[str],
    action: str,
    requested_by: str,
    status: str,
    error: Optional[str],
    provider_receipt: Optional[Dict[str, Any]],
) -> EmailAction:
    action_id = str(uuid.uuid4())
    message_id_value = message_id or ""
    now = datetime.now(timezone.utc)
    conn = db()
    conn.execute(
        """
        INSERT INTO email_actions(
            id, message_id, action, requested_by, requested_at, status, error, provider_receipt_json
        ) VALUES (?,?,?,?,?,?,?,?)
        """,
        (
            action_id,
            message_id_value,
            action,
            requested_by,
            now.isoformat(),
            status,
            error,
            json.dumps(provider_receipt) if provider_receipt else None,
        ),
    )
    conn.commit()
    conn.close()
    return EmailAction(
        id=action_id,
        message_id=message_id_value,
        action=action,
        requested_by=requested_by,
        requested_at=now,
        status=status,
        error=error,
        provider_receipt=provider_receipt,
    )

def get_latest_action(message_id: str) -> Optional[EmailAction]:
    conn = db()
    row = conn.execute(
        """
        SELECT * FROM email_actions
        WHERE message_id = ?
        ORDER BY requested_at DESC
        LIMIT 1
        """,
        (message_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    return EmailAction(
        id=row["id"],
        message_id=row["message_id"],
        action=row["action"],
        requested_by=row["requested_by"],
        requested_at=datetime.fromisoformat(row["requested_at"]),
        status=row["status"],
        error=row["error"],
        provider_receipt=json.loads(row["provider_receipt_json"])
        if row["provider_receipt_json"]
        else None,
    )

def record_threat_audit(
    mailbox: str,
    provider: Optional[str],
    action: str,
    target: Optional[str],
    status: str,
    mock_mode: bool,
    requested_by: str,
    message_id: Optional[str],
    detail: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    audit_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    conn = db()
    conn.execute(
        """
        INSERT INTO threat_intel_audit(
            id, mailbox, provider, action, target, status, mock_mode, requested_by,
            requested_at, message_id, detail_json
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            audit_id,
            mailbox,
            provider,
            action,
            target,
            status,
            1 if mock_mode else 0,
            requested_by,
            now.isoformat(),
            message_id,
            json.dumps(detail) if detail else None,
        ),
    )
    conn.commit()
    conn.close()
    return {
        "id": audit_id,
        "mailbox": mailbox,
        "provider": provider,
        "action": action,
        "target": target,
        "status": status,
        "mock_mode": mock_mode,
        "requested_by": requested_by,
        "requested_at": now.isoformat(),
        "message_id": message_id,
        "detail": detail,
    }

def list_threat_audit(mailbox: str, limit: int) -> List[Dict[str, Any]]:
    conn = db()
    rows = conn.execute(
        """
        SELECT * FROM threat_intel_audit
        WHERE mailbox = ?
        ORDER BY requested_at DESC
        LIMIT ?
        """,
        (mailbox, limit),
    ).fetchall()
    conn.close()
    out: List[Dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "id": row["id"],
                "mailbox": row["mailbox"],
                "provider": row["provider"],
                "action": row["action"],
                "target": row["target"],
                "status": row["status"],
                "mock_mode": bool(row["mock_mode"]),
                "requested_by": row["requested_by"],
                "requested_at": row["requested_at"],
                "message_id": row["message_id"],
                "detail": json.loads(row["detail_json"]) if row["detail_json"] else None,
            }
        )
    return out

URL_RE = re.compile(r"(https?://[^\s<>\"]+)", re.IGNORECASE)
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
DANGEROUS_EXT = {
    ".exe", ".scr", ".js", ".vbs", ".vbe", ".ps1", ".bat", ".cmd", ".lnk",
    ".iso", ".img", ".hta", ".msi", ".jar", ".wsf",
}
URL_SHORTENERS = {
    "bit.ly", "t.co", "tinyurl.com", "goo.gl", "ow.ly", "is.gd", "cutt.ly",
    "rebrand.ly",
}

class EmailParty(BaseModel):
    name: Optional[str] = None
    email: str
    domain: Optional[str] = None

class EmailAttachment(BaseModel):
    filename: str
    size: Optional[int] = None
    sha256: Optional[str] = None
    mime: Optional[str] = None
    is_archive: Optional[bool] = None

class EmailUrl(BaseModel):
    url: str
    domain: Optional[str] = None
    is_shortener: Optional[bool] = None
    reputation: Optional[str] = None

class EmailAuthResults(BaseModel):
    spf: Optional[str] = None
    dkim: Optional[str] = None
    dmarc: Optional[str] = None

class EmailMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    provider: str
    mailbox: str
    thread_id: Optional[str] = None
    received_at: datetime
    from_: EmailParty = Field(..., alias="from")
    to: List[EmailParty]
    cc: Optional[List[EmailParty]] = None
    bcc: Optional[List[EmailParty]] = None
    subject: str
    snippet: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    auth_results: Optional[EmailAuthResults] = None
    attachments: List[EmailAttachment] = Field(default_factory=list)
    urls: List[EmailUrl] = Field(default_factory=list)
    observables: List[str] = Field(default_factory=list)

class MatchedIoc(BaseModel):
    type: str
    value: str
    source: Optional[str] = None

class EmailThreatAssessment(BaseModel):
    message_id: str
    score: int
    verdict: str
    reasons: List[str] = Field(default_factory=list)
    matched_iocs: List[MatchedIoc] = Field(default_factory=list)
    action_recommended: str

class EmailAction(BaseModel):
    id: str
    message_id: str
    action: str
    requested_by: str
    requested_at: datetime
    status: str
    error: Optional[str] = None
    provider_receipt: Optional[Dict[str, Any]] = None

class MailboxIntegrationState(BaseModel):
    mailbox: str
    provider: str
    connected: bool
    last_sync_at: Optional[datetime] = None
    last_sync_ok: Optional[bool] = None
    last_error: Optional[str] = None

class SenderPolicyRequest(BaseModel):
    mailbox: str
    sender_email: Optional[str] = None
    sender_domain: Optional[str] = None
    reason: Optional[str] = None

class SenderAllowRequest(BaseModel):
    mailbox: str
    sender_email: Optional[str] = None
    sender_domain: Optional[str] = None

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

def parse_email_parties(value: str) -> List[EmailParty]:
    parties: List[EmailParty] = []
    for name, addr in getaddresses([value or ""]):
        if not addr:
            continue
        domain = domain_from_email(addr)
        parties.append(EmailParty(name=name or None, email=addr, domain=domain or None))
    return parties

def parse_auth_results(headers: Dict[str, str]) -> Optional[EmailAuthResults]:
    if not headers:
        return None
    auth_header = headers.get("authentication-results", "") or headers.get("auth-results", "")
    if not auth_header:
        return None
    def _match(token: str) -> Optional[str]:
        m = re.search(rf"{token}=([a-zA-Z]+)", auth_header)
        return m.group(1).lower() if m else None
    return EmailAuthResults(
        spf=_match("spf"),
        dkim=_match("dkim"),
        dmarc=_match("dmarc"),
    )

def is_archive_filename(filename: str) -> bool:
    lower = filename.lower()
    return lower.endswith((".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".tgz"))

def build_url_objects(urls: List[str]) -> List[EmailUrl]:
    out: List[EmailUrl] = []
    for url in urls:
        domain = domain_from_url(url)
        out.append(
            EmailUrl(
                url=url,
                domain=domain or None,
                is_shortener=domain in URL_SHORTENERS if domain else None,
            )
        )
    return out

def extract_observables(message: EmailMessage, body_text: str) -> List[str]:
    observables: List[str] = []
    domains = {message.from_.domain, *[p.domain for p in message.to if p.domain]}
    if message.cc:
        domains.update({p.domain for p in message.cc if p.domain})
    if message.bcc:
        domains.update({p.domain for p in message.bcc if p.domain})
    for url in message.urls:
        if url.domain:
            domains.add(url.domain)
    for domain in domains:
        if domain:
            observables.append(domain)
    for ip in IPV4_RE.findall(body_text or ""):
        observables.append(ip)
    return sorted(set(observables))

def sanitize_search_query(q: Optional[str]) -> Optional[str]:
    if not q:
        return None
    q = q.strip()
    if len(q) > 200:
        raise HTTPException(400, "Query too long")
    if re.search(r"[\x00-\x1f]", q):
        raise HTTPException(400, "Invalid query")
    return q

def parse_window(window: Optional[str]) -> Optional[timedelta]:
    if not window:
        return None
    window = window.strip().lower()
    match = re.match(r"^(\d+)(h|d)$", window)
    if not match:
        raise HTTPException(400, "Invalid window format (expected 24h/7d)")
    value = int(match.group(1))
    unit = match.group(2)
    if unit == "h":
        return timedelta(hours=value)
    return timedelta(days=value)

def parse_range(range_value: Optional[str]) -> Optional[timedelta]:
    if not range_value:
        return None
    range_value = range_value.strip().lower()
    match = re.match(r"^(\d+)(h|d)$", range_value)
    if not match:
        raise HTTPException(400, "Invalid range format (expected 24h/7d/30d)")
    value = int(match.group(1))
    unit = match.group(2)
    return timedelta(hours=value) if unit == "h" else timedelta(days=value)

def normalize_gmail_message(mailbox: str, full: Dict[str, Any]) -> Tuple[EmailMessage, str]:
    payload = full.get("payload", {}) or {}
    headers = payload.get("headers", []) or []
    header_map = {x.get("name", "").lower(): x.get("value", "") for x in headers}
    subject = header_map.get("subject", "")
    from_parties = parse_email_parties(header_map.get("from", ""))
    to_parties = parse_email_parties(header_map.get("to", ""))
    cc_parties = parse_email_parties(header_map.get("cc", ""))
    bcc_parties = parse_email_parties(header_map.get("bcc", ""))
    body_text = gmail_extract_body(payload)
    urls = build_url_objects(extract_urls(body_text))
    attachment_objs: List[EmailAttachment] = []
    stack = list(payload.get("parts", []) or [])
    while stack:
        part = stack.pop()
        filename = part.get("filename") or ""
        if filename:
            attachment_objs.append(
                EmailAttachment(
                    filename=filename,
                    size=part.get("body", {}).get("size"),
                    mime=part.get("mimeType"),
                    is_archive=is_archive_filename(filename),
                )
            )
        for ch in (part.get("parts") or []):
            stack.append(ch)
    received_at = datetime.fromtimestamp(
        int(full.get("internalDate", 0)) / 1000,
        tz=timezone.utc,
    )
    message = EmailMessage(
        id=full.get("id") or "",
        provider="google",
        mailbox=mailbox,
        thread_id=full.get("threadId"),
        received_at=received_at,
        from_=from_parties[0] if from_parties else EmailParty(email="", domain=None),
        to=to_parties,
        cc=cc_parties or None,
        bcc=bcc_parties or None,
        subject=subject,
        snippet=full.get("snippet") or body_text[:160] if body_text else None,
        headers={k: v for k, v in header_map.items() if k in {"subject", "from", "to", "cc", "bcc", "date", "reply-to", "message-id", "authentication-results"}},
        auth_results=parse_auth_results(header_map),
        attachments=attachment_objs,
        urls=urls,
        observables=[],
    )
    message.observables = extract_observables(message, body_text)
    return message, body_text

def normalize_graph_message(
    mailbox: str,
    message: Dict[str, Any],
    attachments: List[Dict[str, Any]],
) -> Tuple[EmailMessage, str]:
    from_addr = (message.get("from") or {}).get("emailAddress", {})
    to_parties = []
    for rec in message.get("toRecipients") or []:
        addr = rec.get("emailAddress") or {}
        to_parties.append(
            EmailParty(
                name=addr.get("name"),
                email=addr.get("address") or "",
                domain=domain_from_email(addr.get("address") or "") or None,
            )
        )
    cc_parties = []
    for rec in message.get("ccRecipients") or []:
        addr = rec.get("emailAddress") or {}
        cc_parties.append(
            EmailParty(
                name=addr.get("name"),
                email=addr.get("address") or "",
                domain=domain_from_email(addr.get("address") or "") or None,
            )
        )
    bcc_parties = []
    for rec in message.get("bccRecipients") or []:
        addr = rec.get("emailAddress") or {}
        bcc_parties.append(
            EmailParty(
                name=addr.get("name"),
                email=addr.get("address") or "",
                domain=domain_from_email(addr.get("address") or "") or None,
            )
        )
    body_text = message.get("bodyPreview", "") or ""
    urls = build_url_objects(extract_urls(body_text))
    attachment_objs: List[EmailAttachment] = []
    for attachment in attachments:
        filename = attachment.get("name") or ""
        if not filename:
            continue
        attachment_objs.append(
            EmailAttachment(
                filename=filename,
                size=attachment.get("size"),
                mime=attachment.get("contentType"),
                is_archive=is_archive_filename(filename),
            )
        )
    received_raw = message.get("receivedDateTime") or ""
    received_at = datetime.fromisoformat(received_raw.replace("Z", "+00:00")) if received_raw else datetime.now(timezone.utc)
    msg = EmailMessage(
        id=message.get("id") or "",
        provider="microsoft",
        mailbox=mailbox,
        received_at=received_at,
        from_=EmailParty(
            name=from_addr.get("name"),
            email=from_addr.get("address") or "",
            domain=domain_from_email(from_addr.get("address") or "") or None,
        ),
        to=to_parties,
        cc=cc_parties or None,
        bcc=bcc_parties or None,
        subject=message.get("subject") or "",
        snippet=body_text[:160] if body_text else None,
        headers=None,
        auth_results=None,
        attachments=attachment_objs,
        urls=urls,
        observables=[],
    )
    msg.observables = extract_observables(msg, body_text)
    return msg, body_text

def assess_threat(message: EmailMessage, body_text: str, reply_to: Optional[str]) -> EmailThreatAssessment:
    findings: List[str] = []
    score = 0

    from_domain = message.from_.domain or ""
    reply_domain = domain_from_email(reply_to) if reply_to else ""

    if reply_to and reply_domain and from_domain and reply_domain != from_domain:
        findings.append(f"Reply-To mismatch ({reply_domain} vs {from_domain})")
        score += 25

    if "xn--" in from_domain:
        findings.append("Sender domain uses punycode")
        score += 15

    for url in message.urls:
        if url.domain and "xn--" in url.domain:
            findings.append("URL contains punycode")
            score += 15
        if url.is_shortener:
            findings.append(f"Shortened URL detected ({url.domain})")
            score += 5

    for attachment in message.attachments:
        lower = (attachment.filename or "").lower()
        for ext in DANGEROUS_EXT:
            if lower.endswith(ext):
                findings.append(f"Attachment with dangerous extension ({ext}): {attachment.filename}")
                score += 30
                break

    if message.subject and re.search(
        r"\b(urgent|verify|password|invoice|pay|blocked|suspend)\b", message.subject, re.IGNORECASE
    ):
        findings.append("Subject includes phishing keywords")
        score += 10

    score = min(score, 100)
    verdict = "low"
    if any("dangerous extension" in f for f in findings):
        verdict = "malware"
    elif reply_to and reply_domain and from_domain and reply_domain != from_domain:
        verdict = "spoofing"
    elif score >= 60:
        verdict = "phishing"
    elif score >= 30:
        verdict = "suspicious"

    action_recommended = "none"
    if score >= 70 or verdict in {"phishing", "malware"}:
        action_recommended = "quarantine"
    elif score >= 40:
        action_recommended = "filter"

    return EmailThreatAssessment(
        message_id=message.id,
        score=score,
        verdict=verdict,
        reasons=findings,
        matched_iocs=[],
        action_recommended=action_recommended,
    )

def spoofing_signals(message: Dict[str, Any], assessment: Optional[Dict[str, Any]]) -> List[str]:
    signals: List[str] = []
    auth = message.get("auth_results") or {}
    for key in ("spf", "dkim", "dmarc"):
        value = (auth.get(key) or "").lower()
        if value and value != "pass":
            signals.append(f"{key}:{value}")
    if assessment:
        for reason in assessment.get("reasons", []):
            if "Reply-To mismatch" in reason:
                signals.append("reply_to_mismatch")
    return signals

def build_threat_item(message: Dict[str, Any], assessment: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    score = assessment.get("score") if assessment else 0
    verdict = assessment.get("verdict") if assessment else "low"
    spoofing = spoofing_signals(message, assessment)
    return {
        "id": message.get("id"),
        "received_at": message.get("received_at"),
        "from": message.get("from"),
        "to": message.get("to"),
        "subject": message.get("subject"),
        "score": score,
        "verdict": verdict,
        "threat_type": verdict,
        "urls": message.get("urls") or [],
        "attachments": message.get("attachments") or [],
        "spoofing_signals": spoofing,
        "dlp_violations": [],
    }

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
        "$select": "id,subject,from,replyTo,receivedDateTime,bodyPreview,hasAttachments,"
        "internetMessageId,toRecipients,ccRecipients,bccRecipients",
        "$orderby": "receivedDateTime desc",
    }
    r = requests.get(url, headers={"Authorization": f"Bearer {access_token}"}, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("value", [])

def graph_list_attachments(access_token: str, message_id: str) -> List[Dict[str, Any]]:
    url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments"
    params = {"$select": "name,contentType,size,isInline"}
    r = requests.get(url, headers={"Authorization": f"Bearer {access_token}"}, params=params, timeout=30)
    if r.status_code == 404:
        return []
    r.raise_for_status()
    items = r.json().get("value", [])
    return items

@app.on_event("startup")
def _startup():
    init_db()
    init_email_security_db()
    asyncio.create_task(_oauth_state_cleanup_loop())

@app.get("/health")
def health():
    states = [s.model_dump() for s in list_mailbox_states()]
    return {"ok": True, "time": datetime.now(timezone.utc).isoformat(), "mailboxes": states}

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
    now = datetime.now(timezone.utc)
    try:
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
            legacy = analyze_message(
                provider="google",
                mailbox=mailbox,
                msg_id=mid,
                subject=subject,
                from_addr=from_addr,
                reply_to=reply_to,
                body_text=body,
                attachment_names=attachment_names,
            )
            message, body_text = normalize_gmail_message(mailbox, full)
            assessment = assess_threat(message, body_text, reply_to)
            upsert_email_message(message)
            upsert_email_assessment(assessment)
            out.append(
                {
                    **legacy,
                    "message": message.model_dump(by_alias=True),
                    "assessment": assessment.model_dump(),
                }
            )
        upsert_mailbox_state(
            mailbox=mailbox,
            provider="google",
            connected=True,
            last_sync_at=now,
            last_sync_ok=True,
            last_error=None,
        )
        return {"count": len(out), "results": out}
    except HTTPException as exc:
        upsert_mailbox_state(
            mailbox=mailbox,
            provider="google",
            connected=False,
            last_sync_at=now,
            last_sync_ok=False,
            last_error=str(exc.detail),
        )
        raise

@app.post("/sync/microsoft")
def sync_microsoft(mailbox: str, top: int = 10, fetch_attachments: bool = True):
    now = datetime.now(timezone.utc)
    try:
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
            attachment_items: List[Dict[str, Any]] = []
            attachment_names: List[str] = []
            if fetch_attachments and m.get("hasAttachments") and mid:
                attachment_items = graph_list_attachments(access_token, mid)
                attachment_names = [it.get("name") or "" for it in attachment_items if it.get("name")]
            legacy = analyze_message(
                provider="microsoft",
                mailbox=mailbox,
                msg_id=mid,
                subject=subject,
                from_addr=from_addr,
                reply_to=reply_to,
                body_text=body_text,
                attachment_names=attachment_names,
            )
            message, body_text = normalize_graph_message(mailbox, m, attachment_items)
            assessment = assess_threat(message, body_text, reply_to)
            upsert_email_message(message)
            upsert_email_assessment(assessment)
            out.append(
                {
                    **legacy,
                    "message": message.model_dump(by_alias=True),
                    "assessment": assessment.model_dump(),
                }
            )
        upsert_mailbox_state(
            mailbox=mailbox,
            provider="microsoft",
            connected=True,
            last_sync_at=now,
            last_sync_ok=True,
            last_error=None,
        )
        return {"count": len(out), "results": out}
    except HTTPException as exc:
        upsert_mailbox_state(
            mailbox=mailbox,
            provider="microsoft",
            connected=False,
            last_sync_at=now,
            last_sync_ok=False,
            last_error=str(exc.detail),
        )
        raise

@app.get("/threat-intel/email/messages")
def list_threat_messages(
    mailbox: str,
    provider: Optional[str] = None,
    q: Optional[str] = None,
    score_gte: Optional[int] = None,
    verdict: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    cursor: Optional[int] = None,
):
    if not mailbox:
        raise HTTPException(400, "Missing mailbox")
    q = sanitize_search_query(q)
    limit = min(max(limit, 1), 200)
    offset_value = cursor if cursor is not None else offset
    items, total = list_email_messages(
        mailbox=mailbox,
        provider=provider,
        q=q,
        score_gte=score_gte,
        verdict=verdict,
        limit=limit,
        offset=offset_value,
    )
    next_cursor = None
    if total is not None and offset_value + limit < total:
        next_cursor = offset_value + limit
    return {"items": items, "total": total, "next_cursor": next_cursor}

@app.get("/threat-intel/email/messages/{message_id}")
def get_threat_message(message_id: str):
    record = get_email_message_record(message_id)
    if not record:
        raise HTTPException(404, "Message not found")
    action = get_latest_action(message_id)
    return {
        "message": record["message"],
        "assessment": record["assessment"],
        "action_state": action.model_dump() if action else None,
    }

@app.get("/threat-intel/email/summary")
def threat_summary(
    mailbox: str,
    window: Optional[str] = None,
    provider: Optional[str] = None,
):
    if not mailbox:
        raise HTTPException(400, "Missing mailbox")
    window_delta = parse_window(window)
    cutoff = datetime.now(timezone.utc) - window_delta if window_delta else None
    conn = db()
    params: List[Any] = [mailbox]
    where = ["m.mailbox = ?"]
    if provider:
        where.append("m.provider = ?")
        params.append(provider)
    where_sql = " AND ".join(where)
    rows = conn.execute(
        f"""
        SELECT m.data_json, a.score, a.verdict
        FROM email_messages m
        LEFT JOIN email_assessments a ON m.message_id = a.message_id
        WHERE {where_sql}
        """,
        params,
    ).fetchall()
    conn.close()
    processed = 0
    blocked = 0
    quarantined = 0
    spoofing_or_suspicious = 0
    sender_counts: Dict[str, int] = {}
    url_counts: Dict[str, int] = {}
    hash_counts: Dict[str, int] = {}
    for row in rows:
        message = json.loads(row["data_json"])
        received_at = datetime.fromisoformat(message["received_at"])
        if cutoff and received_at < cutoff:
            continue
        processed += 1
        score = row["score"] or 0
        verdict = row["verdict"] or "low"
        if score >= 70:
            blocked += 1
        elif score >= 40:
            quarantined += 1
        if verdict != "low" or score > 0:
            spoofing_or_suspicious += 1
        sender = (message.get("from") or {}).get("email") or ""
        if sender:
            sender_counts[sender] = sender_counts.get(sender, 0) + 1
        for url in message.get("urls") or []:
            url_value = url.get("domain") or url.get("url")
            if url_value:
                url_counts[url_value] = url_counts.get(url_value, 0) + 1
        for attachment in message.get("attachments") or []:
            sha = attachment.get("sha256")
            if sha:
                hash_counts[sha] = hash_counts.get(sha, 0) + 1
    def top_n(data: Dict[str, int]) -> List[Dict[str, Any]]:
        return [{"value": k, "count": v} for k, v in sorted(data.items(), key=lambda x: x[1], reverse=True)[:5]]
    integration_state = [s.model_dump() for s in list_mailbox_states(mailbox)]
    based_on_last_sync = processed == 0 and bool(integration_state)
    return {
        "processed": processed,
        "blocked": blocked,
        "quarantined": quarantined,
        "spoofing_or_suspicious": spoofing_or_suspicious,
        "top_senders": top_n(sender_counts),
        "top_urls": top_n(url_counts),
        "top_hashes": top_n(hash_counts),
        "integration_state": integration_state,
        "based_on_last_sync": based_on_last_sync,
    }

def _soft_action_receipt(action: str, provider: str) -> Dict[str, Any]:
    return {
        "provider": provider,
        "status": "soft_action",
        "note": f"{action} stored locally; provider action not yet implemented",
    }

@app.post("/threat-intel/email/messages/{message_id}/quarantine")
def quarantine_message(message_id: str, request: Request):
    record = get_email_message_record(message_id)
    if not record:
        raise HTTPException(404, "Message not found")
    message = record["message"]
    action = record_email_action(
        message_id=message_id,
        action="quarantine",
        requested_by=request.headers.get("x-requested-by", "system"),
        status="success",
        error=None,
        provider_receipt=_soft_action_receipt("quarantine", message.get("provider", "")),
    )
    return {"action_id": action.id, "status": action.status, "message_id": message_id}

@app.post("/threat-intel/email/messages/{message_id}/release")
def release_message(message_id: str, request: Request):
    record = get_email_message_record(message_id)
    if not record:
        raise HTTPException(404, "Message not found")
    message = record["message"]
    action = record_email_action(
        message_id=message_id,
        action="release",
        requested_by=request.headers.get("x-requested-by", "system"),
        status="success",
        error=None,
        provider_receipt=_soft_action_receipt("release", message.get("provider", "")),
    )
    return {"action_id": action.id, "status": action.status, "message_id": message_id}

@app.post("/threat-intel/email/messages/{message_id}/rescan")
def rescan_message(message_id: str, request: Request):
    record = get_email_message_record(message_id)
    if not record:
        raise HTTPException(404, "Message not found")
    message_data = record["message"]
    message = EmailMessage.model_validate(message_data)
    body_text = message.snippet or ""
    assessment = assess_threat(message, body_text, reply_to=None)
    upsert_email_assessment(assessment)
    action = record_email_action(
        message_id=message_id,
        action="rescan",
        requested_by=request.headers.get("x-requested-by", "system"),
        status="success",
        error=None,
        provider_receipt={"status": "rescanned"},
    )
    return {
        "action_id": action.id,
        "status": action.status,
        "message_id": message_id,
        "assessment": assessment.model_dump(),
    }

@app.post("/threat-intel/email/senders/block")
def block_sender(payload: SenderPolicyRequest, request: Request):
    if not payload.sender_email and not payload.sender_domain:
        raise HTTPException(400, "sender_email or sender_domain required")
    action = record_email_action(
        message_id=None,
        action="block_sender",
        requested_by=request.headers.get("x-requested-by", "system"),
        status="success",
        error=None,
        provider_receipt={
            "mailbox": payload.mailbox,
            "sender_email": payload.sender_email,
            "sender_domain": payload.sender_domain,
            "reason": payload.reason,
            "status": "stored_policy",
        },
    )
    return {"action_id": action.id, "status": action.status}

@app.post("/threat-intel/email/senders/allow")
def allow_sender(payload: SenderAllowRequest, request: Request):
    if not payload.sender_email and not payload.sender_domain:
        raise HTTPException(400, "sender_email or sender_domain required")
    action = record_email_action(
        message_id=None,
        action="allow_sender",
        requested_by=request.headers.get("x-requested-by", "system"),
        status="success",
        error=None,
        provider_receipt={
            "mailbox": payload.mailbox,
            "sender_email": payload.sender_email,
            "sender_domain": payload.sender_domain,
            "status": "stored_policy",
        },
    )
    return {"action_id": action.id, "status": action.status}

@app.get("/threat-intel/summary")
def threat_intel_summary(
    mailbox: str,
    range: Optional[str] = None,
):
    if not mailbox:
        raise HTTPException(400, "Missing mailbox")
    range_delta = parse_range(range)
    cutoff = datetime.now(timezone.utc) - range_delta if range_delta else None
    records = fetch_threat_records(mailbox, provider=None)
    processed = 0
    blocked = 0
    quarantined = 0
    spoofing = 0
    dlp_count = 0
    sender_counts: Dict[str, int] = {}
    target_counts: Dict[str, int] = {}
    provider_values: Dict[str, int] = {}
    for record in records:
        message = record["message"]
        assessment = record["assessment"]
        received_at = datetime.fromisoformat(message["received_at"])
        if cutoff and received_at < cutoff:
            continue
        processed += 1
        score = assessment.get("score") if assessment else 0
        if score >= 70:
            blocked += 1
        elif score >= 40:
            quarantined += 1
        if spoofing_signals(message, assessment):
            spoofing += 1
        sender = (message.get("from") or {}).get("email") or ""
        if sender:
            sender_counts[sender] = sender_counts.get(sender, 0) + 1
        for target in message.get("to") or []:
            email_value = target.get("email")
            if email_value:
                target_counts[email_value] = target_counts.get(email_value, 0) + 1
        provider_name = message.get("provider") or "unknown"
        provider_values[provider_name] = provider_values.get(provider_name, 0) + 1
    states = list_mailbox_states(mailbox)
    last_sync_at = None
    provider = None
    if states:
        latest = max(
            (s for s in states if s.last_sync_at),
            key=lambda s: s.last_sync_at or datetime.min.replace(tzinfo=timezone.utc),
            default=None,
        )
        if latest:
            last_sync_at = latest.last_sync_at.isoformat() if latest.last_sync_at else None
            provider = latest.provider
    def top_n(data: Dict[str, int]) -> List[Dict[str, Any]]:
        return [{"value": k, "count": v} for k, v in sorted(data.items(), key=lambda x: x[1], reverse=True)[:5]]
    if provider is None and provider_values:
        provider = max(provider_values, key=provider_values.get)
    return {
        "processed_count": processed,
        "blocked_count": blocked,
        "quarantined_count": quarantined,
        "spoofing_count": spoofing,
        "dlp_count": dlp_count,
        "top_senders": top_n(sender_counts),
        "top_targets": top_n(target_counts),
        "last_sync_at": last_sync_at,
        "provider": provider,
    }

@app.get("/threat-intel/messages")
def threat_intel_messages(
    mailbox: str,
    range: Optional[str] = None,
    q: Optional[str] = None,
    type: Optional[str] = None,
    min_score: Optional[int] = None,
    page: int = 1,
    page_size: int = 50,
):
    if not mailbox:
        raise HTTPException(400, "Missing mailbox")
    q = sanitize_search_query(q)
    range_delta = parse_range(range)
    cutoff = datetime.now(timezone.utc) - range_delta if range_delta else None
    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)
    type_value = (type or "").lower() if type else None
    records = fetch_threat_records(mailbox, provider=None)
    filtered: List[Dict[str, Any]] = []
    for record in records:
        message = record["message"]
        assessment = record["assessment"]
        received_at = datetime.fromisoformat(message["received_at"])
        if cutoff and received_at < cutoff:
            continue
        score = assessment.get("score") if assessment else 0
        verdict = assessment.get("verdict") if assessment else "low"
        if min_score is not None and score < min_score:
            continue
        if type_value:
            if type_value == "spoofing":
                if not spoofing_signals(message, assessment):
                    continue
            elif verdict != type_value:
                continue
        if q:
            haystack = " ".join(
                [
                    (message.get("subject") or ""),
                    ((message.get("from") or {}).get("email") or ""),
                    " ".join([u.get("url") or "" for u in message.get("urls") or []]),
                ]
            ).lower()
            if q.lower() not in haystack:
                continue
        filtered.append(build_threat_item(message, assessment))
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": filtered[start:end],
        "page": page,
        "page_size": page_size,
        "total": total,
    }

@app.get("/threat-intel/messages/{message_id}")
def threat_intel_message_detail(message_id: str):
    record = get_email_message_record(message_id)
    if not record:
        raise HTTPException(404, "Message not found")
    message = record["message"]
    assessment = record["assessment"]
    detail = build_threat_item(message, assessment)
    detail["raw_headers"] = message.get("headers") if message.get("headers") else None
    return detail

@app.post("/threat-intel/messages/{message_id}/actions/quarantine")
def threat_intel_action_quarantine(message_id: str, request: Request):
    record = get_email_message_record(message_id)
    if not record:
        raise HTTPException(404, "Message not found")
    message = record["message"]
    audit = record_threat_audit(
        mailbox=message.get("mailbox"),
        provider=message.get("provider"),
        action="quarantine",
        target=message_id,
        status="accepted",
        mock_mode=True,
        requested_by=request.headers.get("x-requested-by", "system"),
        message_id=message_id,
        detail={"note": "mock action"},
    )
    return {
        "status": "accepted",
        "mock_mode": True,
        "action_id": audit["id"],
        "message": "Quarantine request accepted (mock mode)",
    }

@app.post("/threat-intel/messages/{message_id}/actions/release")
def threat_intel_action_release(message_id: str, request: Request):
    record = get_email_message_record(message_id)
    if not record:
        raise HTTPException(404, "Message not found")
    message = record["message"]
    audit = record_threat_audit(
        mailbox=message.get("mailbox"),
        provider=message.get("provider"),
        action="release",
        target=message_id,
        status="accepted",
        mock_mode=True,
        requested_by=request.headers.get("x-requested-by", "system"),
        message_id=message_id,
        detail={"note": "mock action"},
    )
    return {
        "status": "accepted",
        "mock_mode": True,
        "action_id": audit["id"],
        "message": "Release request accepted (mock mode)",
    }

@app.post("/threat-intel/actions/block-sender")
def threat_intel_block_sender(payload: BlockSenderRequest, request: Request):
    if not payload.sender:
        raise HTTPException(400, "Missing sender")
    audit = record_threat_audit(
        mailbox=payload.mailbox,
        provider=None,
        action="block_sender",
        target=payload.sender,
        status="accepted",
        mock_mode=True,
        requested_by=request.headers.get("x-requested-by", "system"),
        message_id=None,
        detail={"note": "mock action"},
    )
    return {
        "status": "accepted",
        "mock_mode": True,
        "action_id": audit["id"],
        "message": "Block sender request accepted (mock mode)",
    }

@app.post("/threat-intel/actions/block-url")
def threat_intel_block_url(payload: BlockUrlRequest, request: Request):
    if not payload.url:
        raise HTTPException(400, "Missing url")
    audit = record_threat_audit(
        mailbox=payload.mailbox,
        provider=None,
        action="block_url",
        target=payload.url,
        status="accepted",
        mock_mode=True,
        requested_by=request.headers.get("x-requested-by", "system"),
        message_id=None,
        detail={"note": "mock action"},
    )
    return {
        "status": "accepted",
        "mock_mode": True,
        "action_id": audit["id"],
        "message": "Block URL request accepted (mock mode)",
    }

@app.get("/threat-intel/audit")
def threat_intel_audit(mailbox: str, limit: int = 100):
    if not mailbox:
        raise HTTPException(400, "Missing mailbox")
    limit = min(max(limit, 1), 200)
    return {"items": list_threat_audit(mailbox, limit)}

@app.get("/threat-intel/export")
def threat_intel_export(
    mailbox: str,
    range: Optional[str] = None,
    format: str = "json",
    q: Optional[str] = None,
    min_score: Optional[int] = None,
):
    if not mailbox:
        raise HTTPException(400, "Missing mailbox")
    q = sanitize_search_query(q)
    range_delta = parse_range(range)
    cutoff = datetime.now(timezone.utc) - range_delta if range_delta else None
    records = fetch_threat_records(mailbox, provider=None)
    items: List[Dict[str, Any]] = []
    for record in records:
        message = record["message"]
        assessment = record["assessment"]
        received_at = datetime.fromisoformat(message["received_at"])
        if cutoff and received_at < cutoff:
            continue
        score = assessment.get("score") if assessment else 0
        if min_score is not None and score < min_score:
            continue
        if q:
            haystack = " ".join(
                [
                    (message.get("subject") or ""),
                    ((message.get("from") or {}).get("email") or ""),
                    " ".join([u.get("url") or "" for u in message.get("urls") or []]),
                ]
            ).lower()
            if q.lower() not in haystack:
                continue
        items.append(build_threat_item(message, assessment))
    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "id",
                "received_at",
                "from",
                "to",
                "subject",
                "score",
                "verdict",
                "threat_type",
                "urls",
                "attachments",
                "spoofing_signals",
                "dlp_violations",
            ],
        )
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    **item,
                    "from": json.dumps(item.get("from")),
                    "to": json.dumps(item.get("to")),
                    "urls": json.dumps(item.get("urls")),
                    "attachments": json.dumps(item.get("attachments")),
                    "spoofing_signals": json.dumps(item.get("spoofing_signals")),
                    "dlp_violations": json.dumps(item.get("dlp_violations")),
                }
            )
        return PlainTextResponse(output.getvalue(), media_type="text/csv")
    if format != "json":
        raise HTTPException(400, "Invalid format (csv|json)")
    return {"items": items}

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
