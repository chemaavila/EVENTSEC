# EVENTSEC Agent Security Notes

## Data Collected (Defensive Only)
- Host inventory: OS, kernel, hostname.
- Process snapshot: PID, name, path, PPID.
- Network connections: local/remote IP/port, PID when available.
- Logged-in users (non-sensitive identifiers).

## Permissions
- Runs with least privilege.
- Elevated privileges only required for service install or for reading OS logs where applicable.

## Storage & Secrets
- API keys stored in OS-appropriate state directories with restrictive permissions.
- TLS is required for production environments.
- Optional custom CA bundle supported via system trust stores.

## Threat Model
- Protects confidentiality and integrity of defensive telemetry.
- Assumes OS-level controls remain intact.
- Does not attempt stealth, persistence tricks, credential theft, keylogging, or bypass of OS security controls.

## Uninstall
See platform install docs for explicit uninstall steps.
