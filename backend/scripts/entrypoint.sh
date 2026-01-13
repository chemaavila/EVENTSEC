#!/usr/bin/env bash
set -euo pipefail

if [ -d /opt/render/project/src/backend ]; then
  cd /opt/render/project/src/backend
elif [ -d backend ]; then
  cd backend
else
  echo "[entrypoint] Staying in $(pwd)"
fi

if [ ! -f alembic.ini ]; then
  echo "[entrypoint] ERROR: alembic.ini not found in $(pwd)." >&2
  exit 1
fi

if [ -z "${DATABASE_URL:-}" ]; then
  echo "[entrypoint] ERROR: DATABASE_URL is not set." >&2
  exit 1
fi

run_migrations="${RUN_MIGRATIONS:-false}"
run_migrations="${run_migrations,,}"
if [ "${run_migrations}" = "true" ]; then
  echo "[entrypoint] Running migrations..."
  alembic upgrade head
  alembic current || true
fi

echo "[entrypoint] Starting app..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
