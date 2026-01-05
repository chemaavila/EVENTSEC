# Seguridad

## Secrets y configuración sensible
- **JWT**: usa `SECRET_KEY` o `SECRET_KEY_FILE`.
- **Agentes/ingesta**: usa `EVENTSEC_AGENT_TOKEN` y `AGENT_ENROLLMENT_KEY`.
- **Email Protection**: configura credenciales OAuth en `email_protection/.env`.

## Buenas prácticas mínimas
- No commitear `.env` ni secrets en el repo.
- Rotar `SECRET_KEY` y credenciales OAuth regularmente.
- En producción, habilitar HTTPS:
  - `SERVER_HTTPS_ENABLED=true`
  - `SERVER_SSL_CERTFILE`, `SERVER_SSL_KEYFILE`
- Para mTLS, configura `SERVER_SSL_CA_FILE` y `SERVER_SSL_CLIENT_CERT_REQUIRED=true`.

## Roles y permisos
Roles definidos en backend: `admin`, `team_lead`, `analyst`, `senior_analyst`.

## Endpoints sensibles
- `/auth/login` emite JWT (cookie `access_token`).
- `/ingest/*` y `/agents/*` aceptan `X-Agent-Token`.
