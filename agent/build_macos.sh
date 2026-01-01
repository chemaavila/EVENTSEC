#!/bin/bash
# Build script for macOS executable (uses local virtualenv to avoid PEP 668)

set -euo pipefail

echo "Building EventSec Agent for macOS..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR=".build-venv"

PYTHON_BIN=""
if command -v python3.12 >/dev/null 2>&1; then
  PYTHON_BIN="python3.12"
elif command -v python3.11 >/dev/null 2>&1; then
  PYTHON_BIN="python3.11"
else
  echo "Error: Python 3.11 or 3.12 is required to build the agent (Pillow compatibility)." >&2
  exit 1
fi

"$PYTHON_BIN" -m venv "$VENV_DIR"
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
APP_BUNDLE="$DIST_DIR/eventsec-agent.app"
CLI_BINARY="$DIST_DIR/eventsec-agent"

if [[ -f "$CLI_BINARY" ]]; then
  chmod +x "$CLI_BINARY"
  cp agent_config.json "$DIST_DIR/agent_config.json"
fi

if [[ -d "$APP_BUNDLE/Contents/MacOS" ]]; then
  cp agent_config.json "$APP_BUNDLE/Contents/MacOS/agent_config.json"
fi

echo ""
echo "Build complete! Double-clickable bundle: dist/eventsec-agent.app"
echo ""
