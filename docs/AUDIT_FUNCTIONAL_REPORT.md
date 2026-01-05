# EventSec Functional Audit Report

## Executive summary
This audit focused on real app behavior across backend APIs, frontend consumption, and integrations.
The environment lacks Docker tooling, so live system execution was blocked; all findings are based
on code inspection with reproducible commands and a runnable audit script.

**Key P0/P1 findings:**
- **P0**: Alert status default mismatch (`draft` in DB model vs `open|in_progress|closed` in API/TS types), which can cause response model validation failures and UI inconsistencies.
- **P1**: CTI adapter is intentionally unimplemented and throws unless `VITE_CTI_USE_MOCK=true`.

## Environment & execution status
**Attempted commands (blocked):**
- `docker compose down -v --remove-orphans`
- Result: `docker: command not found`

**Impact:** live smoke tests were blocked; commands and expected outputs are still provided below.

## Tested flows (scripted / reproducible)
A minimal audit harness is provided in `scripts/audit/functional_audit.sh` with:
- compose up/down (if Docker is available)
- health checks
- OpenAPI fetch
- login and cookie-based authenticated requests

## API inventory summary
See `docs/API_INVENTORY.md` for the full endpoint list.

## Frontend ↔ backend contract checks
See `docs/FRONTEND_BACKEND_CONTRACT.md` for page-to-API mapping and DTO alignment.

## Findings

### AUD-P0-001 — Alert status default mismatch
- **Impact:** Alerts created outside the `create_alert` code path (or legacy DB rows) can carry status `draft`, which is not allowed by `AlertStatus` (`open|in_progress|closed`). This can cause FastAPI response model validation errors (500) and front-end status handling bugs.
- **Root cause:** `backend/app/models.py` defines `Alert.status` default as `draft`, while schema/types expect `open` (`backend/app/schemas.py`, `frontend/src/services/api.ts`).
- **Repro (expected):**
  1. Create an `Alert` row without explicitly setting status (e.g., admin insert, seed, or ORM default).
  2. Call `GET /alerts` and observe response model validation error (FastAPI logs) or UI status mismatch.
- **Fix:** Align DB model default to `open` (minimal change).
- **Verify:**
  ```bash
  curl -i http://localhost:8000/alerts -b /tmp/eventsec_cookies.txt
  ```

### AUD-P1-001 — CTI adapter is unimplemented
- **Impact:** CTI pages throw `CtiNotImplementedError` when `VITE_CTI_USE_MOCK=false`.
- **Root cause:** `frontend/src/services/cti/apiAdapter.ts` intentionally throws to force mock usage.
- **Repro:**
  1. Set `VITE_CTI_USE_MOCK=false`.
  2. Visit Intelligence pages (e.g. `IntelligenceDashboardPage`).
  3. UI reports “not implemented.”
- **Fix:** Keep mock enabled or implement a real adapter.
- **Verify:**
  ```bash
  VITE_CTI_USE_MOCK=true npm run dev
  ```

## Golden path checklist (manual)
1. Login via UI → Dashboard loads.
2. Alerts list loads → open alert detail.
3. Create alert → appears in list.
4. Create incident from alert → incident appears in list.
5. Logout clears session and returns to `/login`.

## Recommended regression checks
```bash
docker compose down -v --remove-orphans
docker compose up -d --build
docker compose ps
curl -s http://localhost:8000/openapi.json | head
curl -i http://localhost:8000/healthz
curl -i http://localhost:8000/readyz
```
