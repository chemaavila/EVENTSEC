#!/usr/bin/env bash
set -euo pipefail

if [ -d "/opt/render/project/src/backend" ]; then
  cd /opt/render/project/src/backend
elif [ -d "backend" ]; then
  cd backend
fi

if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  alembic upgrade head
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
