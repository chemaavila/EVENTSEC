# Network IDS Rules

Detection rules are stored in `detection_rules` and evaluated in `backend/app/main.py`.

## Rule format
Each rule uses **conditions** (exact match or list match) against:
- Event fields: `event_type`, `severity`, `category`, etc.
- Detail fields via `details.*` (e.g., `details.src_ip`, `details.signature`).

Example:
```json
{
  "name": "Suricata high severity",
  "severity": "high",
  "enabled": true,
  "create_incident": true,
  "conditions": {
    "event_type": "network",
    "details.source": "suricata",
    "details.severity": [1, 2]
  }
}
```

## Network fields available in `details.*`
- `source`, `event_type`, `src_ip`, `src_port`, `dst_ip`, `dst_port`, `proto`
- `signature`, `category`, `severity`
- `http.*`, `dns.*`, `tls.*`
- `sensor`

## Example rules (seeded)
See `backend/app/data/detection_rules.json` for 15+ IDS-focused rules covering:
- Suricata severity 1-2 alerts
- Malware/C2 signatures
- DNS NXDOMAIN & suspicious TLDs
- TLS SNI/JA3
- Rare ports and SMB over Internet
- HTTP POST to suspicious hosts

## Tuning
- Add allowlists by matching specific `details.src_ip` or `details.dst_ip` and disabling those rules.
- Duplicate rules for environment-specific sensor names.
