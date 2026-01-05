# Backend (FastAPI)

## Arranque

### Local
```bash
cd backend
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.server
```

### Docker
```bash
docker compose up -d --build backend
```

## Estructura
- `app/main.py`: app FastAPI + routers.
- `app/routers/`: módulos API.
- `app/models.py`: modelos SQLAlchemy.
- `app/crud.py`: acceso a datos.
- `app/auth.py`: JWT y roles.
- `app/search.py`: integración OpenSearch.
- `app/threatmap/`: threat map en tiempo real (WS).
- `app/maintenance.py`: retención diaria (servicio `retention`).

## Endpoints principales
- `/auth/login`, `/auth/logout`
- `/events`, `/alerts`, `/incidents`
- `/rules/detections`
- `/search/kql`
- `/network` y `/ingest/network`
- `/inventory`, `/vulnerabilities`, `/sca`
- `/ws/threatmap`
- `/metrics`
- `/` (health)

## Migraciones (Alembic)

```bash
# crear una nueva migración (ejemplo)
alembic revision -m "add_field" --autogenerate

# aplicar
alembic upgrade head

# revertir una revisión
alembic downgrade -1
```

## Testing
```bash
pytest
```

## Autenticación
- JWT con `SECRET_KEY` (o `SECRET_KEY_FILE`).
- Roles: `admin`, `team_lead`, `analyst`, `senior_analyst`.

## Modelos clave
- `User`, `Alert`, `Incident`, `Workplan`, `Handover` en `app/models.py`.
