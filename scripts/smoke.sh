#!/usr/bin/env bash
set -euo pipefail

COMPOSE_CMD="${COMPOSE_CMD:-docker compose}"
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
WAIT_ATTEMPTS="${WAIT_ATTEMPTS:-60}"
WAIT_INTERVAL="${WAIT_INTERVAL:-2}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-Admin123!}"

log_failure() {
  echo "[smoke] failure diagnostics" >&2
  $COMPOSE_CMD ps >&2 || true
  $COMPOSE_CMD logs --tail=200 backend db opensearch vuln_worker >&2 || true
}

trap 'log_failure' ERR

echo "[smoke] cleaning environment"
$COMPOSE_CMD down -v --remove-orphans

echo "[smoke] starting stack"
$COMPOSE_CMD up -d --build

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

echo "[smoke] login cookie flow"
rm -f /tmp/eventsec_cookies.txt /tmp/eventsec_login.json
login_code=$(curl -sS -c /tmp/eventsec_cookies.txt -X POST "${API_BASE_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}" \
  -o /tmp/eventsec_login.json -w "%{http_code}")
if [ "$login_code" != "200" ]; then
  echo "[smoke] login failed with status ${login_code}" >&2
  cat /tmp/eventsec_login.json >&2 || true
  exit 1
fi

me_code=$(curl -sS -b /tmp/eventsec_cookies.txt "${API_BASE_URL}/me" -o /tmp/eventsec_me.json -w "%{http_code}")
if [ "$me_code" != "200" ]; then
  echo "[smoke] /me failed with status ${me_code}" >&2
  cat /tmp/eventsec_me.json >&2 || true
  exit 1
fi

echo "[smoke] success"
