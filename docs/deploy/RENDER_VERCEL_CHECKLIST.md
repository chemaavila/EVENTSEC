# Render + Vercel Deployment Checklist

## Blueprint / Render
- [ ] `render.yaml` DB plan updated (no legacy `starter`).
- [ ] `eventsec-backend` uses `backend` rootDir and `scripts/render_start.sh`.
- [ ] Health check path set to `/healthz`.
- [ ] `DATABASE_URL` injected from Render DB.
- [ ] `JWT_SECRET` or `SECRET_KEY` set (non-default).
- [ ] `SOFTWARE_API_*` set when external engine is required.
- [ ] `SOFTWARE_INDEXER_*` set when external indexer is required.

## DB / Migrations
- [ ] Alembic upgrade runs on deploy.
- [ ] Tables exist: `alembic_version`, `users`, `pending_events`, `detection_rules`.
- [ ] No `UndefinedTable` errors at runtime.

## Vercel
- [ ] Root Directory set to `frontend` (NO OBSERVADO in repo).
- [ ] Build uses `npm ci` and `npm run build`.
- [ ] `/api` rewrite configured (via `frontend/vercel.json`).
- [ ] `VITE_API_BASE_URL` is empty or `/api`.

## SSE Live SIEM
- [ ] `/api/siem/stream` returns `event: ping` regularly.
- [ ] SIEM page shows `Live connected` status.
- [ ] New events appear without manual refresh.

## Rollback
- [ ] Render: previous release available.
- [ ] Vercel: previous deployment available.
- [ ] DB backup plan documented (NO OBSERVADO).

