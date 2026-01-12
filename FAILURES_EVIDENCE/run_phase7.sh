#!/usr/bin/env bash
set -euo pipefail
ROOT="/workspace/EVENTSEC"
EVID="${ROOT}/FAILURES_EVIDENCE"
TIMELINE="${EVID}/execution_timeline.txt"
log_cmd() { echo "[$(date -Is)] $1" >> "$TIMELINE"; }

log_cmd "cd frontend && npm install"
( cd "$ROOT/frontend" && npm install ) > "$EVID/frontend_build_run.log" 2>&1 || true
log_cmd "cd frontend && npm run build"
( cd "$ROOT/frontend" && npm run build ) >> "$EVID/frontend_build_run.log" 2>&1 || true
