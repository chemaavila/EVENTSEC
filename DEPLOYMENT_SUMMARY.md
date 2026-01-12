# Deployment Summary

## Render (backend)

**Root Directory**: `backend` (recommended) or repo root

**Build Command**:
```
pip install -r requirements.txt
```

**Start Command**:
```
bash -lc 'if [ -d backend ]; then cd backend; fi; export PYTHONPATH=$PWD; alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT'
```

**Required environment variables**:
- `DATABASE_URL`
- `JWT_SECRET` (alias for `SECRET_KEY`)
- `DETECTION_QUEUE_MODE`

**Notes**:
- Ensure database migrations run before the app starts (`alembic upgrade head`).
- Store secrets like `JWT_SECRET`/`SECRET_KEY` and database credentials in Render environment variables.

## Vercel (frontend)

**Root Directory**: `frontend`

**Install Command**:
```
npm ci
```

**Build Command**:
```
npm run build
```

**Output Directory**: `dist`

**Required environment variables**:
- `VITE_API_BASE_URL` (Render backend public URL)
- `VITE_CTI_USE_MOCK=true` (until a CTI API is available)

**Optional environment variables**:
- `VITE_THREATMAP_WS_URL`
- `VITE_EMAIL_PROTECT_BASE_URL`
