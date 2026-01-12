#!/usr/bin/env bash
set -euo pipefail

VERCEL_DOMAIN=${1:-"https://eventsec-ihae-cgz9ykuwu-chemas-projects-a83da5fd.vercel.app"}

printf "== Render healthz ==\n"
curl -i https://eventsec-backend.onrender.com/healthz

printf "\n== Vercel proxy healthz (%s) ==\n" "$VERCEL_DOMAIN"
curl -i "${VERCEL_DOMAIN}/api/healthz"

printf "\n== Render preflight (OPTIONS /auth/login) ==\n"
curl -i -X OPTIONS https://eventsec-backend.onrender.com/auth/login \
  -H "Origin: https://eventsec-ihae-cgz9ykuwu-chemas-projects-a83da5fd.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type,x-request-id,authorization"

printf "\n== Render login POST (expect 200/401/422, not CORS error) ==\n"
curl -i -X POST https://eventsec-backend.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"1234"}'
