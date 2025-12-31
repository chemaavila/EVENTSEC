"""
Unit tests for agent authentication logic.

We keep these tests DB-free and server-free to avoid requiring a running DB in CI.
"""

from __future__ import annotations

import types
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request

from backend.app import main as main_mod
from backend.app import database
from backend.app.routers import events_router
from backend.app.schemas import UserProfile


def _dummy_request() -> Request:
    # Minimal ASGI scope for a Request instance
    scope = {"type": "http", "method": "GET", "path": "/", "headers": []}
    return Request(scope)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_require_agent_auth_accepts_user_jwt_path():
    user = UserProfile(id=1, full_name="U", role="admin", email="u@example.com")
    result = await main_mod.require_agent_auth(
        _dummy_request(),
        current_user=user,
        agent_token=None,
        agent_key=None,
        db=object(),
    )
    assert result is None


@pytest.mark.asyncio
async def test_require_agent_auth_accepts_shared_token(monkeypatch):
    monkeypatch.setenv("EVENTSEC_AGENT_TOKEN", "shared-123")
    result = await main_mod.require_agent_auth(
        _dummy_request(),
        current_user=None,
        agent_token="shared-123",
        agent_key=None,
        db=object(),
    )
    assert result is None


@pytest.mark.asyncio
async def test_require_agent_auth_accepts_agent_key(monkeypatch):
    agent = types.SimpleNamespace(
        id=7, name="a", os="macOS", ip_address="1.2.3.4", version="0.3.0"
    )

    def _fake_lookup(_db, key):  # noqa: ANN001
        return agent if key == "agent-key-abc" else None

    monkeypatch.setattr(main_mod.crud, "get_agent_by_api_key", _fake_lookup)

    result = await main_mod.require_agent_auth(
        _dummy_request(),
        current_user=None,
        agent_token=None,
        agent_key="agent-key-abc",
        db=object(),
    )
    assert result is agent


@pytest.mark.asyncio
async def test_require_agent_auth_rejects_invalid(monkeypatch):
    monkeypatch.setenv("EVENTSEC_AGENT_TOKEN", "shared-123")

    def _fake_lookup(_db, _key):  # noqa: ANN001
        return None

    monkeypatch.setattr(main_mod.crud, "get_agent_by_api_key", _fake_lookup)

    with pytest.raises(HTTPException) as exc:
        await main_mod.require_agent_auth(
            _dummy_request(),
            current_user=None,
            agent_token="wrong",
            agent_key="wrong",
            db=object(),
        )

    assert exc.value.status_code == 401


def test_events_accept_shared_token(monkeypatch):
    monkeypatch.setenv("EVENTSEC_AGENT_TOKEN", "shared-123")

    async def _fake_get_event_queue(_request):  # noqa: ANN001
        class _DummyQueue:
            async def put(self, _item):  # noqa: ANN001
                return None

        return _DummyQueue()

    def _fake_create_event(_db, event):  # noqa: ANN001
        event.id = 123
        event.created_at = datetime.now(timezone.utc)
        return event

    def _fake_get_db():
        yield object()

    monkeypatch.setattr(events_router, "get_event_queue", _fake_get_event_queue)
    monkeypatch.setattr(main_mod.crud, "create_event", _fake_create_event)

    app = main_mod.app
    original_startup = list(app.router.on_startup)
    original_shutdown = list(app.router.on_shutdown)
    app.router.on_startup = []
    app.router.on_shutdown = []
    app.dependency_overrides[database.get_db] = _fake_get_db

    payload = {"event_type": "agent_status", "severity": "low", "category": "agent", "details": {}}
    try:
        with TestClient(app) as client:
            response = client.post("/events", json=payload, headers={"X-Agent-Token": "shared-123"})
    finally:
        app.dependency_overrides = {}
        app.router.on_startup = original_startup
        app.router.on_shutdown = original_shutdown

    assert response.status_code == 200
    body = response.json()
    assert body["agent_id"] is None
