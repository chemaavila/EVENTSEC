# Release Process

## Versioning

- Bump version in `agent/agent.py` (`_get_agent_version()` function) before release.
- Follow semantic versioning (MAJOR.MINOR.PATCH).
- Record the built version in `dist/` artifacts (e.g., `eventsec-agent-1.2.0.zip`).

## Build Artifacts

### macOS

1. Run `./agent/scripts/build_macos.sh` on a macOS host with Python 3.10+.
2. The script builds:
   - `eventsec-agent`: Worker binary (console)
   - `EventSec Agent.app`: Launcher bundle (windowed, tray icon)
3. macOS build runs `python -m agent.assets.generate_icons` to render `agent/assets/logo.png`, `.ico`, and `.icns` from `logo.svg`.
4. Outputs:
   - `dist/eventsec-agent`: Worker executable
   - `dist/EventSec Agent.app`: Launcher bundle
   - `dist/eventsec-agent-macos.zip`: ZIP archive of `.app` bundle
5. Optional notarization (documented below).

### Windows

1. Run `.\agent\scripts\build_windows.ps1` in PowerShell 5.1+.
2. This executes PyInstaller for both:
   - `eventsec-agent.exe`: Worker binary (console)
   - `eventsec-launcher.exe`: Launcher executable (windowed, no console)
3. The Windows build includes `agent/assets/logo.svg` and the generated `logo.ico`.
4. Outputs:
   - `dist/eventsec-agent.exe`: Worker executable
   - `dist/eventsec-launcher.exe`: Launcher executable
5. Optional: Create an installer using Inno Setup or NSIS to wrap both binaries.

### Linux

1. Execute `./agent/scripts/build_linux.sh`.
2. The script packages both binaries:
   - `dist/eventsec-agent`: Worker executable
   - `dist/eventsec-launcher`: Launcher executable
3. Linux build reuses the generated `logo.png` for the launcher icon.
4. Outputs:
   - `dist/eventsec-agent`: Worker executable
   - `dist/eventsec-launcher`: Launcher executable
   - `dist/eventsec-agent.service`: Sample systemd unit template (optional, for reference)

## Signing & Notarization (Optional)

**Note**: For development builds, signing is optional. For production distribution, signing is recommended.

### macOS

1. **Code Signing**:
   ```bash
   codesign --deep --force --options runtime --sign "Developer ID Application: Your Name" "dist/EventSec Agent.app"
   ```

2. **Notarization**:
   ```bash
   xcrun altool --notarize-app \
     --primary-bundle-id "com.eventsec.agent.launcher" \
     --username "your-apple-id@example.com" \
     --password "@keychain:AC_PASSWORD" \
     --file "dist/eventsec-agent-macos.zip"
   ```

3. **Stapling** (after notarization completes):
   ```bash
   xcrun stapler staple "dist/EventSec Agent.app"
   ```

### Windows

1. **Sign executable**:
   ```powershell
   signtool sign /a /tr http://timestamp.digicert.com /td sha256 /fd sha256 dist\eventsec-launcher.exe
   signtool sign /a /tr http://timestamp.digicert.com /td sha256 /fd sha256 dist\eventsec-agent.exe
   ```

2. **Sign installer** (if using Inno Setup/NSIS):
   ```powershell
   signtool sign /a /tr http://timestamp.digicert.com /td sha256 /fd sha256 dist\EventSecAgentSetup.exe
   ```

### Linux

- Optionally GPG-sign the release archive:
  ```bash
  gpg --armor --detach-sign dist/eventsec-agent-linux.tar.gz
  ```

## QA/Validation

1. Run QA plan (see `docs/qa_plan.md`).
2. Verify:
   - Tray icon appears and menu works
   - Worker can be started/stopped/restarted
   - Config/logs are created in correct OS-appropriate locations
   - Status.json updates correctly
   - Log rotation works (5MB, 3 backups)
   - Healthcheck returns correct exit codes
   - CLI flags work as expected
   - Single-instance lock prevents duplicates

3. Run smoke tests:
   - macOS/Linux: `./agent/scripts/smoke_test.sh`
   - Windows: `.\agent\scripts\smoke_test.ps1`

4. Run unit tests:
   ```bash
   pytest agent/tests/
   ```

## Publishing

1. Upload built artifacts to release channel:
   - macOS: `eventsec-agent-macos.zip` (or signed `.app` bundle)
   - Windows: `eventsec-agent.exe` and `eventsec-launcher.exe` (or installer)
   - Linux: `eventsec-agent` and `eventsec-launcher` binaries

2. Update `docs/double_click.md` with:
   - New version number
   - SHA256 hashes of artifacts
   - Release notes/changelog

3. Tag release in git:
   ```bash
   git tag -a v1.2.0 -m "Release v1.2.0"
   git push origin v1.2.0
   ```

## Development Builds

For development/testing, unsigned builds are acceptable. Users may need to:
- macOS: Right-click → Open (to bypass Gatekeeper) or run `xattr -dr com.apple.quarantine dist/EventSec\ Agent.app`
- Windows: Click "More info" → "Run anyway" if SmartScreen blocks
- Linux: Ensure binaries are executable (`chmod +x dist/eventsec-*`)
