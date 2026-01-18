# RUNBOOK: EVENTSEC + Software (Separate Stack)

> This runbook assumes Software is run as a **separate docker-compose stack** to avoid GPLv2 code
> integration into EVENTSEC. Add the Software docker repo under `infra/software/` (see infra/software/README.md).

## 1) Start EVENTSEC
```bash
docker compose up -d --build
```

## 2) Start Software stack (separate)
```bash
cd infra/software/software-docker
# Follow upstream instructions to generate certs and start the stack
# Example:
# docker compose -f generate-indexer-certs.yml run --rm generator
# docker compose up -d
```

## 3) Configure EVENTSEC to talk to Software
Set these environment variables for the EVENTSEC backend:
- `SOFTWARE_API_URL=https://software-manager:55000`
- `SOFTWARE_API_USER=<software_api_user>`
- `SOFTWARE_API_PASSWORD=<software_api_password>`
- `SOFTWARE_API_VERIFY_CERTS=true`
- `SOFTWARE_INDEXER_URL=https://software-indexer:9200`
- `SOFTWARE_INDEXER_USER=<indexer_user>`
- `SOFTWARE_INDEXER_PASSWORD=<indexer_password>`
- `SOFTWARE_INDEXER_VERIFY_CERTS=true`

## 4) Validate
- `GET /agents` returns Software agents.
- `GET /siem/events` returns Software alerts.
- `GET /edr/events` returns Software archive events.
- `GET /siem/stream` returns server-sent events (SSE) for live alerts.
- `POST /xdr/actions` triggers Software Active Response.

## Security notes
- Set `SECRET_KEY` and `AGENT_ENROLLMENT_KEY` in production.
- Ensure TLS certificates are valid for Software API + Indexer.
