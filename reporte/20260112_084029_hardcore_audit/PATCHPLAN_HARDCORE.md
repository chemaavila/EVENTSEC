# PATCHPLAN_HARDCORE

## Commit 1: fix(test): corregir import en test_notifications
- Archivos: backend/tests/test_notifications.py
- Cambio: importar get_agent_shared_token desde backend.app.auth o re-exportarlo desde backend.app.main
- Test: pytest

## Commit 2: chore(frontend): añadir script lint
- Archivos: frontend/package.json
- Cambio: agregar script "lint" (ej. eslint)
- Test: npm run lint

## Commit 3: chore(frontend): ajustar vitest para CI
- Archivos: frontend/package.json
- Cambio: script "test" con --run --watch=false o crear script "test:ci"
- Test: npm run test:ci

## Commit 4: docs(runbook): aclarar requerimientos de Docker/Node
- Archivos: README.md, RUNBOOK_LOCAL_EVENTSEC_ES_HARDCORE.txt
- Cambio: documentar versiones requeridas y prerequisitos
- Test: N/A

## Commit 5: feat(debug): instrumentación detrás de EVENTSEC_DEBUG (si se requiere)
- Archivos: backend/app/routers/events_router.py, backend/app/main.py, backend/app/search.py
- Cambio: logs mínimos (ingest, persistencia, indexado, lectura) con guardas EVENTSEC_DEBUG
- Test: EVENTSEC_DEBUG=1 pytest o smoke test con synthetic telemetry
