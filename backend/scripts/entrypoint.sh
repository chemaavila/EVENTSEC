#!/bin/sh
set -e

wait_attempts="${WAIT_ATTEMPTS:-30}"
wait_interval="${WAIT_INTERVAL:-2}"
max_attempts="${MIGRATION_ATTEMPTS:-10}"

wait_for_db() {
  attempt=1
  while [ "$attempt" -le "$wait_attempts" ]; do
    if python - <<'PY'
import os
from sqlalchemy import create_engine, text

url = os.environ.get("DATABASE_URL")
if not url:
    raise SystemExit(1)
engine = create_engine(url, pool_pre_ping=True, future=True)
with engine.connect() as conn:
    conn.execute(text("SELECT 1"))
PY
    then
      echo "Database is ready."
      return 0
    fi
    echo "Waiting for database (${attempt}/${wait_attempts})..."
    attempt=$((attempt + 1))
    sleep "$wait_interval"
  done
  echo "Database not ready after ${wait_attempts} attempts." >&2
  return 1
}

wait_for_opensearch() {
  attempt=1
  while [ "$attempt" -le "$wait_attempts" ]; do
    if python - <<'PY'
import os
import urllib.request

url = os.environ.get("OPENSEARCH_URL", "").rstrip("/")
if not url:
    raise SystemExit(1)
with urllib.request.urlopen(f"{url}/_cluster/health?timeout=2s", timeout=2) as resp:
    if resp.status >= 400:
        raise SystemExit(1)
PY
    then
      echo "OpenSearch is reachable."
      return 0
    fi
    echo "Waiting for OpenSearch (${attempt}/${wait_attempts})..."
    attempt=$((attempt + 1))
    sleep "$wait_interval"
  done
  echo "OpenSearch not reachable after ${wait_attempts} attempts." >&2
  return 1
}

wait_for_db
wait_for_opensearch

python /app/scripts/check_migrations.py

head_count=$(alembic heads | awk 'NF{print $1}' | wc -l | tr -d ' ')
if [ "$head_count" -gt 1 ]; then
  upgrade_target="heads"
else
  upgrade_target="head"
fi

attempt=1
until alembic upgrade "$upgrade_target"; do
  if [ "$attempt" -ge "$max_attempts" ]; then
    echo "Alembic migrations failed after ${attempt} attempts." >&2
    exit 1
  fi
  echo "Alembic upgrade failed. Retrying (${attempt}/${max_attempts})..." >&2
  attempt=$((attempt + 1))
  sleep 2
done

if [ "${EVENTSEC_SEED:-0}" = "1" ] || [ "${EVENTSEC_SEED:-0}" = "true" ]; then
  echo "Seeding core data..."
  python -m app.seed
fi

exec "$@"
