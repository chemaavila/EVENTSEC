# Building EventSec Agent Executables

This guide explains how to build standalone executables for the EventSec Agent that can run on Windows, macOS, and Linux without requiring Python to be installed.

## Prerequisites

- Python 3.11 or higher (with `venv` module available)
- On Windows/macOS/Linux, ensure `python`/`python3` resolves to the interpreter you want to use
- No global pip install is required; the scripts now create a temporary virtualenv (`.build-venv`)

## Quick Build

### Windows

1. Open Command Prompt or PowerShell in the `agent` directory
2. Run:
   ```cmd
   build_windows.bat
   ```
   The script will create `.build-venv`, install dependencies inside it, run PyInstaller, and delete the venv.
3. The executable will be in the `dist` folder: `dist\eventsec-agent.exe`

### Linux

1. Open terminal in the `agent` directory
2. Make the script executable:
   ```bash
   chmod +x build_linux.sh
   ```
3. Run:
   ```bash
   ./build_linux.sh
   ```
   The script creates y elimina `.build-venv` automáticamente.
4. The executable will be in the `dist` folder: `dist/eventsec-agent`

### macOS

1. Open terminal in the `agent` directory
2. Make the script executable:
   ```bash
   chmod +x build_macos.sh
   ```
3. Run:
   ```bash
   ./build_macos.sh
   ```
   Internamente crea `.build-venv` para sortear el error “externally managed environment” (PEP 668).
4. The executable will be in the `dist` folder: `dist/eventsec-agent`

### Auto-detect (macOS/Linux)

```bash
chmod +x build_all.sh
./build_all.sh
```

After any build, the script copies `agent_config.json` next to the executable. Each endpoint reads that file (API URL, shared token, interval) the first time it starts, so make sure you update it before distributing the binary.

> Tip: when running the binary interactively, it prompts for backend URL/token/interval on the first launch and writes the answers into `agent_config.json`. That means you can hand out the executable + config file and the agent will auto-register on other hosts as soon as it starts.

## Manual Build

If you prefer to build manually:

1. Create and activate a virtual environment (recommended to avoid PEP 668):
   ```bash
   python3 -m venv .manual-venv
   source .manual-venv/bin/activate  # Windows: .manual-venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```

3. Build the executable:
   ```bash
   pyinstaller --onefile --name eventsec-agent --console --clean agent.py
   ```

4. Deactivate/remove the venv if desired.
5. The executable will be in the `dist` folder.

## Using the Executable

### Windows

```cmd
dist\eventsec-agent.exe
```

Or with environment variables:
```cmd
set EVENTSEC_API_URL=http://your-server:8000
set EVENTSEC_AGENT_INTERVAL=30
dist\eventsec-agent.exe
```

### Linux/macOS

```bash
./dist/eventsec-agent
```

Or with environment variables:
```bash
export EVENTSEC_API_URL=http://your-server:8000
export EVENTSEC_AGENT_INTERVAL=30
./dist/eventsec-agent
```

## Environment Variables

The agent supports the following environment variables:

- `EVENTSEC_API_URL`: Backend API URL (default: `http://localhost:8000`)
- `EVENTSEC_AGENT_INTERVAL`: Interval between heartbeats in seconds (default: `60`)

## Distribution

After building, you can distribute the executable from the `dist` folder:

- **Windows**: `eventsec-agent.exe` (single file, ~10-15 MB)
- **Linux**: `eventsec-agent` (single file, ~10-15 MB)
- **macOS**: `eventsec-agent` (single file, ~10-15 MB)

**Note**: The executable is platform-specific. You need to build it on each target platform, or use cross-compilation tools.

## Troubleshooting

### "PyInstaller not found"

Install PyInstaller:
```bash
pip install pyinstaller
```

### "Permission denied" (Linux/macOS)

Make the executable file executable:
```bash
chmod +x dist/eventsec-agent
```

### Large file size

The executable includes Python and all dependencies. This is normal for PyInstaller one-file builds. The size is typically 10-15 MB.

### Antivirus warnings

Some antivirus software may flag PyInstaller executables as suspicious. This is a false positive. You can:
- Add an exception for the executable
- Sign the executable with a code signing certificate (for production)

## Advanced Options

### Custom icon (Windows)

```bash
pyinstaller --onefile --name eventsec-agent --icon=icon.ico --console agent.py
```

### No console window (Windows)

```bash
pyinstaller --onefile --name eventsec-agent --noconsole agent.py
```

### Include additional files

Create a `.spec` file for advanced customization:
```bash
pyinstaller --name eventsec-agent agent.py
# Edit eventsec-agent.spec
pyinstaller eventsec-agent.spec
```

## Building for Multiple Platforms

To build for all platforms, you need access to each platform or use:

1. **Virtual machines** for each OS
2. **Docker containers** for Linux builds
3. **CI/CD pipelines** (GitHub Actions, GitLab CI, etc.)

### Example GitHub Actions workflow

```yaml
name: Build Executables

on: [push, pull_request]

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [windows-latest, ubuntu-latest, macos-latest]
    
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r agent/requirements.txt
          pip install pyinstaller
      - name: Build executable
        run: |
          cd agent
          pyinstaller --onefile --name eventsec-agent --console agent.py
      - name: Upload artifact
        uses: actions/upload-artifact@v2
        with:
          name: eventsec-agent-${{ matrix.os }}
          path: agent/dist/*
```


