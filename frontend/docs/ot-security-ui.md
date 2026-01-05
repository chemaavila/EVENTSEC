# OT Security UI (Frontend)

## Mock mode

The OT module is mock-first and defaults to mock data.

- Feature gate: `VITE_ENABLE_OT_UI=true|false` (default: `false`)
- Env flag: `VITE_OT_USE_MOCK=true|false` (default: `true`, only applies when OT UI is enabled)
- Local override (DEV only): set `localStorage.ot_use_mock` to `"true"` or `"false"`

## Routes

- `/ot/overview`
- `/ot/assets`
- `/ot/communications`
- `/ot/detections`
- `/ot/sensors`
- `/ot/pcap`

## Mock data behavior

- In-memory mock adapter with filtering, pagination, and simulated latency.
- PCAP jobs are stored in-memory for the session and move through queued → running → done.

## Tests

Tests are only included if the repo already has a test runner configured.
