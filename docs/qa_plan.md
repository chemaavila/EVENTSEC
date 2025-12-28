# QA & Test Plan for Double-Click Launcher

## Scenarios

1. **Fresh install (macOS + Windows + Linux)**
   - Run the build script to produce artifacts.
   - Double-click the launcher; confirm tray icon appears.
   - Verify config/log folders are created in OS-appropriate locations.
   - Check that `status.json` is created and updated.

2. **First run**
   - On first launch, verify the launcher detects missing config and creates it from `agent_config.example.json`.
   - Ensure the tray status shows "Stopped" initially.
   - Click "Start Worker" and verify status changes to "Running" with PID.

3. **Worker lifecycle**
   - Start worker from tray menu; verify process starts and `status.json` shows `running: true`.
   - Stop worker from tray menu; verify process terminates and `status.json` shows `running: false`.
   - Restart worker; verify clean stop/start cycle.
   - Kill worker process externally (Activity Monitor/Task Manager); verify launcher detects it and status updates.

4. **Logging & health**
   - Verify logs are written to OS-appropriate location.
   - Trigger log rotation by writing >5MB logs. Confirm `agent.log` is rotated (3 backups).
   - Open `status.json` and ensure `timestamp`, `pid`, `uptime_seconds`, `events_processed`, and `last_error` fields update.
   - Test "View Last 200 Log Lines" menu item; verify window opens with recent logs.

5. **Config management**
   - Click "Open Config"; verify config file opens in default editor.
   - Modify config (e.g., change `api_url`); restart worker; verify new config is used.
   - Corrupt the config file (e.g., invalid JSON); restart worker; verify graceful fallback to defaults.

6. **File management**
   - Click "Open Logs Folder"; verify file manager opens to logs directory.
   - Verify logs are readable and rotated correctly.

7. **CLI compatibility**
   - Run `python -m agent.agent --run-once`; verify one iteration completes and exits.
   - Run `python -m agent.agent --healthcheck`; verify JSON output and exit code (0=healthy, 1=unhealthy).
   - Run with `--config`, `--log-file`, `--status-file` overrides; verify paths are respected.

8. **Platform safety**
   - On Windows, verify `/var/log` paths are skipped gracefully (no crashes).
   - On macOS/Linux, verify `/var/log` access is attempted but failures are logged as warnings.

9. **Single-instance enforcement**
   - Launch launcher; verify tray icon appears.
   - Try to launch second instance; verify it exits immediately (lock file prevents duplicates).

10. **Quit behavior**
    - With worker running, click "Quit Launcher"; verify prompt appears.
    - Choose "Yes" (stop worker and quit); verify worker stops and launcher exits.
    - Launch again, start worker, choose "No" (quit launcher only); verify launcher exits but worker continues.

11. **Upgrade**
    - Install a new launcher build over the previous release while preserving config files.
    - Verify config/log locations remain consistent.
    - Verify worker can be started/stopped normally.

## Commands

- Build macOS: `./agent/scripts/build_macos.sh`
- Build Windows: `.\agent\scripts\build_windows.ps1`
- Build Linux: `./agent/scripts/build_linux.sh`
- Run smoke test (macOS/Linux): `./agent/scripts/smoke_test.sh`
- Run smoke test (Windows): `.\agent\scripts\smoke_test.ps1`
- Run pytest: `pytest agent/tests/`
- Manual healthcheck: `python -m agent.agent --healthcheck`
- Monitor status: `tail -f ~/.local/state/eventsec/status.json` (Linux) or `tail -f ~/Library/Application\ Support/EventSec/agent/status.json` (macOS)

## Test Checklist

- [ ] macOS: Build succeeds, `.app` bundle created
- [ ] macOS: Double-click launches tray icon
- [ ] macOS: Start/Stop/Restart worker works
- [ ] macOS: Config/logs in `~/Library/Application Support` and `~/Library/Logs`
- [ ] Windows: Build succeeds, `.exe` files created
- [ ] Windows: Double-click launches tray icon
- [ ] Windows: Start/Stop/Restart worker works
- [ ] Windows: Config/logs in `%APPDATA%` and `%LOCALAPPDATA%`
- [ ] Linux: Build succeeds, binaries created
- [ ] Linux: Launcher runs and shows tray (if GUI available)
- [ ] Linux: Start/Stop/Restart worker works
- [ ] Linux: Config/logs in `~/.config` and `~/.local/state`
- [ ] Log rotation works (5MB, 3 backups)
- [ ] Status.json updates every few seconds
- [ ] Healthcheck returns 0 for healthy, 1 for unhealthy
- [ ] CLI flags (`--config`, `--log-file`, `--status-file`) work
- [ ] Single-instance lock prevents duplicates
- [ ] Quit prompt works correctly

## Notes

- The launcher manages the agent as a child process (no system services/daemons).
- Auto-start at login is NOT implemented (by design, per user requirements).
- All paths are per-user and writable without admin privileges.
- If signing credentials are not available, run unsigned builds and record the missing signing steps in `docs/release_process.md`.
- If the tray icon fails (e.g., missing GUI libs on Linux server), fall back to CLI via `python -m agent.agent`.
