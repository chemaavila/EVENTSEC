#!/usr/bin/env bash
set -euo pipefail
echo "[render-start] Delegating Render start to scripts/entrypoint.sh (PWD=$(pwd))"
exec bash scripts/entrypoint.sh

