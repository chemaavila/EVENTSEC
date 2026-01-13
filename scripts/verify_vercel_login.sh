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

pass() { printf "PASS: %s\n" "$1"; }
fail() { printf "FAIL: %s\n" "$1"; exit_code=1; }

exit_code=0

printf "\n== /api/healthz ==\n"
health_code=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/healthz")
if [[ "${health_code}" == "200" ]]; then
  pass "/api/healthz returned 200"
else
  fail "/api/healthz returned ${health_code} (expected 200)"
fi

printf "\n== Preflight OPTIONS /api/auth/login ==\n"
preflight_headers=$(curl -s -D - -o /dev/null -X OPTIONS "${BASE_URL}/api/auth/login" \
  -H "Origin: ${BASE_URL}" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type")
preflight_code=$(printf "%s" "${preflight_headers}" | awk 'NR==1 {print $2}')
if [[ "${preflight_code}" == "200" || "${preflight_code}" == "204" ]]; then
  if printf "%s" "${preflight_headers}" | rg -i "access-control-allow-origin: ${BASE_URL}"; then
    pass "OPTIONS /api/auth/login returned ${preflight_code} with CORS headers"
  else
    fail "OPTIONS /api/auth/login missing Access-Control-Allow-Origin for ${BASE_URL}"
  fi
else
  fail "OPTIONS /api/auth/login returned ${preflight_code} (expected 200/204)"
fi

printf "\n== POST /api/auth/login ==\n"
login_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}")
case "${login_code}" in
  200|401|422)
    pass "POST /api/auth/login returned ${login_code}"
    ;;
  *)
    fail "POST /api/auth/login returned ${login_code} (expected 200/401/422)"
    ;;
esac

exit "${exit_code}"
