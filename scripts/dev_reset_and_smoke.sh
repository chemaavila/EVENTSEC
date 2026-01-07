#!/usr/bin/env bash
set -euo pipefail

COMPOSE_CMD="${COMPOSE_CMD:-docker compose}"
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
WAIT_ATTEMPTS="${WAIT_ATTEMPTS:-60}"
WAIT_INTERVAL="${WAIT_INTERVAL:-2}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-Admin123!}"

echo "[smoke] resetting containers and volumes"
$COMPOSE_CMD down -v --remove-orphans
$COMPOSE_CMD up -d --build

echo "[smoke] waiting for backend /readyz"
attempt=1
until curl -fsS "${API_BASE_URL}/readyz" >/dev/null; do
  if [ "$attempt" -ge "$WAIT_ATTEMPTS" ]; then
    echo "[smoke] backend did not become ready after ${WAIT_ATTEMPTS} attempts" >&2
    $COMPOSE_CMD logs --tail=200 backend >&2
    exit 1
  fi
  echo "[smoke] backend not ready yet (${attempt}/${WAIT_ATTEMPTS})"
  attempt=$((attempt + 1))
  sleep "$WAIT_INTERVAL"
done

echo "[smoke] verifying core tables in Postgres"
$COMPOSE_CMD exec -T db psql -U eventsec -d eventsec \
  -c "SELECT to_regclass('public.alembic_version'), to_regclass('public.users');"

missing_tables="$(
  $COMPOSE_CMD exec -T db psql -U eventsec -d eventsec -tA \
    -c "SELECT (to_regclass('public.alembic_version') IS NULL) OR (to_regclass('public.users') IS NULL);"
)"
if [ "$missing_tables" != "f" ]; then
  echo "[smoke] missing required tables after migrations" >&2
  exit 1
fi

echo "[smoke] login smoke test"
login_response="$(
  curl -sS -w "\n%{http_code}" -X POST "${API_BASE_URL}/auth/login" \
    -H "Content-Type: application/json" \
    --data "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}"
)"
login_body="$(printf "%s" "$login_response" | sed '$d')"
login_code="$(printf "%s" "$login_response" | tail -n 1)"
if [ "$login_code" != "200" ]; then
  echo "[smoke] login failed with status ${login_code}" >&2
  echo "$login_body" >&2
  exit 1
fi

token="$(
  printf "%s" "$login_body" | python3 - <<'PY'
import json
import sys

payload = json.load(sys.stdin)
print(payload.get("access_token", ""))
PY
)"

if [ -z "$token" ]; then
  echo "[smoke] no access_token in login response" >&2
  exit 1
fi

me_code="$(
  curl -sS -o /dev/null -w "%{http_code}" "${API_BASE_URL}/me" \
    -H "Authorization: Bearer ${token}"
)"
if [ "$me_code" != "200" ]; then
  echo "[smoke] /me failed with status ${me_code}" >&2
  exit 1
fi

echo "[smoke] success"
