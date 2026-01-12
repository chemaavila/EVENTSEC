# EVENTSEC Endpoint Agent (Go)

This directory contains the Go-based EVENTSEC endpoint agent. It ships a single CLI (`eventsec-agent`) with platform-specific collectors enabled via build tags.

## Overview

- **Common core**: configuration, schema, disk spool, transport, logging.
- **Platform collectors**: `agent/platform/darwin`, `agent/platform/linux`, `agent/platform/windows`.
- **CLI**: `agent/cmd/eventsec-agent`.
- **Tools**: mock collector + telemetry replay.

## Backend Integration

The agent aligns with existing backend endpoints in `backend/app/routers`:

- `POST /agents/enroll` — enrollment using `enrollment_key`.
- `POST /agents/{agent_id}/heartbeat` — heartbeat.
- `POST /inventory/{agent_id}` — inventory snapshots.
- `POST /events` — defensive telemetry events.

## Build

```bash
cd agent

go build ./cmd/eventsec-agent
```

### Cross-platform build (examples)

```bash
GOOS=linux GOARCH=amd64 go build -o dist/eventsec-agent-linux ./cmd/eventsec-agent
GOOS=windows GOARCH=amd64 go build -o dist/eventsec-agent.exe ./cmd/eventsec-agent
GOOS=darwin GOARCH=amd64 go build -o dist/eventsec-agent-darwin ./cmd/eventsec-agent
```

## Running (basic mode)

Create a config file (see `docs/INSTALL_*.md` for paths). Minimal fields:

```yaml
server_url: https://localhost:8443
enrollment_key: eventsec-enroll
heartbeat_interval: 30s
inventory_interval: 10m
log_level: info
max_spool_mb: 256
```

Run:

```bash
./eventsec-agent run -c /etc/eventsec/agent.yml
```

## Local Tools

- Mock collector:
  ```bash
  go run ./tools/mock-collector
  ```

- Telemetry replay:
  ```bash
  go run ./tools/replay --server http://localhost:8081 --api-key mock-api-key --input events.json
  ```

## Tests

```bash
go test ./...
```
