# TEST PLAN: Software parity (SIEM + XDR)

## Automated checks
### Unit
- Mapping Software alerts → EVENTSEC SIEM/EDR schemas.

### Integration
- Mock Software API token + `/agents` response.
- Mock Software indexer search response.

### E2E (manual/CI with docker)
1. `docker compose up -d --build` (EVENTSEC)
2. Start Software docker stack separately.
3. Enroll a Software agent or send event via `/event` API.
4. Validate:
   - Software agent appears in EVENTSEC `/agents`.
   - Software alert appears in `/siem/events`.
   - Software archive telemetry appears in `/edr/events`.
   - SSE `/siem/stream` updates UI in real time.
   - `POST /xdr/actions` triggers active response and is logged.

## Scripts
- Add Software stack under `infra/software` and follow `RUNBOOK.md`.
