#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "Building EventSec Agent for macOS..."

# Install dependencies
echo "Installing build dependencies..."
python3 -m venv .build-venv || true
source .build-venv/bin/activate || . .build-venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r build-requirements.txt
pip install pyinstaller

# Generate icons
echo "Generating icons..."
python -m agent.assets.generate_icons || python scripts/generate_icons.py || true

# Build agent worker
echo "Building agent worker..."
pyinstaller --noconfirm --clean eventsec-agent.spec

# Build launcher (.app bundle)
echo "Building launcher (.app bundle)..."
pyinstaller --noconfirm --clean eventsec-launcher.spec

# Create ZIP release
echo "Creating ZIP release..."
mkdir -p dist
APP_PATH="dist/EventSec Agent.app"
ZIP_PATH="dist/eventsec-agent-macos.zip"

if [ -d "$APP_PATH" ]; then
    rm -f "$ZIP_PATH"
    zip -r "$ZIP_PATH" "$APP_PATH"
    echo ""
    echo "Build complete!"
    echo "  Agent worker: dist/eventsec-agent"
    echo "  Launcher app: $APP_PATH"
    echo "  ZIP release: $ZIP_PATH"
else
    echo "Warning: .app bundle not found at $APP_PATH"
fi

deactivate || true
rm -rf .build-venv || true
