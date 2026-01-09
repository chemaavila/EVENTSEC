# EVENTSEC

EVENTSEC es una plataforma SOC unificada (SIEM + EDR + seguridad de red + protección de email) con
backend FastAPI, frontend React/Vite y servicios de soporte como OpenSearch y Postgres. Incluye
flujos de alertas/incidentes, gestión de usuarios, workplans y telemetría en tiempo real.

## Quickstart (Docker, 5–10 min)

**Requisitos:** Docker + Docker Compose.

```bash
git clone https://github.com/chemaavila/EVENTSEC.git
cd EVENTSEC

docker compose down -v --remove-orphans
docker compose up -d --build
```

> **Linux:** OpenSearch necesita `vm.max_map_count >= 262144`.
> ```bash
> sudo sysctl -w vm.max_map_count=262144
> ```
> **GeoIP (opcional):** monta un MaxMind/GeoLite2 DB en `infra/geoip/GeoLite2-City.mmdb` y define `MAXMIND_DB_PATH`.
> Si no hay DB, puedes activar coordenadas deterministas con `THREATMAP_FALLBACK_COORDS=true`.
> **OpenSearch healthcheck:** usa `curl`/`wget` dentro del contenedor; si tu imagen no lo trae, usa una imagen custom o instala una de ellas.
> **Nota (dev):** el frontend puede arrancar aunque el backend no esté healthy,
> para facilitar el diagnóstico en UI.
> **Detecciones:** por defecto la cola de detección es en memoria (`DETECTION_QUEUE_MODE=memory`).
> Para persistencia básica usa `DETECTION_QUEUE_MODE=db` o `DETECTION_QUEUE_MODE=inline` en dev.

### Migraciones
El backend ejecuta `alembic upgrade head` y el seed en su entrypoint antes de arrancar la API. Si necesitas ejecutarlo manualmente:

Verificación rápida de `alembic_version` (debe devolver un valor no nulo):
```bash
docker compose exec -T db psql -U eventsec -d eventsec -c "SELECT to_regclass('public.alembic_version') AS alembic_version;"
```

Si necesitas ejecutar Alembic manualmente:
```bash
docker compose exec backend alembic upgrade head
```

> **Nota:** evita ejecutar `docker compose ...` dentro de un contenedor.

#### Diagnóstico rápido (zsh-safe)
```bash
python - <<'PY'
import os
from sqlalchemy import create_engine, text

engine = create_engine(os.environ["DATABASE_URL"])
with engine.connect() as conn:
    print(conn.execute(text("SELECT current_database(), current_user, current_setting('search_path')")).all())
    print(conn.execute(text("SELECT to_regclass('alembic_version'), to_regclass('users')")).all())
PY
```

### URLs / Puertos
- Frontend: http://localhost:5173
- Backend (API + Swagger): http://localhost:8000/docs
- OpenSearch: http://localhost:9200
- Postgres: localhost:5432
- Email Protection: http://localhost:8100

### Retención
El servicio `retention` usa `RETENTION_DAYS` (por defecto 30 días en dev). Recomendación:
- **Dev:** 30 días.
- **Prod:** 90 días (o según política SOC).

### OpenSearch (v2 índices)
Los índices de eventos/alertas usan alias (`events`, `alerts`) apuntando a `events-v2`/`alerts-v2`.
- **Dev:** puedes eliminar `events-v1`/`alerts-v1` y recrear desde cero.
- **Prod:** realiza reindex o migración controlada antes de cambiar alias.

Frontend (Vite) usa `VITE_API_BASE_URL`. En dev, si no se define, apunta a `http://localhost:8000`.
Para despliegues detrás de proxy HTTPS, define explícitamente el backend:
```bash
cat > frontend/.env <<'EOF'
VITE_API_BASE_URL=http://localhost:8000
EOF
```

### Agent (terminal-only, recomendado)
Ejecuta el agente desde la raíz del repo para evitar errores de importación:
```bash
python -m venv agent/.venv && source agent/.venv/bin/activate
export PYTHONPATH=$(pwd)
EVENTSEC_AGENT_API_URL=http://localhost:8000 \
EVENTSEC_AGENT_AGENT_ID=3 \
EVENTSEC_AGENT_AGENT_API_KEY=<key> \
python -m agent
```

> **Nota:** el agente usa HTTP por defecto en entornos locales (sin HTTPS).
> Los eventos SIEM/EDR se almacenan en Postgres y se indexan en OpenSearch;
> la vista SIEM/EDR consulta el alias `events`.

Evidencia en DB (últimos agentes y eventos):
```bash
docker exec -i eventsec-db-1 psql -U eventsec -d eventsec -c "select id,name,last_seen from agents order by id desc limit 5;"
docker exec -i eventsec-db-1 psql -U eventsec -d eventsec -c "select event_type, details->>'hostname', created_at from events order by created_at desc limit 5;"
```

### PasswordGuard (agente)
Consulta la guía rápida en [`docs/passwordguard.md`](docs/passwordguard.md) para:
- Formato de eventos y autenticación del endpoint `/api/v1/password-guard/events`.
- Alertas generadas automáticamente por contraseñas comprometidas.
- Vista en UI: `/passwordguard`.

### Health checks rápidos
```bash
docker compose ps
```

```bash
docker compose logs -f --tail=200 backend
```

```bash
docker compose logs -f --tail=200 ids_collector
```

```bash
docker compose logs -f --tail=200 vuln_worker
```

```bash
curl http://localhost:8000/
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz
curl http://localhost:8100/health
```

### Smoke checks
```bash
./scripts/smoke.sh
```

Smoke end-to-end con reinicio completo y verificación de tablas:
```bash
./scripts/smoke_compose.sh
```

Smoke end-to-end con telemetría de agente + IOC + triage:
```bash
./scripts/smoke_end_to_end.sh
```

## Documentación

La guía completa está en `/docs`:
- **Empieza aquí:** [`docs/00-index.md`](docs/00-index.md)
- Setup local: [`docs/01-setup-local.md`](docs/01-setup-local.md)
- Setup Docker: [`docs/02-setup-docker.md`](docs/02-setup-docker.md)
- Arquitectura: [`docs/03-architecture.md`](docs/03-architecture.md)
- Workflows (alertas/incidentes): [`docs/04-workflows.md`](docs/04-workflows.md)
- Backend: [`docs/05-backend.md`](docs/05-backend.md)
- Frontend: [`docs/06-frontend.md`](docs/06-frontend.md)
- Configuración (.env): [`docs/07-configuration.md`](docs/07-configuration.md)
- Deployment: [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)
- IDS: [`docs/IDS.md`](docs/IDS.md)
- Threat Map: [`docs/THREATMAP.md`](docs/THREATMAP.md)
- Auth agente: [`docs/AUTH.md`](docs/AUTH.md)
- Software inventory + vuln intel: [`docs/software-inventory-vuln-intel.md`](docs/software-inventory-vuln-intel.md)
- Troubleshooting: [`docs/08-troubleshooting.md`](docs/08-troubleshooting.md)
- Seguridad: [`docs/09-security.md`](docs/09-security.md)
- Contribución: [`docs/10-contributing.md`](docs/10-contributing.md)

## Servicios opcionales
- **IDS** (`profiles: ids`) está definido en `docker-compose.yml`.
- Consulta detalles en [`docs/02-setup-docker.md`](docs/02-setup-docker.md).

## Troubleshooting rápido
Si algo falla, ve a [`docs/08-troubleshooting.md`](docs/08-troubleshooting.md).

### Troubleshooting: alembic_version missing
Si `public.alembic_version` no existe, normalmente es porque el entrypoint del backend
no ejecutó Alembic o el volumen quedó en un estado inconsistente. Revisa los logs con:

```bash
docker compose logs --tail=200 backend
```
