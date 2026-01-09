# Deployment (dev vs Linux real)

## Dev (Docker Desktop / local)
- Stack por defecto usa **HTTP** en `http://localhost:8000`.
- Frontend usa `VITE_API_BASE_URL` o fallback a `http://localhost:8000`.
- Agente usa `EVENTSEC_AGENT_API_URL` o `api_url` en `agent_config.json` (default HTTP).

```bash
docker compose up -d --build
```

## Linux (captura real IDS)
Para tráfico real del host, habilita `network_mode: host` con el override:

```bash
IDS_INTERFACE=any \
docker compose --profile ids -f docker-compose.yml -f docker-compose.linux-ids.override.yml up -d
```

Detalles en `docs/IDS.md`.

## HTTPS (opcional)
Si usas reverse proxy/HTTPS:
- Backend: `SERVER_HTTPS_ENABLED=true` + certificados (`SERVER_SSL_CERTFILE`, `SERVER_SSL_KEYFILE`).
- Frontend: define `VITE_API_BASE_URL=https://<backend>`.
- Agente: `EVENTSEC_AGENT_API_URL=https://<backend>` y CA en `REQUESTS_CA_BUNDLE`.
