# EDR RBAC (según repo)

Fuentes: `backend/app/auth.py`, `backend/app/main.py`, `backend/app/routers/agents_router.py`.

## Controles observados
- Endpoints de acciones (`POST /endpoints/{endpoint_id}/actions`) requieren `get_current_user` (usuario autenticado).
- Listado de agentes (`GET /agents`) requiere `get_current_admin_user`.
- Autenticación de agentes usa `X-Agent-Key` o `X-Agent-Token` (bootstrap) en `agents_router` y `events_router`.

## NO DISPONIBLE
- Matriz detallada de permisos por rol para acciones (kill/isolate/etc.).
- Aprovals (human-in-the-loop).
- Separación multi-tenant.
