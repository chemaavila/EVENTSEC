#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${EVENTSEC_BASE_URL:-http://localhost:8000}
TENANT_ID=${EVENTSEC_TENANT_ID:-default}
ADMIN_EMAIL=${EVENTSEC_ADMIN_EMAIL:-admin@example.com}
ADMIN_PASSWORD=${EVENTSEC_ADMIN_PASSWORD:-Admin123!}

TOKEN=$(curl -sS -X POST "${BASE_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}" \
  | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')

curl -sS "${BASE_URL}/tenants/${TENANT_ID}/storage-policy" \
  -H "Authorization: Bearer ${TOKEN}" \
  | python -c 'import json,sys; json.load(sys.stdin); print("storage-policy ok")'

curl -sS -X PUT "${BASE_URL}/tenants/${TENANT_ID}/storage-policy" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"data_lake_enabled": true}' \
  | python -c 'import json,sys; json.load(sys.stdin); print("storage-policy updated")'

curl -sS "${BASE_URL}/tenants/${TENANT_ID}/usage" \
  -H "Authorization: Bearer ${TOKEN}" \
  | python -c 'import json,sys; json.load(sys.stdin); print("usage ok")'

curl -sS "${BASE_URL}/tenants/${TENANT_ID}/usage/export.csv" \
  -H "Authorization: Bearer ${TOKEN}" \
  | head -n 2
