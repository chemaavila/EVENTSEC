# EVENTSEC Agent Install (macOS)

## Prereqs
- macOS 13+
- Administrator rights for launchd daemon installation

## Install

1. Create config at `/Library/Application Support/Eventsec/agent.yml`:

```yaml
server_url: https://<eventsec-backend>
enrollment_key: <enrollment-key>
heartbeat_interval: 30s
inventory_interval: 10m
log_level: info
max_spool_mb: 256
```

2. Copy binary to `/usr/local/bin/eventsec-agent`.

3. Install launchd plist (see `agent/packaging/macos/com.eventsec.agent.plist`):

```bash
sudo cp agent/packaging/macos/com.eventsec.agent.plist /Library/LaunchDaemons/
sudo launchctl load /Library/LaunchDaemons/com.eventsec.agent.plist
```

## Uninstall

```bash
sudo launchctl unload /Library/LaunchDaemons/com.eventsec.agent.plist
sudo rm -f /Library/LaunchDaemons/com.eventsec.agent.plist
sudo rm -f /usr/local/bin/eventsec-agent
sudo rm -rf "/Library/Application Support/Eventsec"
```

## pkg Packaging

See `agent/packaging/macos/README.md` for unsigned pkg build steps and notarization guidance.
