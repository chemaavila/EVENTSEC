#!/usr/bin/env bash
set -euo pipefail

COMPOSE_CMD=${COMPOSE_CMD:-"docker compose"}
RESET_STACK=${RESET_STACK:-1}

if [ "$RESET_STACK" -eq 1 ]; then
  $COMPOSE_CMD down -v --remove-orphans
fi

$COMPOSE_CMD up -d --build

echo "Waiting for backend readiness..."
for i in {1..60}; do
  if curl -fsS "http://localhost:8000/readyz" >/dev/null; then
    echo "Backend ready."
    break
  fi
  if [ "$i" -eq 60 ]; then
    echo "Backend failed to become ready." >&2
    exit 1
  fi
  sleep 2
done

echo "Checking frontend..."
for i in {1..30}; do
  if curl -fsS "http://localhost:5173/" >/dev/null; then
    echo "Frontend responding."
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "Frontend failed to respond." >&2
    exit 1
  fi
  sleep 2
done

echo "Checking email protection health..."
curl -fsS "http://localhost:8100/health" >/dev/null

echo "Checking OpenSearch cluster health..."
curl -fsS "http://localhost:9200/_cluster/health?timeout=2s" | head -n 2

echo "Checking DB tables..."
$COMPOSE_CMD exec -T db psql -U eventsec -d eventsec \
  -c "SELECT to_regclass('public.software_components') AS software_components, to_regclass('public.asset_vulnerabilities') AS asset_vulnerabilities;"
$COMPOSE_CMD exec -T db psql -U eventsec -d eventsec \
  -c "SELECT to_regclass('public.alembic_version') AS alembic_version;"

echo "Smoke checks complete."
