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

log "Running database migrations (alembic upgrade head)"
if command -v alembic >/dev/null 2>&1; then
  alembic upgrade head
else
  python -m alembic upgrade head
fi

log "Starting EventSec backend on port ${PORT:-8000}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
