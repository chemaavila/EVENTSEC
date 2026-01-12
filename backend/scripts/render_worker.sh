#!/usr/bin/env bash
set -euo pipefail

log() {
  echo "[render-worker] $*"
}

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "[render-worker] Missing required env: $name" >&2
    exit 1
  fi
}

export PYTHONPATH="$PWD"

require_env "DATABASE_URL"
export VULN_INTEL_WORKER_ROLE="${VULN_INTEL_WORKER_ROLE:-worker}"

log "Starting vuln intel worker role=${VULN_INTEL_WORKER_ROLE}"
exec python -m app.worker
