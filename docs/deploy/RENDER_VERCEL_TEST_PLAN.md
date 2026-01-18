# Render + Vercel Test Plan (No Docker)

> All checks below should be executed after each deploy. If evidence is not available in logs,
> mark the step as **NO OBSERVADO**.

## Backend (Render)
1. **Health**
   - `GET https://<render-backend>/healthz` returns 200 and `{ "ok": true }`.
   - `GET https://<render-backend>/health/db` returns 200 and no missing tables.

2. **Migrations**
   - Render logs show Alembic upgrade executed without errors.
   - Tables exist: `alembic_version`, `users`, `pending_events`, `detection_rules`.
   - If missing tables persist, enable `EVENTSEC_DB_DEBUG=1` and confirm DB/host/search_path in logs.

3. **Worker**
   - Worker starts without crash loops.
   - Logs show worker role: `VULN_INTEL_WORKER_ROLE=worker`.

4. **Software engine integration**
   - `GET /agents` returns Software agents (when `SOFTWARE_API_URL` configured).
   - `GET /siem/events` returns Software alerts (when `SOFTWARE_INDEXER_URL` configured).
   - `GET /edr/events` returns Software archive events (when configured).
   - `POST /xdr/actions` triggers Software active response and creates audit log entry.

## Frontend (Vercel)
1. **Build**
   - Vercel build passes using Node 20–22.

2. **Routing**
   - App loads at `/` without SPA 404 errors.
   - All API calls use `/api` and are rewritten to Render backend.

3. **CORS**
   - Browser console shows no CORS errors.

## SSE Real-time
1. **Backend stream**
   - `curl -N https://<vercel-domain>/api/siem/stream` emits `event: ping` messages.

2. **Frontend live view**
   - SIEM page shows `Live connected` indicator.
   - Events appear without manual refresh.

## Result checklist
- [ ] Backend healthy
- [ ] Migrations complete
- [ ] Worker healthy
- [ ] Software engine integration OK
- [ ] Frontend build OK
- [ ] /api proxy OK
- [ ] SSE live OK
