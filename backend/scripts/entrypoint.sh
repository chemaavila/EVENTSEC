#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] PWD=$(pwd)"
echo "[entrypoint] RUN_MIGRATIONS=${RUN_MIGRATIONS:-<unset>}"
if [ -n "${DATABASE_URL:-}" ]; then
  echo "[entrypoint] DATABASE_URL=set"
else
  echo "[entrypoint] DATABASE_URL=unset"
fi
echo "[entrypoint] ALEMBIC_BIN=$(command -v alembic || echo not-found)"

cd /opt/render/project/src/backend || cd backend || pwd

truthy() {
  case "${1:-}" in
    1|true|TRUE|yes|YES|on|ON) return 0 ;;
    *) return 1 ;;
  esac
}

if truthy "${RUN_MIGRATIONS:-}"; then
  echo "[entrypoint] Running migrations..."
  alembic upgrade head
  echo "[entrypoint] Migrations done."
fi

if [ -n "${DATABASE_URL:-}" ]; then
  python - <<'PY'
import os
from sqlalchemy import create_engine, text

db = os.environ.get("DATABASE_URL")
engine = create_engine(db)
with engine.connect() as conn:
    conn.execute(text("select 1 from public.alembic_version limit 1"))
print("[entrypoint] public.alembic_version check OK.")
PY
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-10000}"
