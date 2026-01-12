# Vercel deployment (frontend)

## Project settings

**Root Directory**
- `frontend` (this is required; it also means `vercel.json` must live in `frontend/`)

**Install Command**
```
npm ci
```

**Build Command**
```
npm run build
```

**Output Directory**
- `dist`

## Rewrites (proxy + SPA fallback)

Because the Vercel Root Directory is `frontend`, the effective file is:
- `frontend/vercel.json`

Use `rewrites` in `vercel.json`:
- `/api/:path*` → `${RENDER_BACKEND_URL}/:path*`
- `/(.*)` → `/index.html` (SPA fallback)

This proxy keeps browser requests same-site so cookies work reliably.

## Environment variables

Required:
- `VITE_API_URL=/api` (preferred)
- `VITE_API_BASE_URL=/api` (legacy)
- `RENDER_BACKEND_URL=https://eventsec-backend.onrender.com` (used in `vercel.json`)
- `VITE_CTI_USE_MOCK=true`

Optional:
- `VITE_THREATMAP_WS_URL` (WebSocket URLs are not proxied by Vercel)
- `VITE_EMAIL_PROTECT_BASE_URL`

### Example values

- `VITE_THREATMAP_WS_URL=wss://<render-backend-host>/ws/threatmap`

## Runbook

- **Frontend shows 404 on refresh:** Confirm the SPA rewrite to `/index.html`.
- **Login cookies missing:** Verify `/api` rewrite and backend `COOKIE_SECURE=true`.
- **CORS error / Failed to fetch:** This means the UI is calling Render directly.
  - Confirm `VITE_API_BASE_URL=/api`.
  - Open `https://<vercel-app>/api/healthz` and expect `200`.
  - In DevTools, login should hit `https://<vercel-app>/api/auth/login` (not `onrender.com`).
- **WebSocket errors:** Ensure `VITE_THREATMAP_WS_URL` points directly to Render.
