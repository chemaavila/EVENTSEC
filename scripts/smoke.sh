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

echo "[smoke] checking /me returns non-500 when unauthenticated"
me_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/me)
if [ "$me_status" -ge 500 ]; then
  echo "[smoke] /me returned ${me_status} without auth" >&2
  exit 1
fi

echo "[smoke] attempting login and /me with session"
cookie_jar="$(mktemp)"
curl -fsS -c "$cookie_jar" -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"Admin123!"}' \
  http://localhost:8000/auth/login >/dev/null
curl -fsS -b "$cookie_jar" http://localhost:8000/me >/dev/null
rm -f "$cookie_jar"
