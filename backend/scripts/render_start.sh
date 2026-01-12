#!/usr/bin/env bash
set -euo pipefail

log() {
  echo "[render-start] $*"
}

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "[render-start] Missing required env: $name" >&2
    exit 1
  fi
}

export PYTHONPATH="$PWD"

require_env "DATABASE_URL"
if [[ -z "${JWT_SECRET:-}" && -z "${SECRET_KEY:-}" ]]; then
  echo "[render-start] Missing JWT_SECRET or SECRET_KEY" >&2
  exit 1
fi

RUN_MIGRATIONS="${RUN_MIGRATIONS:-true}"
if [[ "${RUN_MIGRATIONS}" == "true" ]]; then
  log "Running database migrations (alembic upgrade head)"
  if command -v alembic >/dev/null 2>&1; then
    alembic upgrade head
  else
    python -m alembic upgrade head
  fi
else
  log "RUN_MIGRATIONS=${RUN_MIGRATIONS}; skipping migrations"
fi

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
        raise SystemExit(
            "Missing tables: "
            + ", ".join(missing)
            + ". Run `alembic upgrade head` or set RUN_MIGRATIONS=true."
        )
PY

log "Starting EventSec backend on port ${PORT:-8000}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
