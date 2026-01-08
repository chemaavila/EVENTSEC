"""Integration tests using the mock collector."""

from __future__ import annotations

import json
from pathlib import Path

from agent import agent
from agent.tests import mock_collector


def _read_paths(jsonl_path: Path) -> list[str]:
    if not jsonl_path.exists():
        return []
    return [json.loads(line)["path"] for line in jsonl_path.read_text(encoding="utf-8").splitlines()]


def _agent_host() -> dict[str, str]:
    return {
        "hostname": "agent-host",
        "username": "tester",
        "os": "Linux",
        "os_version": "test",
    }


def test_send_heartbeat_and_event_paths(monkeypatch, tmp_path):
    output_path = tmp_path / "received.jsonl"
    server, _, _state = mock_collector.start_mock_collector(output_path=output_path)
    monkeypatch.setenv(
        "EVENTSEC_AGENT_API_URL", f"http://127.0.0.1:{server.server_address[1]}"
    )
    monkeypatch.setenv("EVENTSEC_AGENT_AGENT_ID", "1")
    monkeypatch.setenv("EVENTSEC_AGENT_AGENT_API_KEY", "test-key")
    monkeypatch.setattr(agent.socket, "gethostbyname", lambda _name: "127.0.0.1")

    host = _agent_host()
    agent.send_heartbeat(host)
    agent.send_event(agent.build_status_event("online"), host)

    server.shutdown()
    server.server_close()

    paths = _read_paths(output_path)
    assert "/agent/heartbeat" in paths
    assert "/events" in paths


def test_fail_first_event_retry(monkeypatch, tmp_path):
    output_path = tmp_path / "received.jsonl"
    server, _, state = mock_collector.start_mock_collector(
        output_path=output_path, fail_first_status=401
    )
    monkeypatch.setenv(
        "EVENTSEC_AGENT_API_URL", f"http://127.0.0.1:{server.server_address[1]}"
    )
    monkeypatch.setenv("EVENTSEC_AGENT_AGENT_ID", "1")
    monkeypatch.setenv("EVENTSEC_AGENT_AGENT_API_KEY", "test-key")
    monkeypatch.setattr(agent.socket, "gethostbyname", lambda _name: "127.0.0.1")

    host = _agent_host()
    agent.send_event(agent.build_status_event("online"), host)

    server.shutdown()
    server.server_close()

    event_paths = [entry["path"] for entry in state.received if entry["path"] == "/events"]
    assert len(event_paths) >= 2
