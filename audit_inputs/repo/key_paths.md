# Rutas clave (repo)

## Ingest/Collector
- `backend/app/routers/events_router.py` (POST /events ingest)
- `agent/agent.py` (send_event, logcollector)

## Normalización / Enrichment
- `backend/app/main.py` -> `process_event_queue()` (construye doc indexado; normalización básica).
- `backend/app/search.py` (indexación OpenSearch + raw/dlq indices)

## Storage / Index
- `backend/app/search.py` (OpenSearch client + ensure_indices + index_event/index_alert)
- `backend/app/models.py` (SQLAlchemy models de Event, Alert, Endpoint, etc.)

## Rules Engine / Scheduler
- `backend/app/routers/rules_router.py` (CRUD de reglas de detección)
- `backend/app/main.py` -> `process_event_queue()` (evalúa reglas y crea alertas básicas)
- `backend/app/data/detection_rules.json` (seed mínimo)

## KQL Runner + Auth/RBAC
- `backend/app/routers/kql_router.py` (POST /search/kql)
- `backend/app/kql.py` (parser KQL→OpenSearch)
- `backend/app/auth.py` (auth helpers)

## UI Query Editor
- `frontend/src/pages/AdvancedSearchPage.tsx`
- `frontend/src/services/api.ts` (POST /search/kql)
- `frontend/src/App.css` (estilos workbench)

## Case/Alert Management
- `backend/app/main.py` (endpoints /alerts, /workplans, /warroom, actions)
- `frontend/src/pages/AlertsPage.tsx` (si aplica)

## Audit Logging
- `backend/app/main.py` -> `log_action()` y endpoints de acciones (ej. /alerts/{id}/isolate-device)
- `backend/app/models.py` (`ActionLog`)

## Scripts de Evidence Pack
- `scripts/build_audit_pack.sh` (comando único)
- `scripts/audit/export_opensearch_schema.py`
- `scripts/audit/export_event_samples.py`
- `scripts/audit/generate_mapping.py`
- `scripts/audit/export_rules.py`
- `scripts/audit/export_metrics.py`
- `scripts/audit/export_edr_audit_logs.py`
- `scripts/audit/validate_audit_pack.py`
