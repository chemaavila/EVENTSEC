#!/usr/bin/env bash
set -euo pipefail

log() {
  echo "[render-predeploy] $*"
}

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "[render-predeploy] Missing required env: $name" >&2
    exit 1
  fi
}

export PYTHONPATH="$PWD"

require_env "DATABASE_URL"

log "Running Alembic migrations"
alembic upgrade head

log "Verifying critical tables exist"
python - <<'PY'
from sqlalchemy import text
from app.database import engine

with engine.connect() as conn:
    if conn.dialect.name != "postgresql":
        raise SystemExit(0)
    missing = []
    for table in ("pending_events", "detection_rules"):
        exists = conn.execute(
            text(f"SELECT to_regclass('public.{table}')")
        ).scalar()
        if exists is None:
            missing.append(table)
    if missing:
        raise SystemExit(f"Missing tables after migrations: {', '.join(missing)}")
PY
