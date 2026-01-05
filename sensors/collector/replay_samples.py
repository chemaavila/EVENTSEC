from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import requests

API_BASE = os.getenv("EVENTSEC_API_BASE", "http://localhost:8000").rstrip("/")
INGEST_URL = f"{API_BASE}/ingest/network/bulk"
TOKEN = os.getenv("EVENTSEC_INGEST_TOKEN", "")
SENSOR_NAME = os.getenv("SENSOR_NAME", "sample-replayer")

SAMPLES_DIR = Path(os.getenv("SAMPLES_DIR", "../../docs/network_ids/samples")).resolve()


def _headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["X-Agent-Token"] = TOKEN
    return headers


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        events.append(json.loads(line))
    return events


def _send(source: str, events: List[Dict[str, Any]]) -> None:
    payload = {
        "source": source,
        "sensor": {"name": SENSOR_NAME, "kind": source, "location": "samples"},
        "events": events,
        "meta": {"collector_version": "sample-replayer"},
    }
    response = requests.post(INGEST_URL, json=payload, headers=_headers(), timeout=10)
    response.raise_for_status()
    print(f"{source} -> {response.json()}")


if __name__ == "__main__":
    for sample in SAMPLES_DIR.glob("*.jsonl"):
        source = "suricata" if "suricata" in sample.name else "zeek"
        events = _load_jsonl(sample)
        if events:
            _send(source, events)
