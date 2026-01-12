# EVENTSEC Agent Install (Windows)

## Prereqs
- Windows Server 2019+ or Windows 10+
- Administrator rights for service installation

## Install (manual)

1. Create config at `C:\ProgramData\Eventsec\agent.yml`:

```yaml
server_url: https://<eventsec-backend>
enrollment_key: <enrollment-key>
heartbeat_interval: 30s
inventory_interval: 10m
log_level: info
max_spool_mb: 256
```

2. Copy binary to `C:\Program Files\Eventsec\eventsec-agent.exe`.

3. Install the service:

```powershell
sc.exe create EventsecAgent binPath= "C:\Program Files\Eventsec\eventsec-agent.exe run" start= auto
sc.exe start EventsecAgent
```

## Uninstall

```powershell
sc.exe stop EventsecAgent
sc.exe delete EventsecAgent
Remove-Item -Recurse -Force "C:\ProgramData\Eventsec"
Remove-Item -Recurse -Force "C:\Program Files\Eventsec"
```

## MSI Packaging

See `agent/packaging/windows/README.md` for the WiX-based MSI outline.
