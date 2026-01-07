# Configuración (.env)

> Referencia directa de variables usadas en el código y `docker-compose.yml`.

## Backend (`backend/.env`)
Usa `backend/.env.example` como base.

| Variable | Servicio | Requerida | Default | Ejemplo | Descripción |
| --- | --- | --- | --- | --- | --- |
| `ENVIRONMENT` | backend | No | `development` | `development` | Entorno de ejecución. |
| `DATABASE_URL` | backend | No | `postgresql+psycopg2://eventsec:eventsec@localhost:5432/eventsec` | `postgresql+psycopg2://eventsec:eventsec@db:5432/eventsec` | Conexión a Postgres. |
| `SECRET_KEY` | backend | No* | `eventsec-dev-secret` | `changeme` | Clave JWT (usa `SECRET_KEY_FILE` en prod). |
| `SECRET_KEY_FILE` | backend | No | - | `/run/secrets/jwt_secret.txt` | Ruta a archivo de secreto JWT. |
| `AGENT_ENROLLMENT_KEY` | backend | No | `eventsec-enroll` | `eventsec-enroll` | Clave de enrolamiento de agentes. |
| `AGENT_ENROLLMENT_KEY_FILE` | backend | No | - | `/run/secrets/agent_enrollment_key.txt` | Archivo de enrolamiento. |
| `EVENTSEC_AGENT_TOKEN` | backend | No | random/`eventsec-dev-token` | `eventsec-dev-token` | Token compartido para ingest. |
| `OPENSEARCH_URL` | backend | No | `http://localhost:9200` | `http://opensearch:9200` | URL OpenSearch. |
| `OPENSEARCH_VERIFY_CERTS` | backend | No | `true` | `true` | Verificar certificados TLS. |
| `OPENSEARCH_CA_FILE` | backend | No | - | `/certs/ca.pem` | CA para OpenSearch. |
| `OPENSEARCH_CLIENT_CERTFILE` | backend | No | - | `/certs/client.crt` | Cert cliente. |
| `OPENSEARCH_CLIENT_KEYFILE` | backend | No | - | `/certs/client.key` | Key cliente. |
| `OPENSEARCH_MAX_RETRIES` | backend | No | `3` | `3` | Reintentos para OpenSearch. |
| `OPENSEARCH_RETRY_BACKOFF_SECONDS` | backend | No | `0.5` | `0.5` | Backoff OpenSearch. |
| `SERVER_HOST` | backend | No | `127.0.0.1` | `0.0.0.0` | Host del servidor. |
| `SERVER_PORT` | backend | No | `8000` | `8000` | Puerto del servidor. |
| `SERVER_HTTPS_ENABLED` | backend | No | `false` | `true` | Habilita HTTPS. |
| `SERVER_SSL_CERTFILE` | backend | No | - | `/certs/server.crt` | Cert servidor. |
| `SERVER_SSL_KEYFILE` | backend | No | - | `/certs/server.key` | Key servidor. |
| `SERVER_SSL_CA_FILE` | backend | No | - | `/certs/ca.pem` | CA para mTLS. |
| `SERVER_SSL_CLIENT_CERT_REQUIRED` | backend | No | `false` | `true` | Requiere cert cliente. |
| `MANAGER_EMAILS` | backend | No | `""` | `soc-manager@example.com` | Destinatarios para alertas. |
| `LEVEL1_DL` | backend | No | `""` | `soc-l1@example.com` | DL nivel 1. |
| `LEVEL2_DL` | backend | No | `""` | `soc-l2@example.com` | DL nivel 2. |
| `UI_BASE_URL` | backend | No | `http://localhost:5173` | `http://localhost:5173` | URL base UI (notificaciones). |
| `NOTIFICATION_DEDUP_MINUTES` | backend | No | `2` | `2` | Ventana de deduplicación. |
| `NETWORK_INGEST_MAX_EVENTS` | backend | No | `1000` | `1000` | Límite de eventos por ingest. |
| `NETWORK_INGEST_MAX_BYTES` | backend | No | `5000000` | `5000000` | Límite de bytes por ingest. |
| `EVENT_QUEUE_MAXSIZE` | backend | No | `2000` | `2000` | Cola interna de eventos. |
| `INCIDENT_AUTO_CREATE_ENABLED` | backend | No | `true` | `true` | Auto-crear incidentes. |
| `INCIDENT_AUTO_CREATE_MIN_SEVERITY` | backend | No | `high` | `high` | Severidad mínima. |
| `TELEMETRY_MODE` | backend | No | `live` | `mock` | Threat map live/mock. |
| `MAXMIND_DB_PATH` | backend | No | - | `/data/GeoIP.mmdb` | DB GeoIP. |
| `THREATMAP_REPLAY_SECONDS` | backend | No | `60` | `60` | Ventana de replay. |
| `THREATMAP_TTL_MS` | backend | No | `45000` | `45000` | TTL de puntos. |
| `THREATMAP_AGG_TICK_MS` | backend | No | `1000` | `1000` | Intervalo de agregación. |
| `THREATMAP_HB_TICK_MS` | backend | No | `2000` | `2000` | Intervalo de heartbeat. |
| `MIGRATION_ATTEMPTS` | backend | No | `10` | `10` | Reintentos de Alembic en entrypoint. |
| `EVENTSEC_DB_DEBUG` | backend | No | `0` | `1` | Imprime diagnósticos del target DB durante migraciones/seed. |
| `SEED_SKIP_ON_ERROR` | backend | No | `0` | `1` | Permite continuar si el seed detecta tablas faltantes. |
| `VULN_INTEL_ENABLED` | backend | No | `true` | `true` | Habilita el pipeline de vuln intel. |
| `VULN_INTEL_WORKER_ROLE` | backend | No | `api` | `worker` | Rol para scheduler (`api`/`worker`). |
| `NVD_API_KEY` | backend | No | - | `...` | API key para NVD. |
| `NVD_BASE_URL` | backend | No | `https://services.nvd.nist.gov/rest/json/cves/2.0` | idem | Base URL NVD CVE. |
| `NVD_CPE_BASE_URL` | backend | No | `https://services.nvd.nist.gov/rest/json/cpes/2.0` | idem | Base URL NVD CPE. |
| `OSV_BASE_URL` | backend | No | `https://api.osv.dev/v1/query` | idem | Base URL OSV query. |
| `OSV_BATCH_URL` | backend | No | `https://api.osv.dev/v1/querybatch` | idem | Base URL OSV batch. |
| `EPSS_BASE_URL` | backend | No | `https://api.first.org/data/v1/epss` | idem | Base URL EPSS. |
| `VULN_INTEL_HTTP_TIMEOUT_SECONDS` | backend | No | `15` | `15` | Timeout HTTP. |
| `VULN_INTEL_HTTP_RETRIES` | backend | No | `3` | `3` | Reintentos HTTP. |
| `VULN_INTEL_CACHE_TTL_HOURS` | backend | No | `24` | `24` | TTL cache. |
| `VULN_INTEL_NOTIFY_IMMEDIATE_MIN_RISK` | backend | No | `CRITICAL` | `CRITICAL` | Umbral notificación inmediata. |
| `VULN_INTEL_NOTIFY_DIGEST_ENABLED` | backend | No | `true` | `true` | Habilita digest diario. |
| `VULN_INTEL_NOTIFY_DIGEST_HOUR_LOCAL` | backend | No | `9` | `9` | Hora digest (local). |
| `VULN_INTEL_TIMEZONE` | backend | No | `Europe/Madrid` | `Europe/Madrid` | Zona horaria digest. |
| `VULN_INTEL_CREATE_ALERTS_FOR_CRITICAL` | backend | No | `true` | `true` | Crear alertas para CRITICAL/KEV. |

\* Requerida en producción (no usar defaults).

## Frontend (`frontend/.env`)
Usa `frontend/.env.example` como base.

| Variable | Servicio | Requerida | Default | Ejemplo | Descripción |
| --- | --- | --- | --- | --- | --- |
| `VITE_API_BASE_URL` | frontend | No | derivado | `http://localhost:8000` | URL API backend. |
| `VITE_THREATMAP_WS_URL` | frontend | No | derivado | `ws://localhost:8000/ws/threatmap` | WebSocket threat map. |
| `VITE_EMAIL_PROTECT_BASE_URL` | frontend | No | derivado | `http://localhost:8100` | Email Protection API. |
| `VITE_CTI_USE_MOCK` | frontend | No | `true` | `true` | Mock de CTI. |
| `VITE_UI_DEBUG` | frontend | No | `false` | `false` | Logs de UI. |
| `VITE_THREATMAP_STALE_MS` | frontend | No | `10000` | `10000` | Umbral stale. |

## Email Protection (`email_protection/.env`)
Usa `email_protection/.env.example` como base.

| Variable | Servicio | Requerida | Default | Ejemplo | Descripción |
| --- | --- | --- | --- | --- | --- |
| `EMAIL_PROTECT_APP_BASE_URL` | email_protection | No | `http://localhost:8100` | `http://localhost:8100` | Base URL interna. |
| `EMAIL_PROTECT_PUBLIC_BASE_URL` | email_protection | No | `http://localhost:8100` | `http://localhost:8100` | Base URL pública. |
| `EMAIL_PROTECT_GOOGLE_CLIENT_ID` | email_protection | Sí | - | `...` | OAuth client ID Gmail. |
| `EMAIL_PROTECT_GOOGLE_CLIENT_SECRET` | email_protection | Sí | - | `...` | OAuth secret Gmail. |
| `EMAIL_PROTECT_GOOGLE_REDIRECT_URI` | email_protection | No | `http://localhost:8100/auth/google/callback` | idem | Redirect Gmail. |
| `EMAIL_PROTECT_GMAIL_PUBSUB_TOPIC` | email_protection | No | - | `projects/.../topics/...` | Pub/Sub Gmail. |
| `EMAIL_PROTECT_MS_CLIENT_ID` | email_protection | Sí | - | `...` | OAuth client ID M365. |
| `EMAIL_PROTECT_MS_CLIENT_SECRET` | email_protection | Sí | - | `...` | OAuth secret M365. |
| `EMAIL_PROTECT_MS_TENANT` | email_protection | No | `common` | `common` | Tenant M365. |
| `EMAIL_PROTECT_MS_REDIRECT_URI` | email_protection | No | `http://localhost:8100/auth/microsoft/callback` | idem | Redirect M365. |
| `EMAIL_PROTECT_TOKEN_DB_PATH` | email_protection | No | `tokens.db` | `tokens.db` | SQLite tokens. |

> En `email_protection/.env.example` existen aliases legacy sin prefijo `EMAIL_PROTECT_`.

## Docker Compose (.env en raíz)
`docker-compose.yml` lee variables del entorno del host. Opcionales:
- `OPENSEARCH_INITIAL_ADMIN_PASSWORD`
- `SERVER_HTTPS_ENABLED`, `SERVER_SSL_CERTFILE`, `SERVER_SSL_KEYFILE`, `SERVER_SSL_CA_FILE`, `SERVER_SSL_CLIENT_CERT_REQUIRED`
- `EVENTSEC_AGENT_TOKEN`
- `RETENTION_DAYS`
