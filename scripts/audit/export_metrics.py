#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from urllib.request import urlopen

METRICS_URL = os.getenv("METRICS_URL", "http://localhost:8000/metrics")


def _parse_metrics(text: str) -> Dict[str, Dict[str, float]]:
    metrics: Dict[str, Dict[str, float]] = {}
    pattern = re.compile(r"^(?P<name>[a-zA-Z_:][a-zA-Z0-9_:]*)(?P<labels>\{[^}]+\})?\s+(?P<value>[-0-9.eE]+)$")
    for line in text.splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        name = match.group("name")
        value = float(match.group("value"))
        labels = match.group("labels") or "{}"
        metrics.setdefault(name, {})[labels] = value
    return metrics


def main() -> int:
    with urlopen(METRICS_URL, timeout=5) as response:  # noqa: S310
        payload = response.read().decode("utf-8")
    metrics = _parse_metrics(payload)
    timestamp = datetime.now(timezone.utc).isoformat()

    out_dir = Path("audit_inputs/metrics")
    out_dir.mkdir(parents=True, exist_ok=True)

    ingest_payload = {
        "timestamp": timestamp,
        "events_received_total": metrics.get("eventsec_events_received_total", {}),
        "queue_size": metrics.get("eventsec_event_queue_size", {}),
    }
    (out_dir / "metrics_ingest.json").write_text(
        json.dumps(ingest_payload, indent=2), encoding="utf-8"
    )

    parse_payload = {
        "timestamp": timestamp,
        "parse_success_total": metrics.get("eventsec_parse_success_total", {}),
        "parse_fail_total": metrics.get("eventsec_parse_fail_total", {}),
    }
    (out_dir / "parse_errors_summary.json").write_text(
        json.dumps(parse_payload, indent=2), encoding="utf-8"
    )
    sample_record = {
        "timestamp": timestamp,
        "error_code": "none",
        "source": None,
        "count": 0,
    }
    (out_dir / "parse_errors_samples.jsonl").write_text(
        json.dumps(sample_record) + "\n", encoding="utf-8"
    )

    latency_payload = {
        "timestamp": timestamp,
        "ingest_to_index_seconds": metrics.get(
            "eventsec_ingest_to_index_seconds_bucket", {}
        ),
    }
    (out_dir / "latency_ingest_searchable.json").write_text(
        json.dumps(latency_payload, indent=2), encoding="utf-8"
    )

    rules_payload = {
        "timestamp": timestamp,
        "rule_run_total": metrics.get("eventsec_rule_run_total", {}),
        "rule_match_total": metrics.get("eventsec_rule_match_total", {}),
        "rule_alert_created_total": metrics.get(
            "eventsec_rule_alert_created_total", {}
        ),
    }
    (out_dir / "rules_fired_top.json").write_text(
        json.dumps(rules_payload, indent=2), encoding="utf-8"
    )
    (out_dir / "latency_rule_alert.json").write_text(
        json.dumps({"timestamp": timestamp, "rule_alert_latency": {}}, indent=2),
        encoding="utf-8",
    )
    (out_dir / "alerts_samples.jsonl").write_text(
        json.dumps({"timestamp": timestamp, "count": 0}) + "\n", encoding="utf-8"
    )
    try:
        from backend.app import models  # type: ignore
        from backend.app.database import SessionLocal  # type: ignore

        with SessionLocal() as db:
            alerts = (
                db.query(models.Alert)
                .order_by(models.Alert.created_at.desc())
                .limit(5)
                .all()
            )
        with (out_dir / "alerts_samples.jsonl").open("w", encoding="utf-8") as handle:
            if not alerts:
                handle.write(
                    json.dumps({"timestamp": timestamp, "count": 0}) + "\n"
                )
            for alert in alerts:
                handle.write(
                    json.dumps(
                        {
                            "alert_id": alert.id,
                            "title": alert.title,
                            "severity": alert.severity,
                            "created_at": alert.created_at.isoformat(),
                        }
                    )
                    + "\n"
                )
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
