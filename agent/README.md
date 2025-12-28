# EventSec Agent - Complete Installation & Usage Guide

This guide covers everything you need to know to install, configure, and run the EventSec Agent from scratch.

---

## 📋 Table of Contents

1. [What is the EventSec Agent?](#what-is-the-eventsec-agent)
2. [Prerequisites](#prerequisites)
3. [Quick Start (Pre-built Executable)](#quick-start-pre-built-executable)
4. [Building from Source](#building-from-source)
5. [Configuration](#configuration)
6. [Running the Agent](#running-the-agent)
7. [Verification & Troubleshooting](#verification--troubleshooting)
8. [Advanced: Running as a Service](#advanced-running-as-a-service)
9. [Distribution to Other Devices](#distribution-to-other-devices)

---

## What is the EventSec Agent?

The EventSec Agent is a lightweight, cross-platform monitoring agent that:
- Connects to your EventSec backend server
- Monitors system logs and events
- Sends security alerts and telemetry to the backend
- Provides real-time endpoint visibility in the EventSec dashboard

**Supported Platforms:**
- ✅ macOS (10.14+)
- ✅ Windows (10/11)
- ✅ Linux (Ubuntu, Debian, RHEL, etc.)

---

## Prerequisites

### On Your Development Machine (for building)

- **Python 3.11+** (check with `python3 --version`)
- **pip** (usually comes with Python)
- **Git** (to clone the repository)

### On Target Machines (where agent runs)

- **Network access** to your EventSec backend server
- **No Python required** (if using pre-built executable)
- **Terminal access** (for CLI method) or ability to run GUI applications

### Backend Information Needed

Before installing the agent, you need:

1. **Backend URL**: `http://your-server-ip:8000` or `https://your-domain.com`
2. **Agent Token**: Must match backend `EVENTSEC_AGENT_TOKEN` (default: `eventsec-agent-token`)
3. **Enrollment Key**: Must match backend `AGENT_ENROLLMENT_KEY` (default: `eventsec-enroll`)

---

## Quick Start (Pre-built Executable)

If you already have a built executable, skip to [Configuration](#configuration).

### Step 1: Build the Agent

Navigate to the agent directory and run the build script for your platform:

#### macOS

```bash
cd agent
chmod +x build_macos.sh
./build_macos.sh
```

**Output:**
- `dist/eventsec-agent.app` (double-clickable GUI)
- `dist/eventsec-agent` (CLI binary)
- `dist/agent_config.json` (configuration file)

#### Windows

```cmd
cd agent
build_windows.bat
```

**Output:**
- `dist\eventsec-agent.exe` (double-clickable executable)
- `dist\agent_config.json` (configuration file)

#### Linux

```bash
cd agent
chmod +x build_linux.sh
./build_linux.sh
```

**Output:**
- `dist/eventsec-agent` (CLI binary)
- `dist/agent_config.json` (configuration file)

### Step 2: Configure the Agent

Edit `dist/agent_config.json` (or `dist/eventsec-agent.app/Contents/MacOS/agent_config.json` for macOS GUI):

```json
{
  "api_url": "http://YOUR-BACKEND-IP:8000",
  "agent_token": "eventsec-agent-token",
  "interval": 60,
  "agent_id": null,
  "agent_api_key": null,
  "enrollment_key": "eventsec-enroll",
  "log_paths": [
    "/var/log/system.log",
    "/var/log/syslog"
  ],
  "version": "0.3.0"
}
```

**Important Fields:**
- `api_url`: Replace `YOUR-BACKEND-IP` with your actual backend server IP/hostname
- `agent_token`: Must match backend `EVENTSEC_AGENT_TOKEN`
- `enrollment_key`: Must match backend `AGENT_ENROLLMENT_KEY`
- `log_paths`: System log files to monitor (adjust for your OS)

### Step 3: Run the Agent

#### macOS

**GUI (Double-click):**
1. Double-click `dist/eventsec-agent.app`
2. If macOS blocks it: Right-click → Open → Open
3. Or run: `xattr -dr com.apple.quarantine dist/eventsec-agent.app`

**CLI (Terminal):**
```bash
cd dist
chmod +x eventsec-agent
./eventsec-agent
```

#### Windows

**GUI (Double-click):**
1. Double-click `dist\eventsec-agent.exe`

**CLI (Command Prompt/PowerShell):**
```cmd
cd dist
eventsec-agent.exe
```

#### Linux

```bash
cd dist
chmod +x eventsec-agent
./eventsec-agent
```

### Step 4: Verify It's Working

Check the log file (next to the executable):

```bash
# macOS/Linux
tail -f dist/agent.log

# Windows
type dist\agent.log
```

**Look for:**
- ✅ `Enrolled successfully with ID: <agent-id>`
- ✅ `Heartbeat acknowledged`
- ✅ `Using backend: http://...`

Check the EventSec Dashboard:
- Open your backend UI (usually `http://your-backend-ip:3000`)
- Navigate to **Agents** or **Endpoints**
- Your agent should appear as **online** ✅

---

## Building from Source

If you want to build the agent yourself or modify the code:

### Step 1: Clone/Download the Repository

```bash
git clone <repository-url>
cd EVENTSEC
```

### Step 2: Navigate to Agent Directory

```bash
cd agent
```

### Step 3: Build for Your Platform

The build scripts automatically:
- Create a temporary virtual environment
- Install all dependencies
- Build the executable using PyInstaller
- Clean up temporary files

**macOS:**
```bash
chmod +x build_macos.sh
./build_macos.sh
```

**Windows:**
```cmd
build_windows.bat
```

**Linux:**
```bash
chmod +x build_linux.sh
./build_linux.sh
```

### Step 4: Configure and Run

Follow steps 2-4 from [Quick Start](#quick-start-pre-built-executable).

---

## Configuration

### Configuration File Location

The agent looks for `agent_config.json` in this order:

1. **Next to the executable** (`dist/agent_config.json`)
2. **Inside macOS app bundle** (`dist/eventsec-agent.app/Contents/MacOS/agent_config.json`)
3. **OS-specific config directory:**
   - macOS: `~/Library/Application Support/EventSec Agent/agent_config.json`
   - Windows: `%APPDATA%\EventSec Agent\agent_config.json`
   - Linux: `~/.config/eventsec-agent/agent_config.json`

### Configuration File Format

```json
{
  "api_url": "http://localhost:8000",
  "agent_token": "eventsec-agent-token",
  "interval": 60,
  "agent_id": null,
  "agent_api_key": null,
  "enrollment_key": "eventsec-enroll",
  "log_paths": [
    "/var/log/system.log",
    "/var/log/syslog"
  ],
  "version": "0.3.0"
}
```

### Configuration Fields Explained

| Field | Required | Description | Default |
|-------|----------|-------------|---------|
| `api_url` | ✅ Yes | Backend server URL | `http://localhost:8000` |
| `agent_token` | ✅ Yes | Shared token (must match backend) | `eventsec-agent-token` |
| `enrollment_key` | ✅ Yes | Enrollment key (must match backend) | `eventsec-enroll` |
| `interval` | ❌ No | Heartbeat interval (seconds) | `60` |
| `log_paths` | ❌ No | Log files to monitor | OS-specific defaults |
| `agent_id` | ❌ No | Pre-assigned agent ID (auto-generated if null) | `null` |
| `agent_api_key` | ❌ No | Pre-assigned API key (auto-generated if null) | `null` |

### Environment Variables

You can override config values with environment variables:

```bash
# macOS/Linux
export EVENTSEC_API_URL=http://192.168.1.100:8000
export EVENTSEC_AGENT_TOKEN=my-custom-token
export EVENTSEC_AGENT_INTERVAL=30
export EVENTSEC_AGENT_CONFIG=/custom/path/config.json

# Windows
set EVENTSEC_API_URL=http://192.168.1.100:8000
set EVENTSEC_AGENT_TOKEN=my-custom-token
set EVENTSEC_AGENT_INTERVAL=30
```

### First-Run Wizard (CLI Only)

When you run the CLI binary for the first time without a config file, it will prompt:

```
Backend URL [http://localhost:8000]: 
Agent Token [eventsec-agent-token]: 
Heartbeat Interval (seconds) [60]: 
Enrollment Key [eventsec-enroll]: 
```

Your answers are saved to `agent_config.json` automatically.

---

## Running the Agent

### Method 1: GUI (Double-Click)

**macOS:**
- Double-click `eventsec-agent.app`
- Agent runs in the background
- Check logs: `~/Library/Logs/EventSec Agent/agent.log` or next to executable

**Windows:**
- Double-click `eventsec-agent.exe`
- Agent runs in the background
- Check logs: `%APPDATA%\EventSec Agent\agent.log` or next to executable

### Method 2: CLI (Terminal)

**macOS/Linux:**
```bash
./dist/eventsec-agent
```

**Windows:**
```cmd
dist\eventsec-agent.exe
```

**Run in Background:**
```bash
# macOS/Linux
nohup ./dist/eventsec-agent > agent.log 2>&1 &

# Windows (PowerShell)
Start-Process -FilePath "dist\eventsec-agent.exe" -WindowStyle Hidden
```

### Method 3: Development Mode (Python)

For development or testing:

```bash
cd agent

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run agent
python -m agent
# or
python agent.py
```

### Command-Line Options

```bash
# Health check
./eventsec-agent --healthcheck

# Run once (test mode, no continuous loop)
./eventsec-agent --run-once

# Show help
./eventsec-agent --help
```

---

## Verification & Troubleshooting

### Check Agent Status

**Health Check:**
```bash
./eventsec-agent --healthcheck
```

Expected output:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00+00:00",
  "pid": 12345,
  "running": true,
  "uptime_seconds": 300,
  "events_processed": 42
}
```

**View Logs:**
```bash
# Real-time log viewing
tail -f dist/agent.log

# Last 50 lines
tail -n 50 dist/agent.log

# Search for errors
grep -i error dist/agent.log
```

### Common Issues

#### ❌ "Cannot connect to backend"

**Solutions:**
1. **Check backend is running:**
   ```bash
   curl http://YOUR-BACKEND-IP:8000/
   ```
   Should return: `{"status":"ok","service":"eventsec-backend"}`

2. **Check firewall:** Ensure port 8000 is open
3. **Verify `api_url`** in `agent_config.json` is correct
4. **Test network connectivity:**
   ```bash
   ping YOUR-BACKEND-IP
   ```

#### ❌ "Enrollment failed"

**Solutions:**
1. Verify `enrollment_key` matches backend `AGENT_ENROLLMENT_KEY`
2. Check backend logs for enrollment errors
3. Ensure backend `/agents/enroll` endpoint is accessible
4. Verify `agent_token` matches backend `EVENTSEC_AGENT_TOKEN`

#### ❌ macOS: "App is damaged" or Gatekeeper blocks it

**Solutions:**
```bash
# Remove quarantine attribute
xattr -dr com.apple.quarantine dist/eventsec-agent.app

# Or allow in System Settings
# System Settings → Privacy & Security → Click "Open Anyway"
```

#### ❌ "Permission denied" when running CLI

**Solutions:**
```bash
# Make executable
chmod +x eventsec-agent

# Run with explicit path
./eventsec-agent
```

#### ❌ Agent stops after closing terminal

**Solutions:**
- Use `nohup` (see [Running the Agent](#running-the-agent))
- Use launchd/systemd service (see [Advanced: Running as a Service](#advanced-running-as-a-service))
- Use the `.app` bundle (double-click)

#### ❌ Log file not found

The agent writes logs to:
1. `agent.log` next to the executable
2. Fallback: `~/.eventsec-agent/agent.log` (macOS/Linux) or `%APPDATA%\EventSec Agent\agent.log` (Windows)

Check both locations:
```bash
# Check next to executable
ls -la dist/agent.log

# Check fallback location
ls -la ~/.eventsec-agent/agent.log
```

---

## Advanced: Running as a Service

### macOS: Using launchd

Create a LaunchAgent:

```bash
# Create the plist file
cat > ~/Library/LaunchAgents/com.eventsec.agent.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.eventsec.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/eventsec-agent</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/path/to/agent.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/agent.log</string>
    <key>WorkingDirectory</key>
    <string>/path/to/dist</string>
</dict>
</plist>
EOF

# Replace /path/to with actual paths
nano ~/Library/LaunchAgents/com.eventsec.agent.plist

# Load the service
launchctl load ~/Library/LaunchAgents/com.eventsec.agent.plist

# Start it
launchctl start com.eventsec.agent

# Check status
launchctl list | grep eventsec
```

**Stop/Unload:**
```bash
launchctl stop com.eventsec.agent
launchctl unload ~/Library/LaunchAgents/com.eventsec.agent.plist
```

### Linux: Using systemd

Create a systemd service:

```bash
# Create service file
sudo nano /etc/systemd/system/eventsec-agent.service
```

**Service file content:**
```ini
[Unit]
Description=EventSec Agent
After=network.target

[Service]
Type=simple
User=your-username
ExecStart=/path/to/eventsec-agent
Restart=always
RestartSec=10
StandardOutput=append:/path/to/agent.log
StandardError=append:/path/to/agent.log
WorkingDirectory=/path/to/dist

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable eventsec-agent
sudo systemctl start eventsec-agent

# Check status
sudo systemctl status eventsec-agent
```

### Windows: Using Task Scheduler

1. Open **Task Scheduler** (`taskschd.msc`)
2. Create **Basic Task**
3. Set trigger: **At startup** or **When I log on**
4. Action: **Start a program**
   - Program: `C:\path\to\eventsec-agent.exe`
   - Start in: `C:\path\to\dist`
5. Check **Run whether user is logged on or not**
6. Save and test

---

## Distribution to Other Devices

### Step 1: Build the Agent

Build for the target platform (see [Building from Source](#building-from-source)).

### Step 2: Prepare Distribution Package

Create a folder with:

```
EventSec-Agent-macOS/
├── eventsec-agent.app          (or eventsec-agent.exe for Windows)
├── agent_config.json           (template, user must edit)
└── README.txt                  (instructions)
```

**README.txt template:**
```
EventSec Agent Installation
===========================

1. Edit agent_config.json:
   - Set api_url to your backend server
   - Set agent_token to match backend EVENTSEC_AGENT_TOKEN
   - Set enrollment_key to match backend AGENT_ENROLLMENT_KEY

2. Run the agent:
   - macOS: Double-click eventsec-agent.app
   - Windows: Double-click eventsec-agent.exe
   - Linux: chmod +x eventsec-agent && ./eventsec-agent

3. Check agent.log for status

4. Verify agent appears in EventSec dashboard
```

### Step 3: Transfer to Target Device

**Methods:**
- **AirDrop** (macOS to macOS)
- **USB drive**
- **Email/Cloud storage** (Google Drive, Dropbox, etc.)
- **Network share** (SMB, NFS, etc.)

### Step 4: Install on Target Device

1. Extract the package
2. Edit `agent_config.json` with backend details
3. Run the executable (see [Running the Agent](#running-the-agent))
4. Verify connectivity (see [Verification & Troubleshooting](#verification--troubleshooting))

---

## Quick Reference

### Essential Commands

```bash
# Build
./build_macos.sh          # macOS
build_windows.bat         # Windows
./build_linux.sh          # Linux

# Run
./dist/eventsec-agent     # macOS/Linux CLI
dist\eventsec-agent.exe   # Windows CLI
# Or double-click .app/.exe

# Health check
./dist/eventsec-agent --healthcheck

# View logs
tail -f dist/agent.log

# Stop agent
pkill -f eventsec-agent   # macOS/Linux
taskkill /F /IM eventsec-agent.exe  # Windows
```

### File Locations

**macOS:**
- Config: `~/Library/Application Support/EventSec Agent/agent_config.json`
- Logs: `~/Library/Logs/EventSec Agent/agent.log` or next to executable
- Status: `~/Library/Application Support/EventSec Agent/status.json`

**Windows:**
- Config: `%APPDATA%\EventSec Agent\agent_config.json`
- Logs: `%APPDATA%\EventSec Agent\agent.log` or next to executable
- Status: `%APPDATA%\EventSec Agent\status.json`

**Linux:**
- Config: `~/.config/eventsec-agent/agent_config.json`
- Logs: `~/.local/state/eventsec-agent/agent.log` or next to executable
- Status: `~/.config/eventsec-agent/status.json`

---

## Support & Documentation

- **Main README**: See `../README.md` for full platform documentation
- **Build Documentation**: See `README_BUILD.md` for advanced build options
- **Agent Code**: See `agent.py` for implementation details
- **Tests**: See `tests/` directory for test examples

---

## License

See main repository LICENSE file.

---

**Last Updated:** 2024-01-01

