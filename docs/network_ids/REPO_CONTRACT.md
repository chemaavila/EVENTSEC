# EVENTSEC Repository Contract (Discovery)

## Auth contract
- **JWT login**: `POST /auth/login` returns `access_token` and `user` (see `backend/app/main.py`).
- **Accepted auth headers**: `Authorization: Bearer <token>`, `X-Auth-Token: <token>`, or `access_token` cookie (see `backend/app/auth.py`).
- **Agent authentication**:
  - `X-Agent-Key` (per-agent API key), `X-Agent-Token` (shared token) for ingest endpoints (see `backend/app/routers/events_router.py` and `backend/app/main.py`).
  - Shared token is read from `EVENTSEC_AGENT_TOKEN` and is disabled in production when using the `main.py` auth dependency.

## Multi-tenant contract
- **No explicit tenant model** exists in Postgres. There is no `tenant_id` column on most tables (see `backend/app/models.py`).
- `tenant_id` appears only in raw OpenSearch mappings (`search.py`) and is currently written as `None` (see `backend/app/routers/events_router.py`).

## Data/event contract
- **Primary event ingest**: `POST /events` expects `SecurityEventCreate` (see `backend/app/routers/events_router.py`, `backend/app/schemas.py`).
- **SecurityEvent fields**: `event_type`, `severity`, `category`, `details`.
- **Event processing**: events are stored in Postgres (`models.Event`) and then pushed to a queue for rule evaluation and OpenSearch indexing (see `backend/app/main.py`).

## Alerts contract
- **Alert model**: `models.Alert` with `status` in `open | in_progress | closed` and `severity` in `low | medium | high | critical` (see `backend/app/models.py`, `backend/app/schemas.py`).
- **Endpoints**: `GET /alerts`, `GET /alerts/{id}`, `POST /alerts`, `PATCH /alerts/{id}` (see `backend/app/main.py`).
- **Rule engine**: `models.DetectionRule` with JSON `conditions`; rules are evaluated per event and create alerts when matched (see `backend/app/main.py`, `backend/app/models.py`).

## OpenSearch contract
- **Client**: `backend/app/search.py` builds OpenSearch client from `settings.opensearch_url`.
- **Indices**:
  - `events-v1` (security events)
  - `alerts-v1` (alerts)
  - `raw-events-YYYY.MM.DD` (raw ingest)
  - `dlq-events-YYYY.MM.DD` (dead-letter queue)
- **Mappings** defined in `backend/app/search.py`.
- **No ILM/rollover** logic is present; daily indices for raw/dlq are created on demand.

## UI contract
- **Routing/layout**: `frontend/src/App.tsx` controls routing and shared chrome (Topbar/Sidebar). Layout styles in `frontend/src/App.css`.
- **Navigation**: `frontend/src/components/layout/Sidebar.tsx`.
- **Alert UI**: `frontend/src/pages/Alerts/*`.
- **Events/KQL**: `frontend/src/pages/EventsExplorerPage.tsx` uses `/events` and `/search/kql`.

## Email notifications contract
- **Notification service**: `backend/app/notifications.py` with `NotificationService.emit()`.
- **Used in**: alert lifecycle operations in `backend/app/main.py` (alert create, update, escalation).

## GAPS
1. **Multi-tenant enforcement**
   - **Missing**: No tenant model or auth-bound tenant_id in DB or OpenSearch writes.
   - **Impact**: Ingest cannot be scoped per tenant; all data is global.
   - **Fix (minimal)**: Add `tenant_id` fields to new IDS tables and accept optional tenant_id on ingest with future authentication mapping. For now, default to `None` and document as single-tenant.
   - **Implementation in this PR**: IDS models include nullable `tenant_id` and ingest stores `None` (future-ready).

2. **Network IDS canonical event model**
   - **Missing**: Existing `network_events` table is web/URL-focused and lacks IDS fields (src/dst IP, flow ids, etc.).
   - **Impact**: Suricata/Zeek data cannot be represented or queried without new schema.
   - **Fix (minimal)**: Replace the network events schema with an IDS-capable model and new OpenSearch mapping.
   - **Implementation in this PR**: IDS event model + OpenSearch index `network-events-*`.

3. **Incident/Case management**
   - **Missing**: No Incident model or API endpoints exist in the backend.
   - **Impact**: Alerts cannot be escalated to cases with evidence/actions.
   - **Fix (minimal)**: Add `incidents` + `incident_items` tables, APIs, and UI list/detail.
   - **Implementation in this PR**: Minimal Incident CRUD with attachments to alerts/events/actions.

4. **Response actions (IPS-lite)**
   - **Missing**: There is no generic response action tracker (only alert-specific actions in `main.py`).
   - **Impact**: IPS-lite orchestration cannot be tracked or attached to incidents.
   - **Fix (minimal)**: Add `response_actions` table + API list/create/update.
   - **Implementation in this PR**: Action tracking endpoints and UI list.
