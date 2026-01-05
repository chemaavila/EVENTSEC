# Network Security / IDS Capability for EVENTSEC

This package adds **network IDS capability** (Suricata + Zeek) to EVENTSEC, including:

- **Ingest** of Suricata EVE JSON and Zeek JSON logs.
- **Normalization & indexing** to OpenSearch (`network-events-*`).
- **Detections** through the existing rule engine (`detection_rules`).
- **IPS-lite** response actions (tracking only; no inline blocking).
- **Incidents** generated from alerts or created manually.
- **Docs, samples, and tests** for reproducible local workflows.

## What this is (and is not)
- ✅ **This is NOT inline IPS.** We only track response actions and forward orchestration requests.
- ✅ **This is event ingestion + detection + response tracking** for SOC workflows.

## Components
- **Backend**: New network ingest endpoints, parsers, OpenSearch mappings, incident/action APIs.
- **Collector**: `sensors/collector` tailer and sample replayer.
- **Sensors**: Suricata + Zeek configs under `sensors/`.
- **UI**: Network Security section and Incidents pages.
- **Rules**: Network IDS rules seeded in `backend/app/data/detection_rules.json`.

## Documents
- [Quickstart (dev)](quickstart_dev.md)
- [Production deploy](deploy_prod.md)
- [Rules](rules.md)
- [Troubleshooting](troubleshooting.md)
- [Evidence pack](evidence.md)
- [Repo contract](REPO_CONTRACT.md)
