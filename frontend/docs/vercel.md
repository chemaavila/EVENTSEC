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

**Node.js version**
- `20.x` (match `frontend/.nvmrc` and `frontend/package.json` engines)
- In Vercel: Project Settings → General → Node.js Version → `20.x`
- Ensure Production Overrides (if used) also set `20.x`

## API proxy + rewrites

Because the Vercel Root Directory is `frontend`, the effective config file is
`frontend/vercel.json`. The root-level `vercel.json` is ignored by Vercel when
Root Directory is set, so keep rewrites in `frontend/vercel.json`.

`frontend/vercel.json` rewrites `/api/*` to Render, keeping same-origin calls
and avoiding CORS issues. The optional `/api/*` proxy function in
`frontend/api/[...path].ts` can also be used, but the rewrite ensures proxying
is always applied at the edge.

## Environment variables

Required:
- `RENDER_BACKEND_URL=https://eventsec-backend.onrender.com` (used by the proxy function)
- `VITE_API_URL=/api` (preferred)
- `VITE_API_BASE_URL=/api` (legacy)
- `VITE_CTI_USE_MOCK=true`

Optional:
- `VITE_THREATMAP_WS_URL` (WebSocket URLs are not proxied by Vercel)
- `VITE_EMAIL_PROTECT_BASE_URL`

### Example values

- `VITE_THREATMAP_WS_URL=wss://<render-backend-host>/ws/threatmap`

## Runbook

- **Frontend shows 404 on refresh:** Confirm the SPA rewrite to `/index.html` in `frontend/vercel.json`.
- **Login cookies missing:** Verify `/api` proxy and backend `COOKIE_SECURE=true`.
- **API proxy:** `/api` must reach Render via Vercel rewrite or API proxy function.
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
- **WebSocket errors:** Ensure `VITE_THREATMAP_WS_URL` points directly to Render.
