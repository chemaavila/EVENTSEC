# Render deployment (backend)

## Blueprint (render.yaml)

The repo root includes a Render Blueprint with:
- Web service `eventsec-backend`
- Background worker `eventsec-vuln-worker`
- Postgres database `eventsec-db`

The web service runs `alembic upgrade head` before deploy and fails the deploy if
`pending_events` is missing after migrations.

## Service settings (for manual setup)

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

**Health Check Path**
```
/healthz
```

## Required environment variables

Minimum required values for a clean boot on Render:

- `DATABASE_URL` (Postgres connection string, from Render DB)
- `JWT_SECRET` (alias for `SECRET_KEY` used by the app)
- `RUN_MIGRATIONS=true` (runs `alembic upgrade head` on startup)
- `OPENSEARCH_REQUIRED=false` (optional OpenSearch in Render)
- `OPENSEARCH_URL` (set when OpenSearch is enabled; leave unset to skip index prep)
- `COOKIE_SECURE=true`

## Vercel frontend note

The frontend uses `frontend/vercel.json` rewrites so `/api/:path*` proxies to the
Render backend origin.

## Common environment variables from `app/config.py`

Set these as needed for your environment:

- `ENVIRONMENT`
- `SECRET_KEY`
- `SECRET_KEY_FILE`
- `AGENT_ENROLLMENT_KEY`
- `AGENT_ENROLLMENT_KEY_FILE`
- `OPENSEARCH_URL`
- `OPENSEARCH_VERIFY_CERTS`
- `OPENSEARCH_CA_FILE`
- `OPENSEARCH_CLIENT_CERTFILE`
- `OPENSEARCH_CLIENT_KEYFILE`
- `OPENSEARCH_MAX_RETRIES`
- `OPENSEARCH_RETRY_BACKOFF_SECONDS`
- `OPENSEARCH_REQUIRED`
- `SERVER_HOST`
- `SERVER_PORT`
- `SERVER_HTTPS_ENABLED`
- `SERVER_SSL_CERTFILE`
- `SERVER_SSL_KEYFILE`
- `SERVER_SSL_CA_FILE`
- `SERVER_SSL_CLIENT_CERT_REQUIRED`
- `CORS_ORIGINS`
- `CORS_ALLOW_ORIGIN_REGEX` (example: `https://.*\.vercel\.app`)
- `COOKIE_NAME`
- `COOKIE_SAMESITE`
- `COOKIE_SECURE`
- `COOKIE_DOMAIN`
- `COOKIE_PATH`
- `COOKIE_MAX_AGE_SECONDS`
- `MANAGER_EMAILS`
- `LEVEL1_DL`
- `LEVEL2_DL`
- `UI_BASE_URL`
- `NOTIFICATION_DEDUP_MINUTES`
- `NETWORK_INGEST_MAX_EVENTS`
- `NETWORK_INGEST_MAX_BYTES`
- `PASSWORD_GUARD_RATE_LIMIT_PER_MINUTE`
- `INCIDENT_AUTO_CREATE_ENABLED`
- `INCIDENT_AUTO_CREATE_MIN_SEVERITY`
- `VULN_INTEL_ENABLED`
- `FEATURE_INTEL_ENABLED`
- `FEATURE_OT_ENABLED`
- `FEATURE_EMAIL_ACTIONS_ENABLED`
- `THREATMAP_FALLBACK_COORDS`
- `VULN_INTEL_WORKER_ROLE`
- `NVD_API_KEY`
- `NVD_BASE_URL`
- `NVD_CPE_BASE_URL`
- `OSV_BASE_URL`
- `OSV_BATCH_URL`
- `EPSS_BASE_URL`
- `VULN_INTEL_HTTP_TIMEOUT_SECONDS`
- `VULN_INTEL_HTTP_RETRIES`
- `VULN_INTEL_CACHE_TTL_HOURS`
- `VULN_INTEL_NOTIFY_IMMEDIATE_MIN_RISK`
- `VULN_INTEL_NOTIFY_DIGEST_ENABLED`
- `VULN_INTEL_NOTIFY_DIGEST_HOUR_LOCAL`
- `VULN_INTEL_TIMEZONE`
- `VULN_INTEL_CREATE_ALERTS_FOR_CRITICAL`
- `DB_READY_WAIT_ATTEMPTS`
- `DB_READY_WAIT_INTERVAL_SECONDS`

## CORS + cookies

When the frontend runs on Vercel, proxy `/api` to the backend (same-site). With
this setup you can keep `COOKIE_SAMESITE=lax` and set `COOKIE_SECURE=true`.

If you skip the proxy and call the backend cross-site, set:
- `COOKIE_SAMESITE=none`
- `COOKIE_SECURE=true`

## Runbook

- **Deploy fails on preDeploy:** Check Render logs for `pending_events table
  missing`. If present, verify Alembic migrations ran and DB points to the
  correct instance.
- **`/readyz` returns 503:** Check DB connectivity and `OPENSEARCH_REQUIRED`.
  If OpenSearch is optional, ensure `OPENSEARCH_REQUIRED=false`.
- **Auth cookies missing:** Confirm Vercel `/api` proxy is configured and
  `COOKIE_SECURE=true`.
