#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "Building EventSec Agent for Linux..."

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r build-requirements.txt
pip install pyinstaller

echo "Generating icons..."
python -m agent.assets.generate_icons || python scripts/generate_icons.py || true

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
