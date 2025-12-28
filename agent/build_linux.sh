#!/bin/bash
# Build script for Linux executable (uses local virtualenv)

set -euo pipefail

echo "Building EventSec Agent for Linux..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR=".build-venv"

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

pip install --upgrade pip
pip install -r build-requirements.txt
pip install -r requirements.txt
pip install pyinstaller

python scripts/generate_icons.py

pyinstaller --noconfirm eventsec-agent.spec

deactivate
rm -rf "$VENV_DIR"

DIST_DIR="$SCRIPT_DIR/dist"
CLI_BINARY="$DIST_DIR/eventsec-agent"

if [[ -f "$CLI_BINARY" ]]; then
  chmod +x "$CLI_BINARY"
  cp agent_config.json "$DIST_DIR/agent_config.json"
fi

echo ""
echo "Build complete! One-click binary is in: dist/eventsec-agent"
echo ""
