from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, List

import requests

from batcher import Batcher
from state import CollectorState
from tailer import iter_new_lines

API_BASE = os.getenv("EVENTSEC_API_BASE", "http://localhost:8000").rstrip("/")
INGEST_URL = f"{API_BASE}/ingest/network/bulk"
TOKEN = os.getenv("EVENTSEC_INGEST_TOKEN", "")
SENSOR_NAME = os.getenv("SENSOR_NAME", "collector-1")
SENSOR_LOCATION = os.getenv("SENSOR_LOCATION", "local")

SURICATA_EVE_PATH = os.getenv("SURICATA_EVE_PATH")
ZEEK_LOG_DIR = os.getenv("ZEEK_LOG_DIR")

MAX_BATCH_EVENTS = int(os.getenv("MAX_BATCH_EVENTS", "500"))
MAX_BATCH_BYTES = int(os.getenv("MAX_BATCH_BYTES", "2000000"))
FLUSH_INTERVAL = float(os.getenv("FLUSH_INTERVAL", "2.0"))
SLEEP_INTERVAL = float(os.getenv("SLEEP_INTERVAL", "1.0"))

STATE_PATH = Path(os.getenv("COLLECTOR_STATE", "/state/state.json"))


class NetworkCollector:
    def __init__(self) -> None:
        self.state = CollectorState(STATE_PATH)
        self.state.load()
        self.session = requests.Session()

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if TOKEN:
            headers["X-Agent-Token"] = TOKEN
        return headers

    def _post_batch(self, source: str, events: List[Dict[str, Any]]) -> None:
        if not events:
            return
        payload = {
            "source": source,
            "sensor": {
                "name": SENSOR_NAME,
                "kind": source,
                "location": SENSOR_LOCATION,
            },
            "events": events,
            "meta": {
                "collector_version": "0.1",
                "host": os.getenv("HOSTNAME"),
            },
        }
        backoff = 1.0
        while True:
            try:
                resp = self.session.post(INGEST_URL, json=payload, headers=self._headers(), timeout=10)
                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    wait = float(retry_after) if retry_after else backoff
                    time.sleep(wait)
                    backoff = min(backoff * 2, 30)
                    continue
                resp.raise_for_status()
                return
            except requests.RequestException:
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)

    def _make_batcher(self, source: str) -> Batcher:
        return Batcher(
            max_events=MAX_BATCH_EVENTS,
            max_bytes=MAX_BATCH_BYTES,
            flush_interval=FLUSH_INTERVAL,
            send_batch=lambda events: self._post_batch(source, events),
        )

    def _iter_suricata_events(self) -> List[Dict[str, Any]]:
        if not SURICATA_EVE_PATH:
            return []
        path = Path(SURICATA_EVE_PATH)
        events: List[Dict[str, Any]] = []
        for line, _ in iter_new_lines(path, self.state):
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return events

    def _iter_zeek_events(self) -> List[Dict[str, Any]]:
        if not ZEEK_LOG_DIR:
            return []
        base = Path(ZEEK_LOG_DIR)
        events: List[Dict[str, Any]] = []
        for path in list(base.glob("*.json")) + list(base.glob("*.log")):
            for line, _ in iter_new_lines(path, self.state):
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return events

    def run(self) -> None:
        suricata_batcher = self._make_batcher("suricata")
        zeek_batcher = self._make_batcher("zeek")
        while True:
            for event in self._iter_suricata_events():
                suricata_batcher.add(event)
            for event in self._iter_zeek_events():
                zeek_batcher.add(event)
            suricata_batcher.flush()
            zeek_batcher.flush()
            time.sleep(SLEEP_INTERVAL)


if __name__ == "__main__":
    NetworkCollector().run()
