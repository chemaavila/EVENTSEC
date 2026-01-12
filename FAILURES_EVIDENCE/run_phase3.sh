#!/usr/bin/env bash
set -euo pipefail
ROOT="/workspace/EVENTSEC"
EVID="${ROOT}/FAILURES_EVIDENCE"
TIMELINE="${EVID}/execution_timeline.txt"
log_cmd() { echo "[$(date -Is)] $1" >> "$TIMELINE"; }
run_to_file() { local cmd="$1"; local outfile="$2"; log_cmd "$cmd"; bash -lc "$cmd" > "$outfile" 2>&1 || true; }

run_to_file "psql --version" "${EVID}/psql_version.txt"
run_to_file "psql -c '\\conninfo'" "${EVID}/db_conninfo.txt"
run_to_file "psql -c '\\dt *.*'" "${EVID}/db_schema_dump.txt"

log_cmd "cd backend && alembic current"
( cd "$ROOT/backend" && alembic current ) > "$EVID/migrations_output.txt" 2>&1 || true
log_cmd "cd backend && alembic history"
( cd "$ROOT/backend" && alembic history ) >> "$EVID/migrations_output.txt" 2>&1 || true
log_cmd "cd backend && alembic upgrade head"
( cd "$ROOT/backend" && alembic upgrade head ) >> "$EVID/migrations_output.txt" 2>&1 || true
