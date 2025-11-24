#!/usr/bin/env python3
"""
Cross-platform build script for EventSec Agent.
Automatically detects the OS and builds the appropriate executable.
"""

import os
import platform
import subprocess
import sys


def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def build_executable():
    """Build the executable using PyInstaller."""
    print("Building executable...")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name", "eventsec-agent",
        "--console",
        "--clean",
        "agent.py"
    ]
    
    subprocess.check_call(cmd)
    
    # Make executable on Unix systems
    if platform.system() != "Windows":
        exe_path = os.path.join("dist", "eventsec-agent")
        if os.path.exists(exe_path):
            os.chmod(exe_path, 0o755)
            print(f"Made {exe_path} executable")


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


