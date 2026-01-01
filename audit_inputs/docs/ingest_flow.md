# Ingest Flow (collector → parser → storage → rules)

Fuente: `backend/app/routers/events_router.py`, `backend/app/main.py`, `backend/app/search.py`, `docker-compose.yml`.

```mermaid
sequenceDiagram
  participant AG as Agent/Source
  participant API as FastAPI /events
  participant DB as Postgres (events table)
  participant Q as Event Queue (asyncio)
  participant OS as OpenSearch (events-v1)
  participant RULE as Rules Engine (stub)

  AG->>API: POST /events (SecurityEventCreate)
  API->>DB: crud.create_event (models.Event)
  API->>Q: enqueue event.id
  Q->>RULE: list_detection_rules (stub)
  Q->>OS: index_event (events-v1)
```

Notas:
- La normalización actual ocurre en `process_event_queue()` construyendo el `doc` indexado (no hay parser dedicado ni transformaciones declarativas).
- El motor de reglas consulta la lista de reglas (`crud.list_detection_rules`) pero no aplica lógica de detección en el código actual.
- OpenSearch índices definidos en `search.ensure_indices()` con mappings básicos.
