#!/usr/bin/env bash
set -euo pipefail
ROOT="/workspace/EVENTSEC"
EVID="${ROOT}/FAILURES_EVIDENCE"
TIMELINE="${EVID}/execution_timeline.txt"
log_cmd() { echo "[$(date -Is)] $1" >> "$TIMELINE"; }
run_to_file() { local cmd="$1"; local outfile="$2"; log_cmd "$cmd"; bash -lc "$cmd" > "$outfile" 2>&1 || true; }

run_to_file "docker compose config" "${EVID}/compose.rendered.yml"
log_cmd "docker compose up -d --build"
bash -lc "docker compose up -d --build" 2>&1 | tee "${EVID}/compose_up_build.log" || true
run_to_file "docker compose ps" "${EVID}/compose_ps.txt"
run_to_file "docker compose logs --no-color --timestamps" "${EVID}/compose_all_logs.txt"
