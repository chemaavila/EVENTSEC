# Setup local (backend + frontend)

## Requisitos
- **Python 3.11** (`.python-version`)
- **Node.js 20** (`.nvmrc`)
- **Postgres 15** y **OpenSearch 2.12.0** (locales o vía Docker)

> Para variables de entorno, consulta [`07-configuration.md`](07-configuration.md).

## Backend (FastAPI)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### Variables de entorno
Copia el ejemplo y ajusta si es necesario:

```bash
cp .env.example .env
```

### Migraciones (Alembic)

```bash
alembic upgrade head
```

### Arranque

```bash
python -m app.server
```

La API quedará en `http://localhost:8000` (Swagger en `/docs`).

## Frontend (React + Vite)

```bash
cd frontend
npm ci
npm run dev
```

El frontend quedará en `http://localhost:5173`.

## Servicios de soporte
Si no ejecutas Postgres/OpenSearch en local, levántalos con Docker:

```bash
docker compose up -d db opensearch
```

> **Linux:** OpenSearch requiere `vm.max_map_count >= 262144`.

