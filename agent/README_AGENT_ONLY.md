# Agent Quickstart (Standalone)

This README focuses **only** on running and distributing the EventSec agent.

## What you need
- A running EventSec backend (API at `http://<host>:8000` or your URL)
- Backend secrets set:
  - `EVENTSEC_AGENT_TOKEN` (shared token)
  - `AGENT_ENROLLMENT_KEY` (for `/agents/enroll`)
- From this repo, the built agent artifacts under `agent/dist/`

## Step-by-step (all OS)
1) Prepare backend
   - Backend reachable (e.g., `http://localhost:8000` or your server).
   - Env vars set: `EVENTSEC_AGENT_TOKEN`, `AGENT_ENROLLMENT_KEY`.

2) Configure the agent
   - Open `agent_config.json` next to the binary (macOS: inside `dist/eventsec-agent.app/Contents/MacOS/agent_config.json`).
   - Set:
     ```json
     {
       "api_url": "http://<your-backend>:8000",
       "agent_token": "eventsec-agent-token",
       "interval": 60,
       "enrollment_key": "eventsec-enroll",
       "log_paths": [
         "/var/log/syslog",
         "/var/log/system.log"
       ]
     }
     ```
   - `api_url` must point to your backend; `agent_token` and `enrollment_key` must match backend values.
   - Logs: `agent.log` next to the binary (fallback `~/.eventsec-agent/agent.log`).

3) Run
   - Windows: double-click `agent/dist/eventsec-agent.exe`.
   - macOS: double-click `agent/dist/eventsec-agent.app`. If blocked once: `xattr -dr com.apple.quarantine dist/eventsec-agent.app`. CLI: `./agent/dist/eventsec-agent`.
   - Linux: `chmod +x agent/dist/eventsec-agent && ./agent/dist/eventsec-agent` (some DEs allow double-click if executable).

4) Verify
   - Check `agent.log` for “Enrolled successfully” and heartbeats.
   - In EventSec UI, the endpoint should show online and log events from monitored paths.

5) Share with others
   - After building on that OS: `./agent-share/scripts/prepare_share.sh` (or `.ps1` on Windows).
   - Zip `agent-share/bin/`. Recipients edit `agent_config.json` and run the OS-specific file.

6) (Optional) Build yourself
   - From `agent/`: Windows `build_windows.bat`; macOS `chmod +x build_macos.sh && ./build_macos.sh`; Linux `chmod +x build_linux.sh && ./build_linux.sh`.

## Build locally (per OS)
From `agent/`:
- Windows: `build_windows.bat`
- macOS: `chmod +x build_macos.sh && ./build_macos.sh`
- Linux: `chmod +x build_linux.sh && ./build_linux.sh`

Outputs:
- Windows: `dist/eventsec-agent.exe`
- macOS: `dist/eventsec-agent.app` (+ CLI `dist/eventsec-agent`)
- Linux: `dist/eventsec-agent`

## Package to share
After building on that OS:
```
./agent-share/scripts/prepare_share.sh   # or .ps1 on Windows
```
This copies the binary/.app and `agent_config.json` into `agent-share/bin/`. Zip that folder and send it; the recipient only edits `agent_config.json` and runs the OS-specific file.

## First run prompts (CLI)
The CLI build asks once for backend URL/token/interval/enrollment key and persists them in `agent_config.json`. GUI builds (`.exe`, `.app`) skip the wizard and rely on the config file for “double-click to run”.

## Verify connectivity
1. Run the agent.
2. Check `agent.log` for “Enrolled successfully” and heartbeats.
3. In the EventSec UI, the endpoint should appear online; log events from monitored paths should flow into Events/SIEM/EDR views.

