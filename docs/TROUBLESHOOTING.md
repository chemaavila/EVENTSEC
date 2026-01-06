# Troubleshooting & Quick Fixes

## Quick Fixes (Known Issues)

### Backend fails on `users.tenant_id` during migrations
**Symptom**: Alembic upgrade fails with `column "tenant_id" of relation "users" does not exist`.

**Cause**: The `users` table was created without `tenant_id` while seed data referenced it.

**Fix**:
- Run migrations after pulling the latest changes.
- Ensure seeding runs after migrations:
  ```bash
  EVENTSEC_SEED=1 docker compose up -d --build
  ```

### Suricata fails with missing capabilities or config errors
**Symptom**: Logs show `sys_nice`/`net_admin` capability errors or `af-packet: Problem with config file`.

**Fix**:
- Ensure the Suricata service includes `NET_ADMIN`, `NET_RAW`, and `SYS_NICE`.
- Confirm the config and rules are mounted under `/etc/suricata`.
- On Docker Desktop (macOS/Windows), packet capture limitations may prevent live traffic capture.

### Frontend Vitest failures
**Common causes**:
- Invalid `Response` construction for 204/205 tests.
- WebSocket URL resolution not honoring overrides.
- Components using `useNavigate` rendered without a `Router`.
- Multiple elements with identical text content.

**Fix**:
- Run `npm test` from `frontend/` and ensure mocks wrap Router usage.
- Prefer `data-testid` for deterministic row and drawer selections.

## Resetting the dev environment
If you want a clean start:
```bash
docker compose down -v --remove-orphans
```

## How to validate a clean install
```bash
docker compose down -v --remove-orphans
docker compose up -d --build
./scripts/smoke.sh
```

Expected results:
- `smoke.sh` reports backend readiness and returns 0.
- `/readyz` returns `{"ok": true, ...}`.
- Frontend responds on `http://localhost:5173/`.

## Useful commands
- Backend readiness:
  ```bash
  curl -s http://localhost:8000/readyz
  ```
- Backend OpenAPI:
  ```bash
  curl -s http://localhost:8000/openapi.json | head
  ```
- Frontend:
  ```bash
  curl -s http://localhost:5173/
  ```

## Alembic migration verification
From `backend/`:
```bash
alembic heads
alembic history --verbose
```

Expected:
- Exactly one head.
- The latest revision should follow the full chain ending in the tenant_id migration.

## Compose project naming (avoid container collisions)
If you run multiple stacks on the same host, set a project name:
```bash
export COMPOSE_PROJECT_NAME=eventsec
```

You can also place this in a local `.env` file to make it persistent.
