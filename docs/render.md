# Render deployment (backend)

## Required env vars (CORS + UI)

Set these on the **web** service (use your **production** Vercel domain):

- `UI_BASE_URL=https://eventsec-ihae.vercel.app`
- `CORS_ORIGINS=https://eventsec-ihae.vercel.app`
- `CORS_ALLOW_ORIGIN_REGEX=https://.*\\.vercel\\.app`
- `COOKIE_SECURE=true`
- `COOKIE_SAMESITE=lax` (recommended when using the Vercel `/api` proxy)

If cookies fail cross-site (direct Render calls), set `COOKIE_SAMESITE=none` and keep `COOKIE_SECURE=true`.

## Troubleshooting

- **CORS preflight returns 400:** Confirm the env vars above and redeploy.
- **Proxy verification script:** Run `scripts/verify_proxy.sh https://<vercel-app>` and ensure `/api/healthz` is `200` and preflight returns `200`.
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
