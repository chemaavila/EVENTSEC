from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any, Dict, List

from backend.app import crud, models
from backend.app.database import SessionLocal


def _load_json_from_zip(zip_path: Path, filename: str) -> List[Dict[str, Any]]:
    with zipfile.ZipFile(zip_path) as archive:
        with archive.open(filename) as handle:
            return json.load(handle)


def _parse_analytic_summary(lines: List[str]) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("---") or stripped.startswith("idx"):
            continue
        parts = [part.strip() for part in stripped.split("|")]
        if len(parts) < 4:
            continue
        idx, severity, category, title = parts[:4]
        try:
            rule_id = int(idx)
        except ValueError:
            continue
        entries.append(
            {
                "id": rule_id,
                "severity": (severity or "medium").lower(),
                "category": category or None,
                "title": title,
            }
        )
    return entries


def _parse_correlation_summary(lines: List[str]) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("---") or stripped.startswith("idx"):
            continue
        parts = [part.strip() for part in stripped.split("|")]
        if len(parts) < 5:
            continue
        idx, severity, window, rule_type, title = parts[:5]
        try:
            rule_id = int(idx)
        except ValueError:
            continue
        window_minutes = None
        if window:
            try:
                window_minutes = int(window)
            except ValueError:
                window_minutes = None
        entries.append(
            {
                "id": rule_id,
                "severity": (severity or "medium").lower(),
                "window_minutes": window_minutes,
                "logic": {"type": rule_type} if rule_type else {},
                "title": title,
            }
        )
    return entries


def _load_from_summary(summary_path: Path) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    text = summary_path.read_text(encoding="utf-8")
    sections = text.split("CORRELATION RULES (100)")
    analytic_section = sections[0].split("ANALYTIC RULES (100)")[-1]
    correlation_section = sections[1] if len(sections) > 1 else ""

    analytic_lines = analytic_section.strip().splitlines()
    correlation_lines = correlation_section.strip().splitlines()

    analytics = _parse_analytic_summary(analytic_lines)
    correlations = _parse_correlation_summary(correlation_lines)
    return analytics, correlations


def import_rules(zip_path: Path) -> int:
    if zip_path.suffix.lower() == ".txt":
        analytics, correlations = _load_from_summary(zip_path)
    else:
        analytics = _load_json_from_zip(zip_path, "analytic_rules_100.json")
        correlations = _load_json_from_zip(zip_path, "correlation_rules_100.json")

    created = 0
    db = SessionLocal()
    try:
        for entry in analytics:
            rule_id = entry.get("id")
            rule = crud.get_analytic_rule(db, rule_id) if rule_id else None
            rule = rule or models.AnalyticRule(created_at=models.utcnow())
            rule.title = entry.get("title") or entry.get("name") or "Untitled"
            rule.description = entry.get("description", "")
            rule.severity = entry.get("severity", "medium")
            rule.category = entry.get("category")
            rule.data_sources = entry.get("data_sources", entry.get("dataSources", []))
            rule.query = entry.get("query", {})
            rule.tags = entry.get("tags", [])
            rule.enabled = bool(entry.get("enabled", True))
            if rule_id:
                rule.id = rule_id
            crud.upsert_analytic_rule(db, rule)
            created += 1

        for entry in correlations:
            rule_id = entry.get("id")
            rule = crud.get_correlation_rule(db, rule_id) if rule_id else None
            rule = rule or models.CorrelationRule(created_at=models.utcnow())
            rule.title = entry.get("title") or entry.get("name") or "Untitled"
            rule.description = entry.get("description", "")
            rule.severity = entry.get("severity", "medium")
            rule.window_minutes = entry.get("window_minutes", entry.get("windowMinutes"))
            rule.logic = entry.get("logic", {})
            rule.tags = entry.get("tags", [])
            rule.enabled = bool(entry.get("enabled", True))
            if rule_id:
                rule.id = rule_id
            crud.upsert_correlation_rule(db, rule)
            created += 1
    finally:
        db.close()

    return created


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Import EventSec rule packs from zip")
    parser.add_argument("zip_path", type=Path, help="Path to eventsec_rules_pack_100_100_v2.zip")
    args = parser.parse_args()

    if not args.zip_path.exists():
        raise SystemExit(f"Zip file not found: {args.zip_path}")

    count = import_rules(args.zip_path)
    print(f"Imported {count} rules")


if __name__ == "__main__":
    main()
