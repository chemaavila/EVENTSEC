#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(pwd)
ARTIFACTS_DIR="${ROOT_DIR}/artifacts"
LOG_DIR="${ARTIFACTS_DIR}/agent_smoke_logs"
OUTPUT_FILE="${ARTIFACTS_DIR}/mock_collector_received.jsonl"
PORT_FILE=$(mktemp)

cleanup() {
  if [ -n "${MOCK_PID:-}" ]; then
    kill "${MOCK_PID}" >/dev/null 2>&1 || true
  fi
  rm -f "${PORT_FILE}"
}
trap cleanup EXIT

mkdir -p "${LOG_DIR}"
rm -f "${OUTPUT_FILE}"

export PYTHONPATH="${ROOT_DIR}"

MOCK_COLLECTOR_OUT="${OUTPUT_FILE}" \
MOCK_COLLECTOR_PORT=0 \
MOCK_COLLECTOR_PORT_FILE="${PORT_FILE}" \
python agent/tests/mock_collector.py &
MOCK_PID=$!

attempt=1
while [ ! -s "${PORT_FILE}" ]; do
  if [ "$attempt" -gt 25 ]; then
    echo "[agent-smoke] mock collector did not start" >&2
    exit 1
  fi
  attempt=$((attempt + 1))
  sleep 0.2
done

MOCK_PORT=$(cat "${PORT_FILE}")

EVENTSEC_AGENT_API_URL="http://127.0.0.1:${MOCK_PORT}" \
EVENTSEC_AGENT_AGENT_ID=1 \
EVENTSEC_AGENT_AGENT_API_KEY="smoke-key" \
python -m agent --run-once \
  --log-file "${LOG_DIR}/agent.log" \
  --status-file "${LOG_DIR}/status.json"

if [ ! -s "${OUTPUT_FILE}" ]; then
  echo "[agent-smoke] no payloads captured" >&2
  exit 1
fi

if ! grep -q '"event_type": "agent_status"' "${OUTPUT_FILE}"; then
  echo "[agent-smoke] agent_status event not found" >&2
  exit 1
fi

echo "[agent-smoke] success"
