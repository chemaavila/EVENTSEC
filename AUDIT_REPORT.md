# EventSec Technical Audit Report (Draft)

## Scope
Backend (FastAPI/SQLAlchemy/Alembic), Frontend (React/Vite/TS), Infra (Docker/Compose), Docs.

## Executive summary
EventSec is operational but has a few P0 risks around frontend container builds (Rollup native
optional dependencies) and ORM relationship consistency across models with multiple FKs. The
current Docker/Compose setup benefits from healthchecks and stricter dependency installs for
reproducibility. Documentation exists but is scattered; consolidating troubleshooting and ORM
conventions is required for durability.

## Findings

### P0 (must fix)
1) **Frontend Docker build is fragile across arch/libc**
   - **Root cause**: Rollup relies on platform-specific optional dependencies; Docker builds may
     skip these or resolve for the wrong platform.
   - **Action**: Use `npm ci --include=optional`, detect platform/libc, install the correct
     Rollup native module, and perform a fail-fast `require()` during build.
   - **Risk**: Build failures in CI on linux/arm64 vs linux/x64; flaky `vite build`.

2) **ORM relationships with multiple FKs need explicit symmetry**
   - **Root cause**: Models like `Alert` and `Incident` reference `users.id` multiple times and
     lack symmetric `back_populates` on both sides, leading to ambiguity in mappers.
   - **Action**: Add `back_populates` and explicit `foreign_keys` on both sides; add a CRUD test
     that exercises relationships.
   - **Risk**: Runtime mapper errors and hard-to-debug query issues.

3) **Backend readiness/liveness endpoints missing**
   - **Root cause**: No standardized `/healthz` or `/readyz` endpoints for container healthchecks.
   - **Action**: Add `/healthz` (liveness) and `/readyz` (DB + OpenSearch readiness).
   - **Risk**: Unreliable healthchecks and opaque startup failures.

### P1 (should fix)
1) **Docker Compose health visibility**
   - **Root cause**: DB/backend/frontend healthchecks are not consistently defined.
   - **Action**: Add healthchecks for Postgres and backend root, and make service dependencies
     wait for health.
   - **Risk**: Harder troubleshooting and nondeterministic startup ordering.

2) **Documentation gaps**
   - **Root cause**: Troubleshooting guidance and ORM conventions are not centralized.
   - **Action**: Add `docs/TROUBLESHOOTING.md` and `docs/DEV_GUIDE.md`.

### P2 (nice to have)
1) **Frontend style system and routing hygiene**
   - **Root cause**: Ad-hoc class naming and scattered routing logic.
   - **Action**: Introduce design tokens, align CSS naming, and centralize routing configuration.

2) **Observability and security hardening**
   - **Root cause**: Logging and health endpoints are not fully standardized.
   - **Action**: Add structured logging, correlation IDs, and `/healthz`/`/readyz` endpoints.

## Backlog
| Priority | Area | Item | Impact | Effort |
| --- | --- | --- | --- | --- |
| P1 | Backend | Add structured logging + correlation IDs | Medium | M |
| P1 | Frontend | Design tokens + base components | Medium | M |
| P2 | Infra | OpenSearch index templates for alerts/incidents | Medium | M |
| P2 | Docs | Full architecture + runbooks | Medium | M |
