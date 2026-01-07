#!/bin/sh
set -euo pipefail

echo "[smoke] cleaning environment"
docker compose down -v --remove-orphans

echo "[smoke] starting db and opensearch"
docker compose up -d --build db opensearch

echo "[smoke] running migrations"
docker compose run --rm migrate

echo "[smoke] validating schema"
docker compose exec -T db psql -U eventsec -d eventsec -c "SELECT to_regclass('public.alembic_version');"
docker compose exec -T db psql -U eventsec -d eventsec -c "SELECT to_regclass('public.users');"
docker compose exec -T db psql -U eventsec -d eventsec -c "SELECT count(*) FROM public.alembic_version;"

echo "[smoke] starting backend and frontend"
docker compose up -d --build backend frontend

echo "[smoke] checking backend readiness"
curl -fsS http://localhost:8000/readyz
curl -fsS http://localhost:8000/healthz
