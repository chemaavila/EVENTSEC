from __future__ import annotations

import os
from fastapi.testclient import TestClient

from backend.app import search
from backend.app.main import app


def test_network_ingest_bulk(monkeypatch):
    os.environ["EVENTSEC_AGENT_TOKEN"] = "test-token"
    monkeypatch.setattr(search, "ensure_indices", lambda: None)
    monkeypatch.setattr(search, "bulk_index_network_events", lambda _docs: None)

    with TestClient(app) as client:
        payload = {
            "source": "suricata",
            "sensor": {"name": "sensor-1", "kind": "suricata", "location": "lab"},
            "events": [
                {
                    "timestamp": "2024-01-01T00:00:00.000Z",
                    "event_type": "alert",
                    "src_ip": "10.0.0.1",
                    "src_port": 1111,
                    "dest_ip": "10.0.0.2",
                    "dest_port": 80,
                    "proto": "TCP",
                    "alert": {"signature": "ET MALWARE Possible Malware traffic", "severity": 1},
                }
            ],
        }
        response = client.post(
            "/ingest/network/bulk",
            json=payload,
            headers={"X-Agent-Token": "test-token"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["accepted"] == 1
        assert body["rejected"] == 0


def test_network_ingest_rejects_missing_auth(monkeypatch):
    monkeypatch.setattr(search, "ensure_indices", lambda: None)
    with TestClient(app) as client:
        response = client.post(
            "/ingest/network/bulk",
            json={"source": "suricata", "sensor": {"name": "s", "kind": "suricata"}, "events": []},
        )
        assert response.status_code == 401
