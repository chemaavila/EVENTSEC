#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.app import models
from backend.app.database import SessionLocal


def main() -> int:
    out_path = Path("audit_inputs/edr/edr_audit_logs.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with SessionLocal() as db:
        logs = (
            db.query(models.ActionLog)
            .filter(models.ActionLog.action_type.like("endpoint_%"))
            .order_by(models.ActionLog.created_at.desc())
            .limit(50)
            .all()
        )

    with out_path.open("w", encoding="utf-8") as handle:
        if not logs:
            handle.write(json.dumps({"count": 0}) + "\n")
        for log in logs:
            record = {
                "audit_id": log.id,
                "time": log.created_at.isoformat(),
                "actor": log.user_id,
                "action": log.action_type,
                "target": {"type": log.target_type, "id": log.target_id},
                "parameters": log.parameters,
                "outcome": log.parameters.get("outcome"),
                "before_state": log.parameters.get("before_state"),
                "after_state": log.parameters.get("after_state"),
                "error_code": log.parameters.get("error_code"),
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
