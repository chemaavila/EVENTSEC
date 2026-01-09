#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-Admin123!}"
AGENT_CMD="${AGENT_CMD:-python -m agent}"

token="$(
  curl -fsS "${API_BASE_URL}/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}" \
  | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])'
)"

auth_header="Authorization: Bearer ${token}"

indicator_exists="$(
  curl -fsS "${API_BASE_URL}/indicators" -H "${auth_header}" \
  | python -c 'import json,sys; data=json.load(sys.stdin); print(any(i.get("type")=="domain" and i.get("value")=="evil.test" and i.get("status")=="active" for i in data))'
)"

if [ "${indicator_exists}" != "True" ]; then
  curl -fsS "${API_BASE_URL}/indicators" \
    -H "${auth_header}" \
    -H "Content-Type: application/json" \
    -d '{"type":"domain","value":"evil.test","description":"Smoke test IOC","severity":"high","source":"smoke","tags":[],"status":"active"}' \
    >/dev/null
fi

EVENTSEC_AGENT_API_URL="${API_BASE_URL}" ${AGENT_CMD} --emit-test-url "http://evil.test/path"

echo "[smoke] waiting for IOC alert"
deadline=$((SECONDS + 30))
while [ $SECONDS -lt $deadline ]; do
  found="$(
    curl -fsS "${API_BASE_URL}/alerts" -H "${auth_header}" \
    | python -c 'import json,sys; data=json.load(sys.stdin); print(any(a.get("title")=="IOC Match: evil.test" for a in data))'
  )"
  if [ "${found}" == "True" ]; then
    echo "[smoke] IOC alert created"
    exit 0
  fi
  sleep 2
done

echo "[smoke] IOC alert not detected within timeout" >&2
exit 1
