"""
Unit tests for agent authentication logic.

We keep these tests DB-free and server-free to avoid requiring a running DB in CI.
"""

from __future__ import annotations

import types

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.app import main as main_mod
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
