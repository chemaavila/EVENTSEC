#!/usr/bin/env bash
set -euo pipefail

VERCEL_APP_URL=${1:-${VERCEL_APP_URL:-}}
ADMIN_EMAIL=${ADMIN_EMAIL:-"admin@example.com"}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-"Admin123!"}

if [[ -z "${VERCEL_APP_URL}" ]]; then
  echo "Usage: $0 https://<vercel-app>" >&2
  echo "Or set VERCEL_APP_URL env var." >&2
  exit 1
fi

BASE_URL=${VERCEL_APP_URL%/}

printf "\n== /api/healthz ==\n"
curl -i "${BASE_URL}/api/healthz"

printf "\n== Preflight OPTIONS /api/auth/login ==\n"
curl -i -X OPTIONS "${BASE_URL}/api/auth/login" \
  -H "Origin: ${BASE_URL}" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type"

printf "\n== POST /api/auth/login ==\n"
curl -i -X POST "${BASE_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}"
