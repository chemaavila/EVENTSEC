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

db_debug() {
  if [ "${EVENTSEC_DB_DEBUG:-0}" = "1" ] || [ "${EVENTSEC_DB_DEBUG:-0}" = "true" ]; then
    python - <<'PY'
import os
import sys
from sqlalchemy import create_engine, text

label = os.environ.get("EVENTSEC_DB_DEBUG_LABEL", "db-debug")
url = os.environ.get("DATABASE_URL")
if not url:
    raise SystemExit("DATABASE_URL is not set")
engine = create_engine(url, pool_pre_ping=True, future=True)
with engine.connect() as conn:
    row = conn.execute(
        text(
            "SELECT current_database() AS db, current_user AS user, "
            "inet_server_addr() AS server_addr, "
            "inet_server_port() AS server_port, "
            "current_setting('search_path') AS search_path"
        )
    ).mappings().first()
    if row:
        print(
            f"[db-debug] {label} "
            f"db={row['db']} user={row['user']} "
            f"server_addr={row['server_addr']} server_port={row['server_port']} "
            f"search_path={row['search_path']}",
            file=sys.stderr,
        )
PY
  fi
}

verify_schema() {
  python - <<'PY'
import os
import sys
from sqlalchemy import create_engine, text

url = os.environ.get("DATABASE_URL")
if not url:
    raise SystemExit("DATABASE_URL is not set")
engine = create_engine(url, pool_pre_ping=True, future=True)
with engine.connect() as conn:
    checks = conn.execute(
        text(
            "SELECT "
            "to_regclass('public.alembic_version') IS NOT NULL AS has_alembic, "
            "to_regclass('public.users') IS NOT NULL AS has_users"
        )
    ).mappings().one()
    missing = []
    if not checks["has_alembic"]:
        missing.append("public.alembic_version")
    if not checks["has_users"]:
        missing.append("public.users")
    if missing:
        print(
            "[migrations] missing required tables after Alembic: "
            + ", ".join(missing),
            file=sys.stderr,
        )
        raise SystemExit(1)
PY
}

head_count=$(alembic heads | awk 'NF{print $1}' | wc -l | tr -d ' ')
if [ "$head_count" -gt 1 ]; then
  upgrade_target="heads"
else
  upgrade_target="head"
fi

attempt=1
while true; do
  echo "Running: alembic upgrade ${upgrade_target} (attempt ${attempt}/${max_attempts})"
  EVENTSEC_DB_DEBUG_LABEL="pre-migration" db_debug
  if alembic --raiseerr upgrade "$upgrade_target"; then
    break
  fi
  if [ "$attempt" -ge "$max_attempts" ]; then
    echo "Alembic migrations failed after ${attempt} attempts." >&2
    cat >&2 <<'EOF'
TROUBLESHOOTING:
- Likely causes: duplicate column from persisted volumes or partial migrations.
- Check migration state:
  docker compose exec backend alembic current
  docker compose exec backend alembic heads
- Dev reset (data loss): docker compose down -v --remove-orphans
EOF
    exit 1
  fi
  echo "Alembic upgrade failed. Retrying (${attempt}/${max_attempts})..." >&2
  attempt=$((attempt + 1))
  sleep 2
done

EVENTSEC_DB_DEBUG_LABEL="post-migration" db_debug
verify_schema

if [ "${EVENTSEC_SEED:-0}" = "1" ] || [ "${EVENTSEC_SEED:-0}" = "true" ]; then
  echo "Seeding core data..."
  EVENTSEC_DB_DEBUG_LABEL="pre-seed" db_debug
  python -m app.seed
fi

exec "$@"
