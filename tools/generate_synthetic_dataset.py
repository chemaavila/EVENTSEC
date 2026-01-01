#!/usr/bin/env python3
from __future__ import annotations

import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List


SOURCES = ["agent_status", "logcollector", "network", "siem", "edr"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _raw_event(source: str, received_time: str, correlation_id: str, raw_id: str) -> Dict:
    payload = {
        "event_type": source,
        "severity": random.choice(["low", "medium", "high"]),
        "category": source,
        "details": {
            "message": f"Synthetic event for {source}",
            "correlation_id": correlation_id,
            "raw_ref": raw_id,
        },
    }
    return {
        "raw_id": raw_id,
        "source": source,
        "received_time": received_time,
        "raw_payload": payload,
        "transport_meta": {"generator": "synthetic"},
        "tenant_id": None,
        "collector_id": "synthetic-generator",
        "correlation_id": correlation_id,
        "parse_status": "synthetic",
    }


def _normalized_event(
    source: str,
    received_time: str,
    correlation_id: str,
    raw_id: str,
    event_id: int,
) -> Dict:
    return {
        "event_id": event_id,
        "agent_id": None,
        "event_type": source,
        "severity": random.choice(["low", "medium", "high"]),
        "category": source,
        "source": source,
        "details": {
            "message": f"Synthetic normalized event for {source}",
            "correlation_id": correlation_id,
            "raw_ref": raw_id,
            "received_time": received_time,
        },
        "message": f"Synthetic normalized event for {source}",
        "correlation_id": correlation_id,
        "raw_ref": raw_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "received_time": received_time,
    }


def _write_jsonl(path: Path, rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    raw_dir = Path("audit_inputs/events_raw")
    norm_dir = Path("audit_inputs/events_normalized")
    raw_dir.mkdir(parents=True, exist_ok=True)
    norm_dir.mkdir(parents=True, exist_ok=True)

    event_id = 1
    for source in SOURCES:
        raw_rows = []
        norm_rows = []
        for idx in range(5):
            raw_id = str(uuid.uuid4())
            correlation_id = str(uuid.uuid4())
            received_time = (_now() - timedelta(minutes=idx)).isoformat()
            raw_rows.append(_raw_event(source, received_time, correlation_id, raw_id))
            norm_rows.append(
                _normalized_event(source, received_time, correlation_id, raw_id, event_id)
            )
            event_id += 1
        _write_jsonl(raw_dir / f"{source}.jsonl", raw_rows)
        _write_jsonl(norm_dir / f"{source}.jsonl", norm_rows)

    expected = {
        "tests": [
            {
                "id": "T01",
                "query_or_rule": "events | where event_type == 'agent_status' | limit 5",
                "input_files": ["events_normalized/agent_status.jsonl"],
                "expected": {
                    "row_count": 5,
                    "columns": ["event_type", "severity", "timestamp"],
                    "must_contain": ["agent_status"],
                    "must_not_contain": [],
                },
            },
            {
                "id": "T02",
                "query_or_rule": "events | where severity == 'high' | limit 5",
                "input_files": ["events_normalized/logcollector.jsonl"],
                "expected": {
                    "row_count": 5,
                    "columns": ["severity"],
                    "must_contain": ["high"],
                    "must_not_contain": [],
                },
            },
            {
                "id": "T03",
                "query_or_rule": "events | where category == 'network' | limit 5",
                "input_files": ["events_normalized/network.jsonl"],
                "expected": {
                    "row_count": 5,
                    "columns": ["category"],
                    "must_contain": ["network"],
                    "must_not_contain": [],
                },
            },
            {
                "id": "T04",
                "query_or_rule": "events | where event_type == 'siem' | limit 5",
                "input_files": ["events_normalized/siem.jsonl"],
                "expected": {
                    "row_count": 5,
                    "columns": ["event_type"],
                    "must_contain": ["siem"],
                    "must_not_contain": [],
                },
            },
            {
                "id": "T05",
                "query_or_rule": "events | where event_type == 'edr' | limit 5",
                "input_files": ["events_normalized/edr.jsonl"],
                "expected": {
                    "row_count": 5,
                    "columns": ["event_type"],
                    "must_contain": ["edr"],
                    "must_not_contain": [],
                },
            },
            {
                "id": "T06",
                "query_or_rule": "events | where correlation_id != '' | limit 5",
                "input_files": ["events_normalized/agent_status.jsonl"],
                "expected": {
                    "row_count": 5,
                    "columns": ["correlation_id"],
                    "must_contain": [],
                    "must_not_contain": [],
                },
            },
            {
                "id": "T07",
                "query_or_rule": "events | project event_type, severity | limit 5",
                "input_files": ["events_normalized/logcollector.jsonl"],
                "expected": {
                    "row_count": 5,
                    "columns": ["event_type", "severity"],
                    "must_contain": ["logcollector"],
                    "must_not_contain": [],
                },
            },
            {
                "id": "T08",
                "query_or_rule": "events | where details.message contains 'Synthetic' | limit 5",
                "input_files": ["events_normalized/network.jsonl"],
                "expected": {
                    "row_count": 5,
                    "columns": ["details"],
                    "must_contain": ["Synthetic"],
                    "must_not_contain": [],
                },
            },
            {
                "id": "T09",
                "query_or_rule": "events | where source == 'siem' | limit 5",
                "input_files": ["events_normalized/siem.jsonl"],
                "expected": {
                    "row_count": 5,
                    "columns": ["source"],
                    "must_contain": ["siem"],
                    "must_not_contain": [],
                },
            },
            {
                "id": "T10",
                "query_or_rule": "events | where raw_ref != '' | limit 5",
                "input_files": ["events_normalized/edr.jsonl"],
                "expected": {
                    "row_count": 5,
                    "columns": ["raw_ref"],
                    "must_contain": [],
                    "must_not_contain": [],
                },
            }
        ]
    }
    Path("audit_inputs/expected_outputs.json").write_text(
        json.dumps(expected, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
