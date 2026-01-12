#!/usr/bin/env bash
set -euo pipefail
ROOT="/workspace/EVENTSEC"
EVID="${ROOT}/FAILURES_EVIDENCE"
TIMELINE="${EVID}/execution_timeline.txt"
log_cmd() { echo "[$(date -Is)] $1" >> "$TIMELINE"; }

log_cmd "cd backend && timeout 8s python -m app.server"
( cd "$ROOT/backend" && timeout 8s python -m app.server ) > "$EVID/backend.log" 2>&1 || true

log_cmd "curl -i http://localhost:8000/healthz"
{ echo "### curl -i http://localhost:8000/healthz"; curl -i http://localhost:8000/healthz; echo; } >> "$EVID/http_calls.log" 2>&1 || true
log_cmd "curl -i http://localhost:8000/readyz"
{ echo "### curl -i http://localhost:8000/readyz"; curl -i http://localhost:8000/readyz; echo; } >> "$EVID/http_calls.log" 2>&1 || true
log_cmd "curl -i http://localhost:8000/docs"
{ echo "### curl -i http://localhost:8000/docs"; curl -i http://localhost:8000/docs; echo; } >> "$EVID/http_calls.log" 2>&1 || true
