# How to Run (Double-Click)

This guide explains how to start the EventSec detection agent without touching the command line. The launcher provides a transparent tray/menu UI that manages the agent as a child process.

## Quick Start

1. **Build the binaries**
   - **macOS**: Run `./agent/scripts/build_macos.sh` to build both `eventsec-agent` (worker) and `EventSec Agent.app` (launcher). Double-click the `.app`; the tray icon appears in the menu bar.
   - **Windows**: Run `.\agent\scripts\build_windows.ps1`. Double-click `dist\eventsec-launcher.exe` to open the tray.
   - **Linux**: Run `./agent/scripts/build_linux.sh`, then run `dist/eventsec-launcher` to show the tray.

2. **Launcher UX**
   - After double-click, a tray/menu bar icon appears (always visible while launcher is running).
   - Right-click or open the icon menu to:
     - **Status**: Shows Running/Stopped, PID, last heartbeat, last error
     - **Start Worker**: Starts the agent as a child process
     - **Stop Worker**: Stops the agent process
     - **Restart Worker**: Stops and restarts the agent
     - **Open Config**: Opens `agent_config.json` (creates from example if missing)
     - **Open Logs Folder**: Opens the logs directory in file manager
     - **View Last 200 Log Lines**: Shows a simple window with recent log entries
     - **Quit Launcher**: Prompts to stop worker or quit launcher only

3. **Config + Logs Locations**

   **Windows (per-user)**:
   - Config: `%APPDATA%\EventSec\agent\agent_config.json`
   - Logs: `%LOCALAPPDATA%\EventSec\logs\agent.log`
   - Status: `%LOCALAPPDATA%\EventSec\agent\status.json`

   **macOS (per-user)**:
   - Config: `~/Library/Application Support/EventSec/agent/agent_config.json`
   - Logs: `~/Library/Logs/EventSec/agent.log`
   - Status: `~/Library/Application Support/EventSec/agent/status.json`

   **Linux (per-user, XDG)**:
   - Config: `~/.config/eventsec/agent_config.json`
   - Logs: `~/.local/state/eventsec/agent.log` (fallback: `~/.cache/eventsec/agent.log`)
   - Status: `~/.local/state/eventsec/status.json` (fallback: `~/.cache/eventsec/status.json`)

4. **Health & Status**
   - The agent writes `status.json` every few seconds with:
     - `timestamp`: ISO8601 timestamp
     - `pid`: Process ID
     - `running`: Boolean
     - `uptime_seconds`: Seconds since start
     - `events_processed`: Counter
     - `last_error`: Error message if any
     - `version`: Agent version
     - `mode`: "foreground" or "service"
   - The tray UI reads this file every 3 seconds to update the status text.
   - Health states:
     - **Healthy**: Recent heartbeat (< 10 seconds old)
     - **Degraded**: Stale heartbeat
     - **Stopped**: No heartbeat and no running process

5. **CLI Compatibility**
   - The agent still supports CLI flags:
     - `--config <path>`: Override config file path
     - `--log-file <path>`: Override log file path
     - `--status-file <path>`: Override status file path
     - `--run-once`: Run one iteration and exit (for tests)
     - `--healthcheck`: Print health JSON and exit
   - Example: `python -m agent.agent --config /custom/path.json --run-once`

6. **Troubleshooting**
   - **Tray icon**: The tray icon is sourced from `agent/assets/logo.svg`. Replace it with your own for branding, rerun `python -m agent.assets.generate_icons`, and rebuild.
   - **SVG conversion**: If `cairosvg` is available:
     - macOS: `brew install cairo pango gdk-pixbuf libffi`
     - Windows: Install wheels (`pip install cairosvg`) or use pre-rendered `logo.png` fallback
   - **No tray icon**: Ensure `pystray` and `Pillow` are installed.
   - **Worker fails to start**: Check the log file or `status.json` for errors.
   - **Launcher locked**: The launcher creates a lock file in the temp directory to prevent multiple instances. Delete it if a crash prevents restart.
   - **Windows /var/log error**: The agent gracefully skips Unix log paths on Windows. This is expected behavior.

## Building from Source

See `agent/README_BUILD.md` for detailed build instructions. Quick summary:

```bash
# macOS
./agent/scripts/build_macos.sh

# Windows (PowerShell)
.\agent\scripts\build_windows.ps1

# Linux
./agent/scripts/build_linux.sh
```

Outputs are placed in `agent/dist/`:
- `eventsec-agent` (or `.exe` on Windows): Worker binary
- `eventsec-launcher` (or `.exe` on Windows, `.app` on macOS): Launcher app
