#!/usr/bin/env bash
set -euo pipefail

log() { echo "[entrypoint] $*"; }

export PYTHONPATH="$PWD"

# Required secrets
if [[ -z "${JWT_SECRET:-}" && -z "${SECRET_KEY:-}" ]]; then
  log "ERROR: Missing JWT_SECRET or SECRET_KEY"
  exit 1
fi

# Required DB
if [[ -z "${DATABASE_URL:-}" ]]; then
  log "ERROR: DATABASE_URL is required"
  exit 1
fi

# Normalize DATABASE_URL for SQLAlchemy
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

if [[ "${EVENTSEC_DB_FORCE_PUBLIC:-}" == "1" ]]; then
  schema="${EVENTSEC_DB_SCHEMA:-public}"
  export PGOPTIONS="-c search_path=${schema}"
  log "EVENTSEC_DB_FORCE_PUBLIC=1; setting PGOPTIONS=-c search_path=${schema}"
fi

truthy() {
  case "$(echo "${1:-}" | tr '[:upper:]' '[:lower:]')" in
    1|true|t|yes|y|on) return 0 ;;
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

log "RUN_MIGRATIONS_ON_START=${RUN_MIGRATIONS_ON_START:-<unset>}"
log "PORT=${PORT:-10000}"

# IMPORTANT: Don't hardcode users/pending_events until verified
get_missing_tables() {
  python - <<'PY'
from app.database import engine, get_missing_tables

with engine.connect() as conn:
    missing = get_missing_tables(conn)
print(",".join(missing))
PY
}

dump_table_checks() {
  python - <<'PY'
import os
from sqlalchemy import inspect, text

from app.database import engine, required_tables_for_dialect

schema = os.environ.get("EVENTSEC_DB_SCHEMA", "public")

with engine.connect() as conn:
    row = conn.execute(
        text(
            "SELECT current_database() AS db, current_user AS user, "
            "current_schema() AS current_schema, "
            "current_setting('search_path') AS search_path"
        )
    ).mappings().first()
    print(f"[entrypoint][db-debug] identity={row}")

    tables = required_tables_for_dialect(conn.dialect.name)
    desired = []
    for table in tables:
        if "." in table:
            desired.append(table)
        else:
            desired.append(f\"{schema}.{table}\")

    inspector_tables = set(inspect(conn).get_table_names(schema=schema))
    print(f\"[entrypoint][db-debug] inspector[{schema}]={sorted(inspector_tables)}\")

    info_rows = conn.execute(
        text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = :schema ORDER BY table_name"
        ),
        {"schema": schema},
    ).fetchall()
    info_tables = {row[0] for row in info_rows}
    print(f\"[entrypoint][db-debug] information_schema[{schema}]={sorted(info_tables)}\")

    pg_rows = conn.execute(
        text(
            "SELECT c.relname "
            "FROM pg_catalog.pg_class c "
            "JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = :schema AND c.relkind IN ('r','p') "
            "ORDER BY c.relname"
        ),
        {"schema": schema},
    ).fetchall()
    pg_tables = {row[0] for row in pg_rows}
    print(f\"[entrypoint][db-debug] pg_catalog[{schema}]={sorted(pg_tables)}\")

    for table in desired:
        print(f\"[entrypoint][db-debug] expected={table}\")
PY
}

if [[ "$should_migrate" == true ]]; then
  log "Running alembic migrations"
  python - <<'PY'
import os
import subprocess

from sqlalchemy import create_engine, text

engine = create_engine(os.environ["DATABASE_URL"], future=True)
lock_id = int(os.environ.get("EVENTSEC_MIGRATION_LOCK_ID", "914067"))

if engine.dialect.name == "postgresql":
    with engine.connect() as conn:
        conn.execute(text("SELECT pg_advisory_lock(:lock_id)"), {"lock_id": lock_id})
        try:
            subprocess.run(["alembic", "upgrade", "head"], check=True)
        finally:
            conn.execute(text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": lock_id})
else:
    subprocess.run(["alembic", "upgrade", "head"], check=True)
PY
  log "Alembic migrations finished"
else
  log "Skipping migrations"
fi

missing_tables=""
had_missing=false
for attempt in 1 2 3; do
  missing_tables="$(get_missing_tables)"
  if [[ -z "$missing_tables" ]]; then
    break
  fi
  had_missing=true
  log "Missing tables detected (attempt ${attempt}/3): ${missing_tables}"
  sleep 2
done

if [[ -n "$missing_tables" ]]; then
  if [[ -n "${EVENTSEC_DB_DEBUG:-}" ]]; then
    dump_table_checks
  fi
  log "ERROR: missing tables after migrations: ${missing_tables}"
  exit 1
fi
if [[ "$had_missing" == true ]]; then
  log "WARNING: transient missing tables detected but resolved after retry"
fi

if [[ -n "${EVENTSEC_DB_DEBUG:-}" ]]; then
  log "DB debug enabled; printing connection identity"
  python - <<'PY'
import os
from sqlalchemy import create_engine, text
engine = create_engine(os.environ["DATABASE_URL"], future=True)
with engine.connect() as conn:
    row = conn.execute(text(
        "SELECT current_database() AS db, current_user AS user, "
        "inet_server_addr() AS server_addr, inet_server_port() AS server_port, "
        "current_setting('search_path') AS search_path"
    )).mappings().first()
    print(f"[entrypoint][db-debug] {row}")
PY
fi

log "Starting app"
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-10000}" \
  --proxy-headers \
  --forwarded-allow-ips="*"
