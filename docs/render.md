# Render deployment (backend)

## Service settings (manual setup)

**Root Directory**
- `backend`

**Build Command**
```
pip install -r requirements.txt
```

**Start Command**
```
bash scripts/entrypoint.sh
```

## Render Start Command

If **Root Directory** is `backend`:
- `bash scripts/entrypoint.sh`

If **Root Directory** is repo root:
- `bash backend/scripts/entrypoint.sh`

## Required env vars (CORS + UI)

Set these on the **web** service (use your **production** Vercel domain):

- `DATABASE_URL=postgresql://...`
- `JWT_SECRET=...` (or `SECRET_KEY`)
- `UI_BASE_URL=https://eventsec-ihae.vercel.app`
- `CORS_ORIGINS=https://eventsec-ihae.vercel.app`
- `CORS_ALLOW_ORIGIN_REGEX=^https://.*\\.vercel\\.app$`
- `COOKIE_SECURE=true`
- `COOKIE_SAMESITE=lax` (recommended when using the Vercel `/api` proxy)
- `RUN_MIGRATIONS=true` (runs `alembic upgrade head` on startup)
- `OPENSEARCH_REQUIRED=false` (optional OpenSearch in Render)
- `OPENSEARCH_URL` (set when OpenSearch is enabled; leave unset to skip index prep)

If cookies fail cross-site (direct Render calls), set `COOKIE_SAMESITE=none` and keep `COOKIE_SECURE=true`.

## Quick checks

```
curl -i https://eventsec-backend.onrender.com/healthz
curl -i -X OPTIONS https://eventsec-backend.onrender.com/auth/login \
  -H "Origin: https://eventsec-ihae.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: authorization,content-type"
curl -i -X POST https://eventsec-backend.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"<user>","password":"<pass>"}'
```

## Troubleshooting

- **CORS preflight returns 400:** Confirm the env vars above and redeploy.
- **Proxy verification script:** Run `scripts/verify_vercel_login.sh https://<vercel-app>` and ensure `/api/healthz` is `200`, preflight returns `200/204`, and login returns `200/401/422`.
- **DB schema check:** `curl -i https://eventsec-backend.onrender.com/health/db` should return `200` when migrated.
- **OPTIONS check:** From any machine, run:
  ```
  curl -i -X OPTIONS https://eventsec-backend.onrender.com/auth/login \
    -H "Origin: https://eventsec-ihae.vercel.app" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: authorization,content-type,x-request-id"
  ```
  Expect `200`/`204` and headers:
  - `Access-Control-Allow-Origin: <origin>`
  - `Access-Control-Allow-Credentials: true`
  - `Access-Control-Allow-Headers` includes `authorization`, `content-type`, `x-request-id`
