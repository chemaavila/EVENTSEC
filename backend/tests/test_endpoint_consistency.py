from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from backend.app import database, models
from backend.app.routers import events_router


def _fake_get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_enroll_creates_endpoint(monkeypatch) -> None:
    from backend.app import main as main_mod

    app = main_mod.app
    original_startup = list(app.router.on_startup)
    original_shutdown = list(app.router.on_shutdown)
    app.router.on_startup = []
    app.router.on_shutdown = []
    app.dependency_overrides[database.get_db] = _fake_get_db

    payload = {
        "name": "endpoint-a",
        "os": "linux",
        "ip_address": "10.0.0.5",
        "version": "0.3.0",
        "enrollment_key": "eventsec-enroll",
    }
    try:
        with TestClient(app) as client:
            response = client.post("/agents/enroll", json=payload)
            assert response.status_code == 200
    finally:
        app.dependency_overrides = {}
        app.router.on_startup = original_startup
        app.router.on_shutdown = original_shutdown

    db = database.SessionLocal()
    try:
        endpoint = (
            db.query(models.Endpoint)
            .filter(models.Endpoint.hostname == "endpoint-a")
            .one_or_none()
        )
        assert endpoint is not None
    finally:
        db.close()


def test_event_ingest_creates_endpoint(monkeypatch) -> None:
    monkeypatch.setenv("EVENTSEC_AGENT_TOKEN", "shared-123")

    async def _fake_get_event_queue(_request):  # noqa: ANN001
        class _DummyQueue:
            def put_nowait(self, _item):  # noqa: ANN001
                return None

            def qsize(self):  # noqa: ANN001
                return 0

        return _DummyQueue()

    monkeypatch.setattr(events_router, "get_event_queue", _fake_get_event_queue)

    from backend.app import main as main_mod

    app = main_mod.app
    original_startup = list(app.router.on_startup)
    original_shutdown = list(app.router.on_shutdown)
    app.router.on_startup = []
    app.router.on_shutdown = []
    app.dependency_overrides[database.get_db] = _fake_get_db

    payload = {
        "event_type": "edr.url_visit",
        "severity": "low",
        "category": "edr",
        "details": {"hostname": "endpoint-b", "url": "http://example.test"},
    }

    try:
        with TestClient(app) as client:
            response = client.post(
                "/events", json=payload, headers={"X-Agent-Token": "shared-123"}
            )
            assert response.status_code == 200
    finally:
        app.dependency_overrides = {}
        app.router.on_startup = original_startup
        app.router.on_shutdown = original_shutdown

    db = database.SessionLocal()
    try:
        endpoint = (
            db.query(models.Endpoint)
            .filter(models.Endpoint.hostname == "endpoint-b")
            .one_or_none()
        )
        assert endpoint is not None
        assert endpoint.last_seen is not None
        assert endpoint.last_seen <= datetime.now(timezone.utc)
    finally:
        db.close()
