# EventSec Development Guide

## Supported runtimes (compatibility contract)

The repo currently pins and/or expects the following runtime majors:

- Python **3.11** (Docker images and CI use Python 3.11).
- Node.js **20** (frontend Dockerfile and CI use Node 20).

If you change these versions, update Dockerfiles, CI workflows, and this guide together.

## Local setup (macOS/Linux)

### Backend (FastAPI)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
alembic upgrade head
export OPENSEARCH_URL="http://localhost:9200"
export SECRET_KEY_FILE=./secrets/jwt_secret.txt
export AGENT_ENROLLMENT_KEY_FILE=./secrets/agent_enrollment_key.txt
python -m app.server
```

### Frontend (Vite)

```bash
cd frontend
npm ci
npm run dev
```

### Agent (CLI/desktop)

```bash
cd agent
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m agent
```

### Email protection service

```bash
cd email_protection
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8100
```

### Scanner (protoxol triage)

```bash
cd protoxol_triage_package
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python protoxol_triage.py
```

## Docker Compose quickstart

```bash
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

## Environment variables

See `backend/app/config.py` for backend runtime settings and `email_protection/.env.example`
for the email protection service.
