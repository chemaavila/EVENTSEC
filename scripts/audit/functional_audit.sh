#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
API_BASE="${EVENTSEC_API_BASE:-http://localhost:8000}"
FRONTEND_BASE="${EVENTSEC_FRONTEND_BASE:-http://localhost:5173}"
COOKIE_JAR="${EVENTSEC_COOKIE_JAR:-/tmp/eventsec_cookies.txt}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found; install Docker to run the audit harness." >&2
  exit 1
fi

cleanup() {
  rm -f "${COOKIE_JAR}"
}
trap cleanup EXIT

echo "[audit] bringing down services"
docker compose -f "${COMPOSE_FILE}" down -v --remove-orphans

echo "[audit] starting services"
docker compose -f "${COMPOSE_FILE}" up -d --build

echo "[audit] services"
docker compose -f "${COMPOSE_FILE}" ps

echo "[audit] health checks"
curl -sf "${API_BASE}/healthz" >/dev/null
curl -sf "${API_BASE}/readyz" >/dev/null
curl -sf "${API_BASE}/openapi.json" | head -n 5 >/dev/null
curl -sfI "${FRONTEND_BASE}/" >/dev/null

if [[ -n "${EVENTSEC_EMAIL:-}" && -n "${EVENTSEC_PASSWORD:-}" ]]; then
  echo "[audit] login"
  curl -sf -X POST "${API_BASE}/auth/login" \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"${EVENTSEC_EMAIL}\",\"password\":\"${EVENTSEC_PASSWORD}\"}" \
    -c "${COOKIE_JAR}" >/dev/null

  echo "[audit] authenticated alerts list"
  curl -sf "${API_BASE}/alerts" -b "${COOKIE_JAR}" >/dev/null
else
  echo "[audit] skipping login (set EVENTSEC_EMAIL and EVENTSEC_PASSWORD)"
fi

echo "[audit] done"
