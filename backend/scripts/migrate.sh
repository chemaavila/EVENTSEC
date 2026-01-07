#!/bin/sh
set -euo pipefail

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
