# Frontend (React + Vite + TS)

## Arranque

### Local
```bash
cd frontend
npm ci
npm run dev
```

### Docker
```bash
docker compose up -d --build frontend
```

## Rutas principales (App.tsx)
- `/` Dashboard
- `/login`
- `/alerts`, `/alerts/:alertId`
- `/incidents`, `/incidents/:incidentId`
- `/detections/rules` (Rule Library)
- `/advanced-search` (KQL)
- `/events`
- `/network-security/*` (overview, events, detections, sensors, actions)
- `/email-protection`
- `/email-security`, `/email-security/settings`, `/email-security/threat-intel`
- `/intelligence/*` (dashboard, search, entity, graph, attack, indicators, reports, cases, playbooks, connectors)
- `/admin/users` (solo admin)

## Build / Test
```bash
npm run build
```

```bash
npm test
```

## Convenciones UI
- Estilos principales en `frontend/src/App.css` y componentes en `frontend/src/components/`.
- Contexto de autenticación en `frontend/src/contexts/AuthContext`.

## Troubleshooting (Docker)
**Error de Rollup native packages**
- El Dockerfile instala el paquete nativo correcto para la arquitectura/GLIBC.
- Si el build falla, revisa el log del paso que instala `@rollup/rollup-*`.

```bash
docker compose logs -f --tail=200 frontend
```
