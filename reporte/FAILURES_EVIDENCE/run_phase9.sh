#!/usr/bin/env bash
set -euo pipefail
ROOT="/workspace/EVENTSEC"
EVID="${ROOT}/FAILURES_EVIDENCE"
TIMELINE="${EVID}/execution_timeline.txt"
log_cmd() { echo "[$(date -Is)] $1" >> "$TIMELINE"; }

log_cmd "pip-audit"
pip-audit > "$EVID/pip_audit.txt" 2>&1 || true
log_cmd "cd frontend && npm audit --audit-level=high"
( cd "$ROOT/frontend" && npm audit --audit-level=high ) > "$EVID/npm_audit.txt" 2>&1 || true

log_cmd "rg -n \"(AKIA|BEGIN PRIVATE KEY|api_key|secret|token)\" -S ."
rg -n "(AKIA|BEGIN PRIVATE KEY|api_key|secret|token)" -S "$ROOT" > "$EVID/secrets_scan.txt" 2>&1 || true
