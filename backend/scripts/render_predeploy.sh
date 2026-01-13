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
from app import database

with database.engine.connect() as conn:
    missing = database.get_missing_tables(
        conn, tables=("users", "pending_events", "detection_rules", database.ALEMBIC_TABLE)
    )
    if missing:
        raise SystemExit(f"Missing tables after migrations: {', '.join(missing)}")
PY
