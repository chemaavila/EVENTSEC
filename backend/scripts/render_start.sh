#!/usr/bin/env bash
set -euo pipefail

log() { echo "[render-start] $*"; }

log "Delegating Render start to scripts/entrypoint.sh (PWD=$(pwd))"
exec bash scripts/entrypoint.sh
