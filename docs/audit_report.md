# EVENTSEC Audit Report (PR-ready)

## Arquitectura as-built (según repo)

```mermaid
flowchart LR
  frontend[Frontend (React/Vite)\n:5173] --> backend[Backend (FastAPI)\n:8000]
  backend --> db[(Postgres 15\n:5432)]
  backend --> opensearch[(OpenSearch\n:9200)]
  vuln_worker[Vuln worker\napp.worker] --> db
  retention[Retention job\napp.maintenance] --> db
  ids_collector[IDS collector] --> backend
  opensearch --> backend
  migrate[Migrate service\nalembic upgrade head] --> db
  migrate --> opensearch
```

### Componentes principales
- **Backend**: FastAPI + SQLAlchemy + Alembic, expone API y readiness.  
- **DB**: Postgres 15.  
- **OpenSearch**: índices de eventos/alertas.  
- **Workers**: `vuln_worker` (vulnerabilidades) y `retention`.  
- **Frontend**: React/Vite (consume endpoints `auth`, `alerts`, `inventory`, `vulnerabilities`).  

## Evidencia mínima disponible (repositorio)
- **Worker consulta `software_components`**: `app.worker` filtra `SoftwareComponent.last_seen_at`.  
- **Migración existente**: Alembic `202603120001_vuln_intel_inventory.py` crea `software_components`.  
- **Arranque actual**: el worker usa `entrypoint: ["python", "-m", "app.worker"]`, evitando `entrypoint.sh` (migraciones).  

> Nota: en este entorno no hay Docker disponible, por lo que los comandos de runtime fallan y no se adjuntan logs.

## RCA (hipótesis evaluadas)
- **H1 (migraciones no ejecutadas)**: *Compatible*. El worker no ejecuta migraciones y depende solo de DB healthy.  
- **H2 (DB distinta)**: *No evidenciado*. Compose usa `DATABASE_URL` igual en backend/worker.  
- **H3 (search_path distinto)**: *No evidenciado*. No hay configuración que altere `search_path` en compose.

Conclusión: el fallo es consistente con una carrera donde `vuln_worker` consulta tablas antes de que el backend termine las migraciones.

## Cambios propuestos en este PR
1. **Servicio `migrate`**: ejecuta migraciones antes de backend/workers.  
2. **Readyz**: valida tablas críticas (`software_components`, `asset_vulnerabilities`, `users`, `alembic_version`).  
3. **Worker**: espera esquema requerido y falla con mensaje claro si no está migrado.  
4. **Smoke script**: nuevo `scripts/smoke_compose.sh` valida tabla `software_components`.  
5. **Tests backend**: DB readiness + worker schema + OpenAPI contract mínimo.  
6. **Docs**: actualización de quickstart/troubleshooting.

## Cómo verificar
```bash
docker compose down -v --remove-orphans
docker compose up -d --build
./scripts/smoke_compose.sh
pytest backend/tests
```
