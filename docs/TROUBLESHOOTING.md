# EventSec Troubleshooting

## Frontend Rollup native module failures in Docker

**Symptoms**
- `Error: Cannot find module '@rollup/rollup-linux-<arch>-<libc>'`
- `ERR_MODULE_NOT_FOUND` during `npm run build` or `vite build`

**Root cause**
Rollup uses platform-specific optional dependencies. In Docker builds, those optional packages
may be skipped or resolved for a different architecture/`libc` than the container (x64 vs arm64,
GNU libc vs musl), causing missing native modules at build time.

**Fix**
- The frontend Dockerfile enforces `npm ci --include=optional`, installs the expected Rollup
  native package for the current `platform/arch/libc`, and performs a `require()` to fail fast.

**Verification**
```bash
docker compose build frontend
```

**If the error persists**
- Check that the Node image is `node:20-slim` and that your builder uses the expected architecture.
- Clear Docker build cache:
  ```bash
  docker builder prune -f
  ```
- Confirm the Rollup version is present in `frontend/package-lock.json` and `node_modules/rollup`.

## Backend healthcheck failures

**Symptoms**
- `backend` stays `unhealthy` in `docker compose ps`

**Fix**
- Verify the backend responds at `/healthz` and `/readyz`:
  ```bash
  curl -sSf http://localhost:8000/healthz
  curl -sSf http://localhost:8000/readyz
  ```
- Ensure Postgres and OpenSearch containers are healthy:
  ```bash
  docker compose ps
  docker compose logs --tail=200 db opensearch
  ```
- Inspect the container health status directly:
  ```bash
  docker inspect --format '{{json .State.Health}}' eventsec_backend | jq
  ```

## OpenSearch healthcheck gotchas

**Symptoms**
- `opensearch` stays `unhealthy` even though logs show it started

**Root cause**
Single-node OpenSearch will often remain `yellow` (no replica allocation). A strict `green`
check will fail. Additionally, the base image may not include `curl`.

**Fix**
- Healthcheck waits for `yellow`:
  ```text
  /_cluster/health?wait_for_status=yellow&timeout=2s
  ```
- If `curl` is missing, build a custom image that adds it and update compose accordingly.

## IDS stack capture limitations

**Symptoms**
- Suricata/Zeek containers run but only see container-to-container traffic.

**Root cause**
Docker bridge networking does not expose host traffic to IDS containers by default.

**Fix (Linux only)**
- Use host networking and grant capabilities:
  ```yaml
  network_mode: host
  cap_add:
    - NET_ADMIN
    - NET_RAW
  ```

**macOS Docker Desktop**
- Host networking behaves differently; IDS containers will not capture host traffic. Expect
  only inter-container traffic unless you use a dedicated sensor on the host.

## Data lake usage endpoints returning 403

**Symptoms**
- `GET /tenants/{tenant_id}/usage` returns `403 Data lake feature is disabled for this tenant`
- `GET /tenants/{tenant_id}/storage-policy` returns `403 Tenant access denied`

**Fix**
- Ensure the authenticated user has a matching `tenant_id`.
- Enable the feature flag for that tenant:
  ```bash
  curl -X PUT http://localhost:8000/tenants/<tenant_id>/storage-policy \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -d '{"data_lake_enabled": true}'
  ```

## Health smoke tests

```bash
curl -i http://localhost:8000/healthz
curl -i http://localhost:8000/readyz
curl -I http://localhost:5173/
```
