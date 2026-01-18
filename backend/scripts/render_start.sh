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

if [[ -n "${DATABASE_URL:-}" ]]; then
  scheme="${DATABASE_URL%%:*}"
  normalized="$DATABASE_URL"
  if [[ "$DATABASE_URL" == postgres://* ]]; then
    normalized="postgresql+psycopg2://${DATABASE_URL#postgres://}"
  elif [[ "$DATABASE_URL" == postgresql://* && "$DATABASE_URL" != postgresql+* ]]; then
    normalized="postgresql+psycopg2://${DATABASE_URL#postgresql://}"
  fi
  export DATABASE_URL="$normalized"
  normalized_scheme="${DATABASE_URL%%:*}"
  if [[ "$scheme" != "$normalized_scheme" ]]; then
    log "Normalized DATABASE_URL scheme (${scheme} -> ${normalized_scheme})"
  fi
fi

if [[ "${EVENTSEC_DB_FORCE_PUBLIC:-}" == "1" ]]; then
  export PGOPTIONS="--search_path=public"
  log "EVENTSEC_DB_FORCE_PUBLIC=1; setting PGOPTIONS=--search_path=public"
fi

RUN_MIGRATIONS_ON_START="${RUN_MIGRATIONS_ON_START:-true}"
if [[ "${RUN_MIGRATIONS_ON_START}" == "true" ]]; then
  log "Running database migrations with advisory lock"
  python - <<'PY'
import os
import subprocess
import sys

from sqlalchemy import create_engine, text

DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(DATABASE_URL, future=True)
LOCK_KEY = 4242001

def run_alembic() -> None:
    try:
        subprocess.check_call(["alembic", "upgrade", "head"])
    except FileNotFoundError:
        subprocess.check_call([sys.executable, "-m", "alembic", "upgrade", "head"])

if engine.dialect.name != "postgresql":
    run_alembic()
    raise SystemExit(0)

with engine.connect() as conn:
    conn.execute(text("SELECT pg_advisory_lock(:key)"), {"key": LOCK_KEY})
    try:
        run_alembic()
    finally:
        conn.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": LOCK_KEY})
PY
else
  log "RUN_MIGRATIONS_ON_START=${RUN_MIGRATIONS_ON_START}; skipping migrations"
fi

log "Verifying critical tables exist"
python - <<'PY'
import os

from sqlalchemy import create_engine, text

from app.database import ALEMBIC_TABLE, DEFAULT_REQUIRED_TABLES

engine = create_engine(os.environ["DATABASE_URL"], future=True)
required = (*DEFAULT_REQUIRED_TABLES, ALEMBIC_TABLE)

with database.engine.connect() as conn:
    missing = database.get_missing_tables(conn)
    if missing:
        raise SystemExit(
            "Missing tables: "
            + ", ".join(missing)
            + ". Run `alembic upgrade head` or set RUN_MIGRATIONS_ON_START=true."
        )
PY

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
    print(f"[render-start][db-debug] {row}")
PY
fi

log "Starting EventSec backend on port ${PORT:-8000}"
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --proxy-headers \
  --forwarded-allow-ips="*"
