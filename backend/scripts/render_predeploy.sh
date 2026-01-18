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

if [[ -n "${EVENTSEC_DB_DEBUG:-}" ]]; then
  log "DB debug enabled; printing connection identity"
  python - <<'PY'
import os
from sqlalchemy import create_engine, text

engine = create_engine(os.environ["DATABASE_URL"], future=True)
with engine.connect() as conn:
    row = conn.execute(
        text(
            "SELECT current_database() AS db, current_user AS user, "
            "inet_server_addr() AS server_addr, inet_server_port() AS server_port, "
            "current_setting('search_path') AS search_path"
        )
    ).mappings().first()
    print(f"[render-predeploy][db-debug] {row}")
PY
fi

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
