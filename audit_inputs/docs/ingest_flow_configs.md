# Ingest Flow Configs (reales en repo)

Fuentes: `docker-compose.yml`, `backend/app/config.py`, `backend/app/search.py`.

## Servicios y puertos
- Backend FastAPI: `backend` expone `8000:8000` (docker-compose).
- OpenSearch: `opensearch` expone `9200:9200` (docker-compose).
- Postgres: `db` expone `5432:5432` (docker-compose).

## TLS/Auth
- Backend configura TLS opcional via `SERVER_HTTPS_ENABLED`, `SERVER_SSL_CERTFILE`, `SERVER_SSL_KEYFILE` (`backend/app/config.py`, docker-compose env).
- OpenSearch: conexión configurable con `opensearch_url` y opciones de TLS (`opensearch_verify_certs`, `opensearch_ca_file`, `opensearch_client_certfile`, `opensearch_client_keyfile`) en `backend/app/config.py`.
- Ingest `/events` requiere `X-Agent-Key` o `X-Agent-Token` (shared) según `backend/app/routers/events_router.py`.

## Retries / Backpressure
- Cola async de eventos con tamaño `EVENT_QUEUE_MAXSIZE` (env var) y métricas de retries/drops (`backend/app/main.py`, `backend/app/metrics.py`).
- OpenSearch reintentos con backoff (`opensearch_max_retries`, `opensearch_retry_backoff_seconds`) en `backend/app/search.py`.

## DLQ / Replay / Idempotencia
- DLQ y replay no están implementados en el código actual.
- Idempotencia/dedupe explícita no está implementada.
