#!/bin/bash
# Cross-platform build script (for macOS/Linux)
# This script detects the OS and builds accordingly

OS="$(uname -s)"
echo "Detected OS: $OS"

case "$OS" in
    Linux*)
        echo "Building for Linux..."
        ./build_linux.sh
        ;;
    Darwin*)
        echo "Building for macOS..."
        ./build_macos.sh
        ;;
    *)
        echo "Unsupported OS: $OS"
        echo "Please use the appropriate build script for your platform:"
        echo "  - Windows: build_windows.bat"
        echo "  - Linux: build_linux.sh"
        echo "  - macOS: build_macos.sh"
        exit 1
        ;;
esac


