#!/usr/bin/env bash
set -euo pipefail

COMPOSE_CMD="${COMPOSE_CMD:-docker compose}"
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
WAIT_ATTEMPTS="${WAIT_ATTEMPTS:-60}"
WAIT_INTERVAL="${WAIT_INTERVAL:-2}"

log_failure() {
  echo "[smoke] failure diagnostics" >&2
  $COMPOSE_CMD ps >&2 || true
  $COMPOSE_CMD logs --tail=200 backend db opensearch vuln_worker >&2 || true
}

trap 'log_failure' ERR

echo "[smoke] waiting for backend readiness"
attempt=1
until curl -fsS "${API_BASE_URL}/readyz" >/dev/null; do
  if [ "$attempt" -ge "$WAIT_ATTEMPTS" ]; then
    echo "[smoke] backend did not become ready after ${WAIT_ATTEMPTS} attempts" >&2
    exit 1
  fi
  echo "[smoke] backend not ready yet (${attempt}/${WAIT_ATTEMPTS})"
  attempt=$((attempt + 1))
  sleep "$WAIT_INTERVAL"
done

curl -fsS "${API_BASE_URL}/healthz" >/dev/null

echo "[smoke] validating schema"
$COMPOSE_CMD exec -T db psql -U eventsec -d eventsec -c "SELECT to_regclass('public.alembic_version');"
$COMPOSE_CMD exec -T db psql -U eventsec -d eventsec -c "SELECT to_regclass('public.users');"
$COMPOSE_CMD exec -T db psql -U eventsec -d eventsec -c "SELECT count(*) FROM public.alembic_version;"

echo "[smoke] checking worker status"
if ! $COMPOSE_CMD ps --status running --services | grep -q "^vuln_worker$"; then
  echo "[smoke] vuln_worker is not running" >&2
  $COMPOSE_CMD logs --tail=200 vuln_worker >&2 || true
  exit 1
fi

echo "[smoke] success"
