# EVENTSEC Technical Notes (Current State)

## Entry points & components
- **Backend API**: FastAPI app in `backend/app/main.py` routes for SIEM, EDR, agents, events, rules, and XDR actions.
- **SIEM**: `/siem/events` maps OpenSearch or Software indexer data in `backend/app/routers/siem_router.py`.
- **EDR**: `/edr/events` maps OpenSearch or Software archives via `backend/app/routers/edr_router.py`.
- **Event ingestion**: `/events` accepts incoming payloads and queues processing in `backend/app/routers/events_router.py`.
- **Agents**: EventSec enrollment + heartbeat flow in `backend/app/routers/agents_router.py`, with Software API passthrough when configured.
- **XDR actions**: `/xdr/actions` triggers Software Active Response and logs results in `backend/app/routers/xdr_router.py`.

## SIEM pipeline (current)
- Ingest → DB event → optional queue → rules/worker → OpenSearch indices.
- OpenSearch alias `events` is used for searching (`backend/app/search.py`).
- Software indexer integration is implemented to pull from `software-alerts-*` when configured (`backend/app/integrations/software_indexer.py`).

## EDR pipeline (current)
- `/edr/events` reads OpenSearch docs with `event_type` prefix `edr.` or Software archives via the indexer integration.

## Real-time
- Added SSE endpoint `/siem/stream` to stream Software alerts with polling (`backend/app/routers/siem_router.py`).

## Security & secrets
- Production mode requires non-default `SECRET_KEY` and `AGENT_ENROLLMENT_KEY` (`backend/app/config.py`).
- TLS verification is enforced for Software API/indexer in non-development environments (`backend/app/config.py`).
