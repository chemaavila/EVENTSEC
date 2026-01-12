#!/usr/bin/env bash
set -euo pipefail
BASE_URL=${EVENTSEC_API_BASE:-http://localhost:8000}
TOKEN=${EVENTSEC_INGEST_TOKEN:-${EVENTSEC_AGENT_TOKEN:-eventsec-dev-token}}
FILE=${1:-}
if [[ -z "$FILE" ]]; then
  echo "Usage: $0 <payload.json>" >&2
  exit 1
fi

curl -sS -w "\nHTTP_STATUS=%{http_code}\n" \
  -H "Content-Type: application/json" \
  -H "X-Agent-Token: ${TOKEN}" \
  --data-binary "@${FILE}" \
  "${BASE_URL}/events"
