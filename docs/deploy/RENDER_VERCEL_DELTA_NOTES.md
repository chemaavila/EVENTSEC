# Render/Vercel Delta Notes (Repo vs Required)

> This document compares **required configuration** vs **repo configuration**.
> Runtime/console settings that are not in the repository are marked **NO OBSERVADO**.

## Summary
- Render blueprint database plan must be updated from legacy `starter` to a supported plan.
- Render startup scripts already exist and use `/healthz` health checks.
- Vercel routing is defined in both `/vercel.json` and `/frontend/vercel.json` (potential duplication).
- Frontend defaults to `/api` in production (proxy-first approach).

## Comparative Table
| Elemento | ZIP requerido | Config actual (repo) | Diferencia | Fix |
|---|---|---|---|---|
| Frontend framework | Vite SPA | `frontend/package.json` uses Vite | OK | None |
| RootDir frontend | `frontend` | `frontend/vercel.json` exists | OK | Ensure Vercel RootDir=frontend (NO OBSERVADO) |
| Build/install/output | `npm ci` / `npm run build` / `dist` | Scripts in `frontend/package.json` | OK | None |
| Node version | 20–22 | `frontend/package.json` engines | OK | None |
| Vercel rewrites | `/api/:path*` → Render | `/frontend/vercel.json` and `/vercel.json` both define same rewrites | Potential duplication | Align to single source (NO OBSERVADO which file Vercel uses) |
| API base URL | `/api` in production | `frontend/src/config/endpoints.ts` defaults to `/api` | OK | Remove absolute prod URL env var (NO OBSERVADO) |
| Backend runtime | Python 3.11 | `.python-version` is 3.11 | OK | Set Render runtime to 3.11 (NO OBSERVADO) |
| Backend start | `scripts/render_start.sh` | Render YAML uses `render_start.sh` | OK | None |
| Health check | `/healthz` | Render YAML `healthCheckPath: /healthz` | OK | None |
| DB plan (blueprint) | Non-legacy plan | `render.yaml` DB plan set to `REPLACE_ME` | Needs manual UI update | Set to supported plan in Render UI |
| DB migrations | Alembic | `render_predeploy.sh` runs alembic + table check | OK | Ensure DATABASE_URL points to same DB (NO OBSERVADO) |
| SSE backend | Keep-alive + heartbeat | `/siem/stream` SSE implemented in backend | OK | Ensure proxy headers + heartbeat handled (repo updated) |
| CORS | allow Vercel origin | CORS origin + regex in backend settings | OK | Ensure env values in Render UI (NO OBSERVADO) |

## Notes on NO OBSERVADO
- Render UI settings (rootDir, env vars, DB plan chosen) are not in the repo.
- Vercel project settings (RootDir, env vars) are not in the repo.

