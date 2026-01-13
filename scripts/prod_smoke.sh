#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${1:-}
if [ -z "$BASE_URL" ]; then
  echo "Usage: $0 <base_url>" >&2
  exit 2
fi

BASE_URL=${BASE_URL%/}

curl -fsS "${BASE_URL}/healthz" >/dev/null
curl -fsS "${BASE_URL}/health/opensearch" >/dev/null

status_code=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health/db" || true)
if [ "$status_code" != "200" ] && [ "$status_code" != "404" ]; then
  echo "Unexpected /health/db status: ${status_code}" >&2
  exit 1
fi
