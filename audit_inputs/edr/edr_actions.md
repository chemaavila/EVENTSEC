# EDR Actions (según repo)

Fuentes: `backend/app/main.py`, `agent/agent.py`.

## Acciones soportadas
- `isolate` (aislar host)
- `release` (remover aislamiento)
- `reboot`
- `command` (ejecutar comando remoto, simulado)

## UI/API (backend)
- Crear acción: `POST /endpoints/{endpoint_id}/actions`
  - Payload: `EndpointActionCreate` (`action_type`, `parameters`)
- Consultar acciones por endpoint: `GET /endpoints/{endpoint_id}/actions`
- Agente obtiene acciones pendientes: `GET /agent/actions?hostname=...`
- Agente completa acción: `POST /agent/actions/{action_id}/complete`

## Ejecución del agente (simulada)
- `agent/agent.py` → `process_actions()` ejecuta acciones de forma simulada y responde con `output`.

## Guardrails / auditoría
- Se registra acción con `log_action()` en `backend/app/main.py` al crear la acción.
- Sin workflow de aprobaciones ni allowlist explícita en el canal de management (requiere instrumentación adicional).
