#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.app import models
from backend.app.database import SessionLocal


def main() -> int:
    out_dir = Path("audit_inputs/rules")
    out_dir.mkdir(parents=True, exist_ok=True)

    rules_payload = []
    with SessionLocal() as db:
        rules = db.query(models.DetectionRule).all()
        for rule in rules:
            rules_payload.append(
                {
                    "rule_id": rule.id,
                    "name": rule.name,
                    "description": rule.description,
                    "severity": rule.severity,
                    "enabled": rule.enabled,
                    "conditions": rule.conditions,
                    "schedule": None,
                    "lookback": None,
                    "suppression": None,
                    "grouping": None,
                    "outputs": [],
                    "mitre": [],
                }
            )

    (out_dir / "rules.json").write_text(
        json.dumps({"rules": rules_payload}, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
