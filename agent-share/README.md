# Agent Share Package

This folder keeps everything you need to hand over the EventSec agent to another device.

## Contents

- `bin/` – drop the compiled binaries here (macOS, Linux, Windows). The helper script below populates this folder automatically.
- `agent_config.example.json` – template configuration sent alongside the binary.
- `scripts/prepare_share.sh` / `scripts/prepare_share.ps1` – copy the latest build artefacts from `agent/dist/` into `bin/`.

## How to prepare the shareable bundle

1. Build the agent for your target OS:

   ```bash
   cd ../agent
   ./build_macos.sh      # or ./build_linux.sh / build_windows.bat
   ```

2. Run the helper script from the repo root:

   ```bash
   ./agent-share/scripts/prepare_share.sh
   ```

   or on Windows PowerShell:

   ```powershell
   ./agent-share/scripts/prepare_share.ps1
   ```

   This copies every `eventsec-agent*` binary from `agent/dist/` into `agent-share/bin/` and places a fresh `agent_config.json` next to it.

3. Zip or copy the entire `agent-share/` directory to the destination host.

## Instructions for the destination host

1. Extract `agent-share/` anywhere (e.g., `C:\EventSecAgent` or `/opt/eventsec-agent`).
2. Edit `agent_config.json` to point to your backend:

   ```json
   {
     "api_url": "http://<manager-ip>:8000",
     "agent_token": "eventsec-agent-token",
     "interval": 60,
     "enrollment_key": "eventsec-enroll",
     "log_paths": [
       "/var/log/system.log"
     ]
   }
   ```

3. Run the binary for your platform:

   - macOS GUI: open `agent-share/bin/eventsec-agent.app`
   - macOS/Linux CLI: `./eventsec-agent`
   - Windows: double-click `eventsec-agent.exe` (or run from PowerShell)

4. Logs are written to `agent.log` next to the executable (fallback: `~/.eventsec-agent/agent.log`). Share it when troubleshooting.
5. Confirm the host appears under **Endpoints** and telemetry/alerts flow into the EventSec dashboard.

That’s all that needs to be sent—no Python or extra dependencies required on the receiving device.***


