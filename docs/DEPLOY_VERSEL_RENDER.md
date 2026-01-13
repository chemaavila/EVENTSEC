# Render + Vercel deployment settings

## Render (backend)

**Root Directory**
- `backend`

**Build Command**
```
pip install -r requirements.txt
```

**Start Command**
If Root Directory is `backend`:
```
bash scripts/entrypoint.sh
```

If Root Directory is repo root:
```
bash backend/scripts/entrypoint.sh
```

**Required env vars**
- `DATABASE_URL`
- `JWT_SECRET`
- `RUN_MIGRATIONS=true`
- `CORS_ORIGINS=https://eventsec-ihae.vercel.app`
- `CORS_ALLOW_ORIGIN_REGEX=^https://.*\.vercel\.app$`
- `COOKIE_SECURE=true`

**Optional env vars**
- `OPENSEARCH_REQUIRED=false`
- `OPENSEARCH_URL` (unset if OpenSearch is disabled)

## Vercel (frontend)

**Root Directory**
- `frontend`

**Rewrites**
- `frontend/vercel.json` proxies `/api/:path*` to the Render backend.

**Node version**
- `.nvmrc` and `package.json` engines target Node 20.x for consistent builds.
