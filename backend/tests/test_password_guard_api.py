from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from backend.app import models, search
from backend.app.main import app


def test_password_guard_ingest_creates_alert(db_session, monkeypatch):
    os.environ["EVENTSEC_AGENT_TOKEN"] = "test-token"
    monkeypatch.setattr(search, "index_alert", lambda _doc: None)

    payload = {
        "host_id": "host-1",
        "user": "alice",
        "entry_id": "entry-123",
        "entry_label": "Okta Admin",
        "exposure_count": 3,
        "action": "DETECTED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "client_version": "0.1.0",
    }

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/password-guard/events",
            json=payload,
            headers={"X-Agent-Token": "test-token"},
        )

    assert response.status_code == 201
    body = response.json()
    assert body["alert_id"] is not None

    alerts = db_session.query(models.Alert).all()
    assert len(alerts) == 1
    assert alerts[0].title == "Pwned password detected"


def test_password_guard_ingest_no_alert(db_session):
    os.environ["EVENTSEC_AGENT_TOKEN"] = "test-token"
    payload = {
        "host_id": "host-2",
        "user": "bob",
        "entry_id": "entry-456",
        "entry_label": "Github",
        "exposure_count": 0,
        "action": "ROTATED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "client_version": "0.1.0",
    }

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/password-guard/events",
            json=payload,
            headers={"X-Agent-Token": "test-token"},
        )

    assert response.status_code == 201
    body = response.json()
    assert body["alert_id"] is None

    alerts = db_session.query(models.Alert).all()
    assert len(alerts) == 0
