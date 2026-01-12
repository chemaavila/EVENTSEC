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

## API proxy (serverless function)

All `/api/*` requests are handled by `frontend/api/[...path].ts`, which proxies to
the Render backend defined by `RENDER_BACKEND_URL`. This avoids CORS issues and
keeps cookies same-site without relying on `vercel.json` rewrites.

## Environment variables

Required:
- `RENDER_BACKEND_URL=https://eventsec-backend.onrender.com` (used by the proxy)
- `VITE_API_URL=/api` (preferred)
- `VITE_API_BASE_URL=/api` (legacy)
- `VITE_CTI_USE_MOCK=true`

Optional:
- `VITE_THREATMAP_WS_URL` (WebSocket URLs are not proxied by Vercel)
- `VITE_EMAIL_PROTECT_BASE_URL`

### Example values

- `VITE_THREATMAP_WS_URL=wss://<render-backend-host>/ws/threatmap`

## Runbook

- **Frontend shows 404 on refresh:** Confirm the SPA rewrite to `/index.html`.
- **Login cookies missing:** Verify `/api` proxy and backend `COOKIE_SECURE=true`.
- **API proxy:** `/api` is served by `frontend/api/[...path].ts` and must reach Render.
- **CORS error / Failed to fetch:** This means the UI is calling Render directly.
  - Confirm `VITE_API_URL=/api` (or `VITE_API_BASE_URL=/api`).
  - Open `https://<vercel-app>/api/healthz` and expect `200` (example: `https://eventsec-ihae.vercel.app/api/healthz`).
  - In DevTools, login should hit `https://<vercel-app>/api/auth/login` (not `onrender.com`).
  - Preflight should succeed:
    ```
    curl -i -X OPTIONS "https://<vercel-app>/api/auth/login" \
      -H "Origin: https://<vercel-app>" \
      -H "Access-Control-Request-Method: POST" \
      -H "Access-Control-Request-Headers: content-type,authorization,x-request-id"
    ```
  - Confirm `VITE_API_BASE_URL=/api`.
  - Open `https://<vercel-app>/api/healthz` and expect `200`.
  - In DevTools, login should hit `https://<vercel-app>/api/auth/login` (not `onrender.com`).
- **WebSocket errors:** Ensure `VITE_THREATMAP_WS_URL` points directly to Render.
