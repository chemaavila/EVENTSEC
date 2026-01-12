#!/usr/bin/env bash
set -euo pipefail
ROOT="/workspace/EVENTSEC"
EVID="${ROOT}/FAILURES_EVIDENCE"
TIMELINE="${EVID}/execution_timeline.txt"
log_cmd() { echo "[$(date -Is)] $1" >> "$TIMELINE"; }

log_cmd "pytest -q backend/tests"
pytest -q "$ROOT/backend/tests" > "$EVID/tests_and_linters.txt" 2>&1 || true
log_cmd "cd frontend && npm test"
( cd "$ROOT/frontend" && npm test ) >> "$EVID/tests_and_linters.txt" 2>&1 || true
