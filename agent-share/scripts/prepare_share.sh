#!/usr/bin/env bash
set -euo pipefail

ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
DIST_DIR="$ROOT/../agent/dist"
BIN_DIR="$ROOT/bin"
CONFIG_SRC="$ROOT/agent_config.example.json"

if [[ ! -d "$DIST_DIR" ]]; then
  echo "[agent-share] No build artifacts found in $DIST_DIR"
  echo "Run one of the build scripts in ./agent before packaging."
  exit 1
fi

rm -rf "$BIN_DIR"
mkdir -p "$BIN_DIR"

shopt -s nullglob
copied=false
for file in "$DIST_DIR"/eventsec-agent*; do
  if [[ -d "$file" ]]; then
    cp -R "$file" "$BIN_DIR/"
  else
    cp "$file" "$BIN_DIR/"
  fi
  copied=true
done
shopt -u nullglob

if [[ "$copied" = false ]]; then
  echo "[agent-share] No eventsec-agent binaries found in $DIST_DIR"
  exit 1
fi

cp "$CONFIG_SRC" "$BIN_DIR/agent_config.json"
echo "[agent-share] Shareable bundle ready in $BIN_DIR"


