# Troubleshooting

## Docker / Compose

- **OpenSearch fails to start**: On Linux, ensure `vm.max_map_count >= 262144`:
  ```bash
  sudo sysctl -w vm.max_map_count=262144
  ```
- **Backend cannot connect to OpenSearch**: Verify `OPENSEARCH_URL` matches the Compose
  service name (`http://opensearch:9200`).
- **Backend cannot connect to Postgres**: Ensure `DATABASE_URL` points to `db` in Compose
  (`postgresql+psycopg2://eventsec:eventsec@db:5432/eventsec`).

## Frontend

- **Vite build fails with native Rollup**: Run `npm rebuild` in `frontend/` (CI already does
  this in `.github/workflows/ci.yml`).
- **UI shows no data**: Verify backend is running and `VITE_THREATMAP_WS_URL` (if set) points
  to the backend WebSocket endpoint.

## Backend / Agent

- **401 for agent enrollment**: Ensure `AGENT_ENROLLMENT_KEY_FILE` is populated and the
  agent config includes the correct enrollment key.
- **Shared agent token disabled**: In production mode, `X-Agent-Token` is rejected; use
  per-agent API keys (`X-Agent-Key`).

## Email protection

- **OAuth callback mismatch**: Ensure `APP_BASE_URL` and `PUBLIC_BASE_URL` match the
  externally reachable URL for the service.
