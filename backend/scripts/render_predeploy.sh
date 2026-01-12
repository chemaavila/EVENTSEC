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

log "Verifying pending_events table exists"
python - <<'PY'
from sqlalchemy import text
from app.database import engine

with engine.connect() as conn:
    if conn.dialect.name != "postgresql":
        raise SystemExit(0)
    exists = conn.execute(
        text("SELECT to_regclass('public.pending_events')")
    ).scalar()
    if exists is None:
        raise SystemExit("pending_events table missing after migrations")
PY
