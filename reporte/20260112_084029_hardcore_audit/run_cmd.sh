#!/usr/bin/env bash
set -euo pipefail
LOG_FILE="${LOG_FILE:-./reporte/20260112_084029_hardcore_audit/FAILURES_EVIDENCE/command_log.csv}"
run_cmd() {
  local out_file="$1"
  shift
  local cmd=("$@")
  local start_ts end_ts duration exit_code
  start_ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  local start_ns
  start_ns=$(date +%s%3N)
  {
    "${cmd[@]}"
  } >"$out_file" 2>&1
  exit_code=$?
  end_ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  local end_ns
  end_ns=$(date +%s%3N)
  duration=$((end_ns - start_ns))
  printf '%s,%s,%s,"%s",%s\n' "$start_ts" "$duration" "$exit_code" "${cmd[*]}" "$out_file" >> "$LOG_FILE"
  return $exit_code
}
