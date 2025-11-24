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
pip install -r requirements.txt
pip install pyinstaller

pyinstaller --onefile --name eventsec-agent --console --clean agent.py

deactivate
rm -rf "$VENV_DIR"

chmod +x dist/eventsec-agent
cp agent_config.json dist/agent_config.json

echo ""
echo "Build complete! Executable is in the 'dist' folder: dist/eventsec-agent"
echo ""
