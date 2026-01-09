# EventSec Documentation - Platform Overview

This document summarizes the current EventSec Enterprise stack, describes what each major component does, and explains how the pieces interact.

## Architecture at a Glance

- **Backend (FastAPI + PostgreSQL + OpenSearch)**: Handles authentication, alerts, workplans, war room notes, sandbox analysis, endpoint inventory, telemetry ingestion, analytics/rules, and action logging. It exposes REST APIs and a metrics endpoint. Authentication uses JWTs shipped via secure cookies; every request is validated via FastAPI dependencies.
- **Frontend (React + Vite)**: Implements the UI for dashboards, alerts, endpoints, analytics, rules, and advanced search. React router and an `AuthContext` control navigation and authentication. API requests call `frontend/src/services/api.ts`, which now relies on `credentials: "include"` to include the backend cookie.
- **Agent (PyInstaller + Python)**: Sends telemetry to the backend, reports inventories/scans, and provides a CLI/GUI for deployment. Already built artifacts live under `agent/dist`/`agent-share`.
- **Supporting services**:
  - OpenSearch for event indexing and KQL workbench.
  - Postgres for relational data/models.
  - Retention job runs daily via the backend image (entrypoint `app.maintenance`).
  - **Email Protection service** (`email_protection`): exposes OAuth connectors to Gmail and Microsoft Graph, syncs inboxes, runs a lightweight phishing analysis, and stores tokens in SQLite. Accessible on port `8100`.
- **Docker-compose** orchestrates the stack plus the new connectors.
- **Docs & commands**: `docs/test_commands.txt` lists CLI commands for testing each sub-system, including OAuth flows.

## Backend Details

1. **Configuration**: `backend/app/config.py` loads secrets/URLs, including OpenSearch TLS options. Logging, secrets, and agent enrollment keys are read from files.
2. **Routing**: `backend/app/main.py` wires routers (`alerts`, `edr`, `siem`, `inventory`, `rules`, `sca`, `kql`, `agents`, etc.) to REST endpoints. Authentication helpers live in `backend/app/auth.py`.
3. **Data layer**: SQLAlchemy models in `backend/app/models.py`, Alembic migrations under `backend/alembic/versions`.
4. **Search**: `backend/app/search.py` manages OpenSearch clients, includes retries/backoff, and indexes events/alerts.
5. **Agents**: `agents_router` handles enrollment/heartbeat/action pulls. Endpoint actions are logged and results update endpoint states.
6. **Sandbox/Warroom**: Routes provide sample analysis responses plus war room note creation and action logs.
7. **Security**: FastAPI dependencies ensure `@app.get("/me")` returns user profile only when the cookie token is valid. Login sets an `HttpOnly` cookie when HTTPS is enabled.

## Frontend Details

1. **Auth layer** (`frontend/src/contexts/AuthContext.tsx`): stores `user` state, calls `/auth/login` via `api.ts`, and fetches `/me` at startup. Logout hits the backend logout endpoint to clear the cookie.
2. **API services** (`frontend/src/services/api.ts`): centralizes fetch wrappers for alerts, users, endpoints, sandbox, rules, etc. All requests set `credentials: "include"` so cookies travel along.
3. **Pages/components**: Routes configured in `frontend/src/App.tsx` cover dashboards, alerts, analytics, endpoints, workplans. Shared layout (Topbar/Sidebar) handles navigation.
4. **Styling**: CSS managed via `App.css`, `index.css`, and component-specific styles.

## Email Protection Service

1. **Purpose**: Enables OAuth integration with Google/Microsoft to gather inbox messages, run a phishing analysis, and expose sync/webhook APIs.
2. **Implementation**: `email_protection/app.py` uses FastAPI, sqlite token store, optional Pub/Sub endpoints, and sync endpoints `/sync/google` and `/sync/microsoft`.
3. **Deployment**: Dockerfile builds the app; `docker-compose.yml` exposes it on port 8100 and pulls OAuth credentials from `EMAIL_PROTECT_*` env vars.
4. **Operations**: Hooks into EventSec via documented OAuth URLs and sync workflows (see `docs/test_commands.txt`). Use `curl` to test.

## Scanner Integration

1. **Purpose**: Adds a defensive triage command that collects system/process data, flags suspicious files, optionally runs YARA/VT/OTX, and writes structured reports.
2. **Implementation**: `protoxol_triage_package/protoxol_triage.py` includes collectors, heuristics, optional reputation clients, and CLI options (e.g., `--yara`, `--vt`, `--otx`, `--zip`).

## Deployment & Testing

1. **Docker Compose** (`docker-compose.yml`): brings up OpenSearch, Postgres, backend, frontend, retention, email protection, and optional IDS (profile-based). Secrets mount JWT/agent enrollment keys.
2. **Commands**: `docs/test_commands.txt` lists CLI operations for reprovisioning (`docker compose down -v`, `up -d --build`), running migrations/tests, frontend dev server, and interaction with email protection.

## Extensibility

- **Agent API**: ready for additional command types, telemetry fields, and remote actions.
- **Frontend**: new pages can be hooked via `App.tsx` routes and share `api.ts`.
- **Email Protection**: can be invoked from the dashboard via scheduled syncs or manual buttons.
- **Scanner**: designed as an on-demand job (Docker profile) and can later be converted into an API endpoint or scheduled job.

Use this document as your reference when navigating the codebase, running the stack, or extending functionality. Let me know if you’d like a PDF/export or to link this overview from the README. 
