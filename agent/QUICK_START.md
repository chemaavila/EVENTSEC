# Quick Start - Building Executables

## Windows

```cmd
cd agent
build_windows.bat
```

> The script creates a temporary `.build-venv`, installs dependencies inside it, runs PyInstaller, and removes the venv.

Executable: `dist\eventsec-agent.exe`

## Linux

```bash
cd agent
chmod +x build_linux.sh
./build_linux.sh
```

Executable: `dist/eventsec-agent`

## macOS

```bash
cd agent
chmod +x build_macos.sh
./build_macos.sh
```

> Uses a temporary `.build-venv` to avoid the “externally managed environment” error on modern macOS.

Executable: `dist/eventsec-agent`

## Configure the agent

Every build places (or first run generates) `agent_config.json` next to the executable. Edit it before running on other devices:

```json
{
  "api_url": "http://your-server-ip:8000",
  "agent_token": "super-secret-token",
  "interval": 60
}
```

If present, environment variables override these values. You can also point to a different file via `EVENTSEC_AGENT_CONFIG`.

When you run the binary from a terminal, it will ask once for the backend URL, token, and heartbeat interval and persist the answers back to `agent_config.json`. Ship that file together with the executable and other devices will auto-configure themselves on first start.

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


