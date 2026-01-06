# PasswordGuard

PasswordGuard integra eventos de detección de credenciales expuestas (HIBP) en EVENTSEC,
crea alertas cuando hay contraseñas comprometidas y ofrece una vista dedicada en el UI
para revisar detecciones, aprobaciones y rotaciones.

## Backend API

### POST `/api/v1/password-guard/events`

Ingesta eventos desde el agente PasswordGuard. Autenticación:

- `Authorization: Bearer <jwt>` (usuarios)
- `X-Agent-Token` (token compartido, fuera de producción)
- `X-Agent-Key` (API key por agente)

Headers opcionales:
- `X-Tenant-Id`: tenant explícito (si no hay JWT con tenant).

```json
{
  "host_id": "workstation-12",
  "user": "alice",
  "entry_id": "vault-42",
  "entry_label": "Okta Admin",
  "exposure_count": 21234,
  "action": "DETECTED",
  "timestamp": "2025-03-20T10:12:04Z",
  "client_version": "0.1.0"
}
```

- Si `action == DETECTED` y `exposure_count > 0`, se crea una alerta
  (`severity=high`, `title="Pwned password detected"`).
- Se registra un audit trail con `token_id`, `ip_address` y actor.
- Rate limit por `host_id` (configurable con `PASSWORD_GUARD_RATE_LIMIT_PER_MINUTE`).

### GET `/api/v1/password-guard/events`

Filtros:

```
tenant_id=default
host_id=workstation-12
user=alice
action=DETECTED
from=2025-03-01T00:00:00Z
to=2025-03-31T23:59:59Z
```

### GET `/api/v1/password-guard/alerts`

Lista de alertas originadas por PasswordGuard (con vínculo al evento).

## UI

Ruta: `/passwordguard`.

Incluye:
- Tabla de eventos recientes con alertas enlazadas.
- Filtros por host, usuario, acción y rango de fechas.
- Drawer con línea de tiempo de aprobaciones y rotaciones.

## Integración rápida del agente

Ejemplo básico (curl):

```bash
curl -X POST http://localhost:8000/api/v1/password-guard/events \
  -H "Content-Type: application/json" \
  -H "X-Agent-Token: <token>" \
  -d '{"host_id":"host-1","user":"alice","entry_id":"vault-1","entry_label":"Okta","exposure_count":12,"action":"DETECTED","timestamp":"2025-03-20T10:12:04Z","client_version":"0.1.0"}'
```

El agente PasswordGuard (vault + monitor + rotación con consentimiento) se entregará en
PRs posteriores siguiendo la arquitectura definida para el binario Go.
