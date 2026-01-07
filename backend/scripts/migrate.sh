#!/bin/sh
set -euo pipefail

if [ -z "${DATABASE_URL:-}" ]; then
  echo "[migrate] DATABASE_URL is not set" >&2
  exit 1
fi

timeout_seconds="${MIGRATE_DB_TIMEOUT_SECONDS:-60}"
elapsed=0
sleep_interval=2

echo "[migrate] waiting for database readiness"
while ! pg_isready -d "$DATABASE_URL" >/dev/null 2>&1; do
  if [ "$elapsed" -ge "$timeout_seconds" ]; then
    echo "[migrate] database did not become ready within ${timeout_seconds}s" >&2
    exit 1
  fi
  elapsed=$((elapsed + sleep_interval))
  sleep "$sleep_interval"
done

echo "[migrate] assert alembic directory exists"
ls -la /app/alembic
ls -la /app/alembic/versions | head -n 50

echo "[migrate] alembic heads"
alembic heads -v

head_count=$(alembic heads | awk 'NF{print $1}' | wc -l | tr -d ' ')
if [ "$head_count" -gt 1 ]; then
  upgrade_target="heads"
else
  upgrade_target="head"
fi

echo "[migrate] running alembic upgrade ${upgrade_target}"
alembic --raiseerr upgrade "$upgrade_target"

echo "[migrate] verifying required tables"
EVENTSEC_MIGRATION_VERIFY=1 python /app/scripts/check_migrations.py
