#!/bin/sh
set -e

max_attempts="${MIGRATION_ATTEMPTS:-10}"
attempt=1

until alembic upgrade head; do
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
