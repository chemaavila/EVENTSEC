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

truthy() {
  case "${1:-}" in
    1|true|TRUE|yes|YES|on|ON) return 0 ;;
    *) return 1 ;;
  esac
}

if truthy "${RUN_MIGRATIONS:-}"; then
  alembic upgrade head
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" \
  --proxy-headers --forwarded-allow-ips="*"
