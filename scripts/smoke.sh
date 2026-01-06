#!/usr/bin/env bash
set -euo pipefail

COMPOSE_CMD=${COMPOSE_CMD:-"docker compose"}

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

echo "Checking backend OpenAPI..."
curl -fsS "http://localhost:8000/openapi.json" | head -n 5

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

echo "Smoke checks complete."
