#!/usr/bin/env bash
set -euo pipefail

RENDER_URL=${1:-${RENDER_URL:-}}

if [[ -z "${RENDER_URL}" ]]; then
  echo "Usage: $0 https://<render-backend>" >&2
  echo "Or set RENDER_URL env var." >&2
  exit 1
fi

BASE_URL=${RENDER_URL%/}

printf "\n== Render DB health ==\n"
headers=$(curl -s -D - -o /tmp/render_db_body.json "${BASE_URL}/health/db")
status_code=$(printf "%s" "${headers}" | awk 'NR==1 {print $2}')

if [[ "${status_code}" == "200" ]]; then
  echo "PASS: /health/db returned 200"
  cat /tmp/render_db_body.json
  exit 0
fi

echo "FAIL: /health/db returned ${status_code}"
cat /tmp/render_db_body.json
exit 1
