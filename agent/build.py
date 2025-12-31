#!/usr/bin/env python3
"""
Cross-platform build script for EventSec Agent.
Automatically detects the OS and builds the appropriate executable.
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", "build-requirements.txt"]
    )
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    )
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def build_executable():
    """Build the executable using PyInstaller."""
    print("Building executable...")

    # Ensure icons are up-to-date for the current platform.
    subprocess.check_call([sys.executable, "scripts/generate_icons.py"])

    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "eventsec-agent.spec",
    ]

    subprocess.check_call(cmd)

    dist_dir = Path("dist")
    exe_path = dist_dir / "eventsec-agent"
    config_src = Path("agent_config.json")
    config_dst = dist_dir / "agent_config.json"

    if platform.system() != "Windows" and exe_path.exists():
        os.chmod(exe_path, 0o755)
        print(f"Made {exe_path} executable")

    if config_src.exists():
        shutil.copy2(config_src, config_dst)

    app_bundle_config = (
        dist_dir / "eventsec-agent.app" / "Contents" / "MacOS" / "agent_config.json"
    )
    if app_bundle_config.parent.exists():
        shutil.copy2(config_src, app_bundle_config)


def main():
    """Main build function."""
    system = platform.system()
    print(f"Detected OS: {system}")
    print("=" * 50)

    try:
        install_dependencies()
        build_executable()

        print("=" * 50)
        print("Build complete!")

        if system == "Windows":
            print("Executable: dist\\eventsec-agent.exe")
        else:
            print("Executable: dist/eventsec-agent")

    except subprocess.CalledProcessError as e:
        print(f"Error during build: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
