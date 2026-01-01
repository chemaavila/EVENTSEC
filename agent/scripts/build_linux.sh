#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "Building EventSec Agent for Linux..."

PYTHON_BIN=""
if command -v python3.12 >/dev/null 2>&1; then
  PYTHON_BIN="python3.12"
elif command -v python3.11 >/dev/null 2>&1; then
  PYTHON_BIN="python3.11"
else
  echo "Error: Python 3.11 or 3.12 is required to build the agent (Pillow compatibility)." >&2
  exit 1
fi

echo "Installing dependencies..."
"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install -r requirements.txt
"$PYTHON_BIN" -m pip install -r build-requirements.txt
"$PYTHON_BIN" -m pip install pyinstaller

echo "Generating icons..."
"$PYTHON_BIN" -m agent.assets.generate_icons || "$PYTHON_BIN" scripts/generate_icons.py || true

echo "Building agent worker..."
pyinstaller --noconfirm --clean eventsec-agent.spec

echo "Building launcher..."
pyinstaller --noconfirm --clean eventsec-launcher.spec

echo "Packaging systemd unit template..."
cat <<'EOF' > dist/eventsec-agent.service
[Unit]
Description=EventSec Agent service
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/eventsec-agent
Restart=always
RestartSec=5
User=%i

[Install]
WantedBy=default.target
EOF

echo ""
echo "Build complete!"
echo "  Agent worker: dist/eventsec-agent"
echo "  Launcher: dist/eventsec-launcher"
echo "  Systemd unit template: dist/eventsec-agent.service"
