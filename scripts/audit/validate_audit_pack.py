#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple


REQUIRED = [
    "schemas/kql_schema_runtime.json",
    "schemas/opensearch_indices.json",
    "schemas/opensearch_aliases.json",
    "schemas/schema_drift_report.md",
    "rules/rules.json",
    "metrics/metrics_ingest.json",
    "metrics/parse_errors_summary.json",
    "metrics/parse_errors_samples.jsonl",
    "metrics/latency_ingest_searchable.json",
    "metrics/latency_rule_alert.json",
    "metrics/rules_fired_top.json",
    "metrics/alerts_samples.jsonl",
    "edr/edr_audit_logs.jsonl",
    "repo/docker_compose_resolved.yml",
    "repo/architecture_overview.md",
]


def _find_placeholders(base: Path) -> List[Path]:
    placeholders = []
    for path in base.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "NO DISPONIBLE" in text:
                placeholders.append(path)
    return placeholders


def _check_required(base: Path) -> List[Tuple[str, str]]:
    missing = []
    for rel in REQUIRED:
        path = base / rel
        if not path.exists() or path.stat().st_size == 0:
            missing.append((rel, "missing"))
    events_raw = list((base / "events_raw").glob("*.jsonl"))
    events_norm = list((base / "events_normalized").glob("*.jsonl"))
    mappings = list((base / "docs").glob("mapping_*.md"))
    if not events_raw:
        missing.append(("events_raw/*.jsonl", "missing"))
    if not events_norm:
        missing.append(("events_normalized/*.jsonl", "missing"))
    if not mappings:
        missing.append(("docs/mapping_*.md", "missing"))
    return missing


def main() -> int:
    base = Path("audit_inputs")
    base.mkdir(parents=True, exist_ok=True)
    report_md = base / "VALIDATION_REPORT.md"
    report_json = base / "VALIDATION_REPORT.json"

    placeholders = _find_placeholders(base)
    missing = _check_required(base)

    status = "INPUTS READY" if not placeholders and not missing else "INPUTS STILL MISSING"

    report = {
        "status": status,
        "missing": [item for item, _ in missing],
        "placeholders": [str(path) for path in placeholders],
    }

    report_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [f"# {status}", "", "## Missing artifacts"]
    if missing:
        for rel, reason in missing:
            lines.append(f"- {rel} ({reason})")
    else:
        lines.append("(none)")
    lines.append("")
    lines.append("## Placeholders detected")
    if placeholders:
        for path in placeholders:
            lines.append(f"- {path}")
    else:
        lines.append("(none)")

    report_md.write_text("\n".join(lines), encoding="utf-8")

    if status != "INPUTS READY":
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
