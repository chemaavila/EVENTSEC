# Deployment Guide (Render + Vercel, no Docker)

> Scope: Production deployment without Docker. This guide uses existing Render/Vercel conventions in the repo.
> Where details are not in the repository, they are marked **NO OBSERVADO**.

## Prerequisites
- **Backend**: Python 3.11 (see `.python-version`).
- **Frontend**: Node 20–22 (see `frontend/package.json` engines).
- **Database**: PostgreSQL 15 or compatible (Render managed DB or existing).
- **Software engine**: External API + Indexer only (no embedded code).

## Path 1 — Render Blueprint (render.yaml)

1. Update `render.yaml` database plan:
   - Replace the legacy `starter` plan with a supported plan in the Render UI.
   - The repo uses a placeholder `REPLACE_ME` to avoid assuming a plan.

2. Create Blueprint:
   - Render → Blueprints → New Blueprint Instance.
   - Select repo and branch (NO OBSERVADO: actual repo/branch in UI).
   - Ensure services are created:
     - `eventsec-backend` (web service)
     - `eventsec-vuln-worker` (worker)
     - `eventsec-db` (database)

3. Verify required commands from `render.yaml`:
   - `preDeployCommand`: `bash scripts/render_predeploy.sh`
   - `startCommand`: `bash scripts/render_start.sh`
   - `healthCheckPath`: `/healthz`

4. Set required env vars (Render UI):
   - `DATABASE_URL` (from DB)
   - `JWT_SECRET` or `SECRET_KEY`
   - `UI_BASE_URL`, `CORS_ORIGINS`, `CORS_ALLOW_ORIGIN_REGEX`
   - `SOFTWARE_API_*` and `SOFTWARE_INDEXER_*` when using external engine

## Path 2 — Render Manual Alignment (existing services)

1. Backend service (existing):
   - RootDir: `backend`
   - PreDeploy: `bash scripts/render_predeploy.sh`
   - Start: `bash scripts/render_start.sh`
   - Health check: `/healthz`

2. Worker service:
   - RootDir: `backend`
   - Start: `bash scripts/render_worker.sh`

3. Database:
   - Use Render managed PostgreSQL or existing DB.
   - Set `DATABASE_URL` to the internal connection string.

## Vercel (frontend)

1. Project settings:
   - Root directory: `frontend`
   - Build: `npm ci && npm run build`
   - Output: `dist`

2. API routing:
   - Use `/api` proxy via `frontend/vercel.json` rewrites.
   - Set `VITE_API_BASE_URL` to `/api` or leave empty (defaults to `/api` in production).

## Health checks
- Backend: `GET /healthz` should return `{ "ok": true }`.
- DB: `GET /health/db` should return OK with no missing tables.

## Rollback
- Render: redeploy the previous successful release (Render UI).
- Vercel: rollback to prior deployment (Vercel UI).
- DB: do **not** drop database without a backup (NO OBSERVADO: backup strategy).

