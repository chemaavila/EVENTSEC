import importlib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load_app(tmp_path):
    os.environ["TOKEN_DB_PATH"] = str(tmp_path / "test.db")
    if "app" in sys.modules:
        del sys.modules["app"]
    import app as app_module
    importlib.reload(app_module)
    app_module.init_db()
    return app_module


def test_normalize_gmail_message(tmp_path):
    app_module = load_app(tmp_path)
    full = {
        "id": "msg-1",
        "threadId": "thread-1",
        "snippet": "Hello there",
        "internalDate": str(int(datetime.now(tz=timezone.utc).timestamp() * 1000)),
        "payload": {
            "headers": [
                {"name": "From", "value": "Alice <alice@example.com>"},
                {"name": "To", "value": "Bob <bob@example.net>"},
                {"name": "Subject", "value": "Verify account"},
                {"name": "Authentication-Results", "value": "spf=pass dkim=pass dmarc=pass"},
            ],
            "body": {"data": ""},
            "parts": [
                {"filename": "invoice.zip", "mimeType": "application/zip", "body": {"size": 1234}},
            ],
        },
    }
    message, body_text = app_module.normalize_gmail_message("mbox@example.com", full)
    assert message.provider == "google"
    assert message.from_.email == "alice@example.com"
    assert message.to[0].email == "bob@example.net"
    assert message.subject == "Verify account"
    assert message.attachments[0].filename == "invoice.zip"
    assert message.auth_results.spf == "pass"
    assert body_text == ""


def test_list_filters(tmp_path):
    app_module = load_app(tmp_path)
    client = TestClient(app_module.app)
    now = datetime.now(timezone.utc)
    msg_low = app_module.EmailMessage(
        id="msg-low",
        provider="google",
        mailbox="mbox@example.com",
        received_at=now,
        from_=app_module.EmailParty(email="low@example.com", domain="example.com"),
        to=[app_module.EmailParty(email="user@example.com", domain="example.com")],
        subject="hello",
        urls=[app_module.EmailUrl(url="https://example.com")],
    )
    msg_high = app_module.EmailMessage(
        id="msg-high",
        provider="google",
        mailbox="mbox@example.com",
        received_at=now,
        from_=app_module.EmailParty(email="high@example.com", domain="example.com"),
        to=[app_module.EmailParty(email="user@example.com", domain="example.com")],
        subject="urgent verify",
        auth_results=app_module.EmailAuthResults(spf="fail"),
    )
    app_module.upsert_email_message(msg_low)
    app_module.upsert_email_message(msg_high)
    app_module.upsert_email_assessment(
        app_module.EmailThreatAssessment(
            message_id="msg-low",
            score=10,
            verdict="low",
            reasons=[],
            matched_iocs=[],
            action_recommended="none",
        )
    )
    app_module.upsert_email_assessment(
        app_module.EmailThreatAssessment(
            message_id="msg-high",
            score=80,
            verdict="phishing",
            reasons=["Reply-To mismatch (evil.com vs example.com)"],
            matched_iocs=[],
            action_recommended="quarantine",
        )
    )
    response = client.get(
        "/threat-intel/messages",
        params={"mailbox": "mbox@example.com", "min_score": 70},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == "msg-high"
    response = client.get(
        "/threat-intel/messages",
        params={"mailbox": "mbox@example.com", "q": "https://example.com", "page_size": 1},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_summary_and_audit(tmp_path):
    app_module = load_app(tmp_path)
    client = TestClient(app_module.app)
    now = datetime.now(timezone.utc)
    msg = app_module.EmailMessage(
        id="msg-1",
        provider="google",
        mailbox="mbox@example.com",
        received_at=now,
        from_=app_module.EmailParty(email="spoof@example.com", domain="example.com"),
        to=[app_module.EmailParty(email="target@example.com", domain="example.com")],
        subject="verify account",
        auth_results=app_module.EmailAuthResults(spf="fail"),
    )
    app_module.upsert_email_message(msg)
    app_module.upsert_email_assessment(
        app_module.EmailThreatAssessment(
            message_id="msg-1",
            score=75,
            verdict="phishing",
            reasons=["Reply-To mismatch (evil.com vs example.com)"],
            matched_iocs=[],
            action_recommended="quarantine",
        )
    )
    app_module.upsert_mailbox_state(
        mailbox="mbox@example.com",
        provider="google",
        connected=True,
        last_sync_at=now,
        last_sync_ok=True,
        last_error=None,
    )
    summary = client.get("/threat-intel/summary", params={"mailbox": "mbox@example.com"}).json()
    assert summary["processed_count"] == 1
    assert summary["blocked_count"] == 1
    assert summary["spoofing_count"] == 1
    assert summary["provider"] == "google"
    action = client.post("/threat-intel/messages/msg-1/actions/quarantine")
    assert action.status_code == 200
    audit = client.get("/threat-intel/audit", params={"mailbox": "mbox@example.com"}).json()
    assert audit["items"][0]["action"] == "quarantine"
