#!/usr/bin/env bash
set -euo pipefail

log() {
  echo "[entrypoint] $*"
}

if [[ "$(basename "${PWD}")" == "backend" ]]; then
  :
elif [[ -d "/opt/render/project/src/backend" ]]; then
  cd /opt/render/project/src/backend
elif [[ -d "./backend" ]]; then
  cd ./backend
else
  log "ERROR: unable to locate backend directory from $(pwd)"
  exit 1
fi

export PYTHONPATH="$PWD"

if [[ -z "${JWT_SECRET:-}" && -z "${SECRET_KEY:-}" ]]; then
  log "ERROR: Missing JWT_SECRET or SECRET_KEY"
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
  log "DATABASE_URL set (scheme=${normalized_scheme})"
  if [[ "$scheme" != "$normalized_scheme" ]]; then
    log "Normalized DATABASE_URL scheme (${scheme} -> ${normalized_scheme})"
  fi
else
  log "DATABASE_URL unset"
fi

if [[ "${EVENTSEC_DB_FORCE_PUBLIC:-}" == "1" ]]; then
  export PGOPTIONS="--search_path=public"
  log "EVENTSEC_DB_FORCE_PUBLIC=1; setting PGOPTIONS=--search_path=public"
fi

log "RUN_MIGRATIONS=${RUN_MIGRATIONS:-<unset>}"
log "RUN_MIGRATIONS_ON_START=${RUN_MIGRATIONS_ON_START:-<unset>}"
log "PORT=${PORT:-10000}"

if [[ -z "${DATABASE_URL:-}" ]]; then
  log "ERROR: DATABASE_URL is required for startup"
  exit 1
fi

max_attempts=30
attempt=1
while [[ $attempt -le $max_attempts ]]; do
  if python - <<'PY'
import os
from sqlalchemy import create_engine, text

engine = create_engine(os.environ["DATABASE_URL"], future=True)
with engine.connect() as conn:
    conn.execute(text("SELECT 1"))
PY
  then
    log "Database connection ready."
    break
  fi
  sleep_seconds=$((2 ** (attempt - 1)))
  if [[ $sleep_seconds -gt 5 ]]; then
    sleep_seconds=5
  fi
  log "Database not ready (attempt ${attempt}/${max_attempts}); retrying in ${sleep_seconds}s"
  sleep "$sleep_seconds"
  attempt=$((attempt + 1))
  if [[ $attempt -gt $max_attempts ]]; then
    log "ERROR: database is not reachable after ${max_attempts} attempts"
    exit 1
  fi
done

truthy() {
  case "${1:-}" in
    1|true|TRUE|yes|YES|on|ON) return 0 ;;
    *) return 1 ;;
  esac
}

should_migrate=false
if truthy "${RUN_MIGRATIONS_ON_START:-}"; then
  should_migrate=true
elif truthy "${RUN_MIGRATIONS:-}"; then
  should_migrate=true
elif [[ -z "${RUN_MIGRATIONS_ON_START:-}" && -z "${RUN_MIGRATIONS:-}" ]]; then
  should_migrate=true
fi

get_missing_tables() {
  python - <<'PY'
import os
from sqlalchemy import create_engine

from app import database

engine = create_engine(os.environ["DATABASE_URL"], future=True)
with engine.connect() as conn:
    missing = database.get_missing_tables(conn)
print(",".join(missing))
PY
}

missing_tables="$(get_missing_tables 2>/dev/null || true)"

if [[ -n "$missing_tables" ]]; then
  log "Detected missing tables: ${missing_tables}"
  if [[ "$should_migrate" != true ]]; then
    export EVENTSEC_DB_NOT_MIGRATED=1
    log "Migrations disabled and schema missing; continuing with EVENTSEC_DB_NOT_MIGRATED=1"
  fi
else
  log "Required tables appear present."
fi

if [[ "$should_migrate" == true ]]; then
  log "Running alembic upgrade head"
  if ! alembic upgrade head; then
    log "ERROR: alembic upgrade failed"
    exit 1
  fi
  log "Alembic migrations finished"
  post_missing_tables="$(get_missing_tables 2>/dev/null || true)"
  if [[ -n "$post_missing_tables" ]]; then
    log "ERROR: missing tables after migrations: ${post_missing_tables}"
    exit 1
  fi
else
  log "Skipping migrations"
fi

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
    print(f"[entrypoint][db-debug] {row}")
PY
fi

log "Starting app"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-10000}"
