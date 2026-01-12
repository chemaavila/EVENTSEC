#!/usr/bin/env bash
set -euo pipefail
ROOT="/workspace/EVENTSEC"
EVID="${ROOT}/FAILURES_EVIDENCE"
TIMELINE="${EVID}/execution_timeline.txt"
log_cmd() {
  local cmd="$1"
  echo "[$(date -Is)] $cmd" >> "$TIMELINE"
}
run_to_file() {
  local cmd="$1"; local outfile="$2"
  log_cmd "$cmd"
  bash -lc "$cmd" > "$outfile" 2>&1 || true
}

log_cmd "git clone https://github.com/chemaavila/EVENTSEC.git /workspace/EVENTSEC_TMP"

run_to_file "tree -a -L 5" "${EVID}/tree_L5.txt"
run_to_file "ls -la" "${EVID}/ls_la_root.txt"
run_to_file "rg -n \"os\\.environ|getenv|process\\.env|ENV\\[\" -S ." "${EVID}/env_usages.txt"

# Environment versions
log_cmd "uname -a"
uname -a >> "${EVID}/environment_versions.txt" 2>&1 || true
log_cmd "docker version"
docker version >> "${EVID}/environment_versions.txt" 2>&1 || true
log_cmd "docker compose version"
docker compose version >> "${EVID}/environment_versions.txt" 2>&1 || true
log_cmd "node -v"
node -v >> "${EVID}/environment_versions.txt" 2>&1 || true
log_cmd "npm -v"
npm -v >> "${EVID}/environment_versions.txt" 2>&1 || true
log_cmd "python3 --version"
python3 --version >> "${EVID}/environment_versions.txt" 2>&1 || true
log_cmd "pip --version"
pip --version >> "${EVID}/environment_versions.txt" 2>&1 || true

run_to_file "docker info" "${EVID}/docker_info.txt"
