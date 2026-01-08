"""Core unit tests for agent configuration and payloads."""

from __future__ import annotations

from agent import agent


def test_env_overrides_config(monkeypatch):
    original = agent.CONFIG
    agent.CONFIG = {"api_url": "http://config", "agent_token": "config-token"}
    monkeypatch.setenv("EVENTSEC_AGENT_API_URL", "http://env")
    assert agent.get_config_value("api_url") == "http://env"
    agent.CONFIG = original


def test_agent_headers_prefers_api_key(monkeypatch):
    original = agent.CONFIG
    agent.CONFIG = {}
    monkeypatch.setenv("EVENTSEC_AGENT_AGENT_API_KEY", "api-key")
    monkeypatch.setenv("EVENTSEC_AGENT_AGENT_TOKEN", "shared-token")
    headers = agent.agent_headers()
    assert headers["X-Agent-Key"] == "api-key"
    assert "X-Agent-Token" not in headers
    agent.CONFIG = original


def test_agent_headers_falls_back_to_token(monkeypatch):
    original = agent.CONFIG
    agent.CONFIG = {"agent_token": "config-token"}
    monkeypatch.delenv("EVENTSEC_AGENT_AGENT_API_KEY", raising=False)
    monkeypatch.delenv("EVENTSEC_AGENT_AGENT_TOKEN", raising=False)
    headers = agent.agent_headers()
    assert headers["X-Agent-Token"] == "config-token"
    agent.CONFIG = original


def test_status_event_schema():
    event = agent.build_status_event("online")
    assert event["event_type"] == "agent_status"
    assert event["severity"] == "info"
    assert event["category"] == "status"
    details = event["details"]
    for key in ("timestamp", "hostname", "os", "status"):
        assert key in details
