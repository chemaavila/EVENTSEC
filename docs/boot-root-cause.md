# Root Cause: Docker Compose boot failures (Alembic + collector)

## Resumen técnico (muy detallado)

### 1) Timeline del fallo
1. `docker compose up -d --build` arranca `backend`.
2. `entrypoint.sh` intenta ejecutar `alembic upgrade`.
3. Alembic carga `alembic/env.py` y ejecuta `_load_revisions()`.
4. Alembic usa `importlib` para importar `alembic/versions/*.py`.
5. Una migration corrupta lanza `SyntaxError` durante el import.
6. Alembic aborta antes de construir `revision_map`.
7. Resultado: el backend no inicia la API, `/healthz` y `/readyz` no responden.
8. Consecuencia: el frontend falla con `ERR_CONNECTION_RESET/Failed to fetch`, y los servicios dependientes reinician.

### 2) Causa raíz exacta
- **Migration corrupta**: `202603010001_password_guard.py` contenía una línea inválida con un `\` (interpretado como line continuation), generando `SyntaxError` y bloqueando Alembic.
- **Heads duplicados/duplicated revision**: el revision `202603010001` apareció más de una vez, provocando warnings y potenciales múltiples heads.

### 3) Impacto sistémico
- **Backend**: `unhealthy` porque nunca llega a `uvicorn` ni a endpoints de salud.
- **Frontend**: peticiones a `:8000` fallan (backend no listo).
- **Workers**: dependen de tablas existentes; sin migraciones, entran en restart-loop.
- **ids_collector**: se ejecuta como script top-level y fallaba al resolver imports relativos.

### 4) Fix aplicado
- **Migration saneada**:
  - Se recuperó `202603010001_password_guard.py` eliminando líneas corruptas; no contenía operaciones de schema.
  - Se movió `tenant_id` a `202603010002_add_users_tenant_id.py` para evitar colisiones de revision.
- **Preflight de migrations**: `scripts/check_migrations.py` compila `alembic/versions/*.py` antes de migrar.
- **Alembic head/heads**: el entrypoint detecta múltiples heads y ejecuta `alembic upgrade heads` cuando aplica.
- **Healthcheck fiable**: `/readyz` sólo retorna 200 cuando DB + OpenSearch están accesibles.
- **Collector estable**: se corrigió `tailer.py` para usar imports absolutos.

### 5) Prevención
- **`check_migrations.py`** asegura que migrations no compilables fallen rápido con mensaje claro.
- **`check_collector_imports.py`** valida imports/compilación del collector.
- **Recomendación CI**: añadir `python scripts/check_migrations.py` como gate.

## Comandos de verificación rápida
```bash
docker compose down -v --remove-orphans
docker compose up -d --build

docker compose ps
curl -sSf http://localhost:8000/healthz
curl -sSf http://localhost:8000/readyz
curl -I http://localhost:5173
```
