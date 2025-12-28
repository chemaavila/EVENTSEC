# Quick Start - Building Executables

## Windows

```cmd
cd agent
build_windows.bat
```

> The script creates a temporary `.build-venv`, installs dependencies inside it, runs PyInstaller, and removes the venv.

Executable: `dist\eventsec-agent.exe` (double-clickable, no console)

## Linux

```bash
cd agent
chmod +x build_linux.sh
./build_linux.sh
```

Executable: `dist/eventsec-agent` (CLI)

## macOS

```bash
cd agent
chmod +x build_macos.sh
./build_macos.sh
```

> Uses a temporary `.build-venv` to avoid the “externally managed environment” error on modern macOS.

Executable: `dist/eventsec-agent` (CLI) + `dist/eventsec-agent.app` (double-clickable bundle)

## Configure the agent

Every build places (or first run generates) `agent_config.json` next to the executable (and inside `Contents/MacOS` for the `.app`). Edit it before running on other devices:

```json
{
  "api_url": "http://your-server-ip:8000",
  "agent_token": "super-secret-token",
  "interval": 60
}
```

If present, environment variables override these values. You can also point to a different file via `EVENTSEC_AGENT_CONFIG`.

When you run the CLI binary from a terminal, it will ask once for the backend URL, token, and heartbeat interval and persist the answers back to `agent_config.json`. The GUI (`.exe` / `.app`) builds skip the prompt and rely entirely on the config file, so shipping the executable + `agent_config.json` is enough for other devices to auto-configure themselves on first start. Runtime logs are written to `agent.log` next to the executable; if that path is read-only the agent falls back to `~/.eventsec-agent/agent.log`.

## Python Script (Cross-platform)

```bash
cd agent
python build.py
```

## Using the Executable

### Windows
```cmd
dist\eventsec-agent.exe
```

### Linux/macOS
```bash
./dist/eventsec-agent
```

### With Custom Settings
```bash
# Windows
set EVENTSEC_API_URL=http://192.168.1.100:8000
set EVENTSEC_AGENT_INTERVAL=30
set EVENTSEC_AGENT_TOKEN=my-shared-token
dist\eventsec-agent.exe

# Linux/macOS
export EVENTSEC_API_URL=http://192.168.1.100:8000
export EVENTSEC_AGENT_INTERVAL=30
export EVENTSEC_AGENT_TOKEN=my-shared-token
./dist/eventsec-agent
```

## Distribution

The executable is a standalone file (~10-15 MB) that includes Python and all dependencies. You can distribute it without requiring Python to be installed on the target machine.

**Note**: Each OS requires its own build. You cannot run a Windows executable on Linux, etc.

### Authentication with the backend

- The backend exposes `EVENTSEC_AGENT_TOKEN` (default `eventsec-agent-token`). Set the same value on the agent before running it.
- Requests include an `X-Agent-Token` header so the backend can allow POSTs to `/alerts` without a human session.


