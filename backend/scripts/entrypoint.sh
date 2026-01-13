#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] PWD=$(pwd)"
echo "[entrypoint] RUN_MIGRATIONS=${RUN_MIGRATIONS:-<unset>}"
if [ -n "${DATABASE_URL:-}" ]; then
  echo "[entrypoint] DATABASE_URL=set"
else
  echo "[entrypoint] DATABASE_URL=unset"
fi
echo "[entrypoint] OPENSEARCH_REQUIRED=${OPENSEARCH_REQUIRED:-<unset>}"
if [ -n "${OPENSEARCH_URL:-}" ]; then
  echo "[entrypoint] OPENSEARCH_URL=set"
else
  echo "[entrypoint] OPENSEARCH_URL=unset"
fi

if [ -d "/opt/render/project/src/backend" ]; then
  cd /opt/render/project/src/backend
elif [ -d "backend" ]; then
  cd backend
fi

if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  alembic upgrade head
fi

echo "[entrypoint] OPENSEARCH_REQUIRED=${OPENSEARCH_REQUIRED:-<unset>}"
echo "[entrypoint] OPENSEARCH_URL=${OPENSEARCH_URL:-<unset>}"
echo "[entrypoint] ALEMBIC_BIN=$(command -v alembic || echo not-found)"

if [ -d "/opt/render/project/src/backend" ]; then
  cd /opt/render/project/src/backend
elif [ -d "backend" ]; then
  cd backend
fi

echo "[entrypoint] Now in $(pwd)"
ls -la

truthy() {
  case "${1:-}" in
    1|true|TRUE|yes|YES|on|ON) return 0 ;;
    *) return 1 ;;
  esac
}

should_migrate=false
if truthy "${RUN_MIGRATIONS:-}"; then
  should_migrate=true
fi

python - <<'PY'
import os
import sys
from sqlalchemy import create_engine, text

db = os.environ.get("DATABASE_URL")
if not db:
    print("[entrypoint] DATABASE_URL missing; cannot check schema.", file=sys.stderr)
    sys.exit(2)
engine = create_engine(db)
with engine.connect() as conn:
    try:
        conn.execute(text("select 1 from alembic_version limit 1"))
        print("[entrypoint] alembic_version table exists.")
        sys.exit(0)
    except Exception as exc:
        print("[entrypoint] alembic_version missing or unreadable -> migrations needed:", exc)
        sys.exit(1)
PY
schema_check_exit=$?

if [ "$schema_check_exit" -eq 1 ]; then
  should_migrate=true
elif [ "$schema_check_exit" -eq 2 ]; then
  echo "[entrypoint] Cannot verify DB schema because DATABASE_URL missing."
  exit 2
fi

if [ "$should_migrate" = true ]; then
  echo "[entrypoint] Running alembic upgrade head..."
  alembic upgrade head
  echo "[entrypoint] Alembic migrations finished."
else
  echo "[entrypoint] Skipping migrations."
fi

python - <<'PY'
import os
import sys
from sqlalchemy import create_engine, text

required = ["alembic_version", "users", "pending_events", "detection_rules"]
db = os.environ.get("DATABASE_URL")
engine = create_engine(db)
missing = []
with engine.connect() as conn:
    for table in required:
        try:
            conn.execute(text(f"select 1 from {table} limit 1"))
        except Exception:
            missing.append(table)
if missing:
    print("[entrypoint] ERROR: required tables still missing:", missing, file=sys.stderr)
    sys.exit(1)
print("[entrypoint] DB sanity check OK.")
PY

echo "[entrypoint] Starting app..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
