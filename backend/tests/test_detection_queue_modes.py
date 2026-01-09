from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from backend.app import config, models
from backend.app.auth import require_agent_auth
from backend.app.main import app


def _override_agent():
    return None


async def _noop_worker(*_args, **_kwargs) -> None:
    await asyncio.sleep(0)


def test_db_queue_mode_creates_pending_event(monkeypatch, db_session):
    monkeypatch.setattr(config.settings, "detection_queue_mode", "db")
    monkeypatch.setattr("backend.app.main.process_db_event_queue", _noop_worker)
    app.dependency_overrides[require_agent_auth] = _override_agent

    client = TestClient(app)
    response = client.post(
        "/events",
        json={
            "event_type": "edr.process_start",
            "severity": "low",
            "category": "edr",
            "details": {"hostname": "test-host"},
        },
        headers={"X-Agent-Token": "eventsec-dev-token"},
    )

    assert response.status_code == 200

    pending = db_session.query(models.PendingEvent).all()
    assert len(pending) == 1
    assert pending[0].processed_at is None

    app.dependency_overrides = {}
