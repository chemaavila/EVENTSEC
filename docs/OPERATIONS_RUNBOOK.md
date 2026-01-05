# EventSec Operations Runbook

## Startup order expectations
1. **db** and **opensearch** must be healthy.
2. **backend** starts once DB/OpenSearch are healthy.
3. **frontend** and **email_protection** wait on backend health.
4. **retention** waits on backend + db + opensearch health.

Use:
```bash
docker compose ps
```

## Health endpoints
- **/healthz**: liveness (always 200, no DB/OpenSearch calls)
- **/readyz**: readiness (checks DB + OpenSearch, returns 200 or 503)

Smoke tests:
```bash
curl -i http://localhost:8000/healthz
curl -i http://localhost:8000/readyz
```

## Service roles
- **opensearch**: search and analytics datastore (single-node by default).
- **db**: PostgreSQL for core relational data.
- **backend**: FastAPI API server.
- **frontend**: Vite dev server serving the UI.
- **email_protection**: email ingestion pipeline.
- **retention**: scheduled retention/maintenance worker.
- **ids stack**: Suricata + Zeek + ids_collector (optional `ids` profile).

## Logs and rotation
Core services use Docker `json-file` logging with rotation:
- max size: 10 MB
- max files: 3

To view logs:
```bash
docker compose logs -f --tail=200 backend frontend
```

## Shutdown / upgrade
- Clean shutdown:
  ```bash
  docker compose down
  ```
- Clean shutdown with volumes reset (dev only):
  ```bash
  docker compose down -v
  ```
- Upgrade images and rebuild:
  ```bash
  docker compose pull
  docker compose up -d --build
  ```

## Diagnostics
- Inspect container health:
  ```bash
  docker inspect --format '{{json .State.Health}}' eventsec_backend | jq
  ```
- Check DB connectivity from backend container:
  ```bash
  docker exec -it eventsec_backend python -c "import psycopg2; psycopg2.connect('host=db dbname=eventsec user=eventsec password=eventsec')"
  ```
- Check OpenSearch connectivity from backend container:
  ```bash
  docker exec -it eventsec_backend python -c "import urllib.request; print(urllib.request.urlopen('http://opensearch:9200').status)"
  ```
