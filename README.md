# EVENTSEC

EVENTSEC es una plataforma SOC unificada (SIEM + EDR + seguridad de red + protección de email) con
backend FastAPI, frontend React/Vite y servicios de soporte como OpenSearch y Postgres. Incluye
flujos de alertas/incidentes, gestión de usuarios, workplans y telemetría en tiempo real.

## Quickstart (Docker, 5–10 min)

**Requisitos:** Docker + Docker Compose.

```bash
git clone https://github.com/chemaavila/EVENTSEC.git
cd EVENTSEC

docker compose up -d --build
```

> **Linux:** OpenSearch necesita `vm.max_map_count >= 262144`.
> ```bash
> sudo sysctl -w vm.max_map_count=262144
> ```

### Migraciones
El contenedor `backend` ejecuta `alembic upgrade head` en el arranque. Si necesitas ejecutarlo manualmente:

```bash
docker compose exec backend alembic upgrade head
```

### URLs / Puertos
- Frontend: http://localhost:5173
- Backend (API + Swagger): http://localhost:8000/docs
- OpenSearch: http://localhost:9200
- Postgres: localhost:5432
- Email Protection: http://localhost:8100

### Health checks rápidos
```bash
docker compose ps
```

```bash
docker compose logs -f --tail=200 backend
```

```bash
curl http://localhost:8000/
curl http://localhost:8100/health
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
- Troubleshooting: [`docs/08-troubleshooting.md`](docs/08-troubleshooting.md)
- Seguridad: [`docs/09-security.md`](docs/09-security.md)
- Contribución: [`docs/10-contributing.md`](docs/10-contributing.md)

## Servicios opcionales
- **Scanner** (`profiles: scanner`) y **IDS** (`profiles: ids`) están definidos en `docker-compose.yml`.
- Consulta detalles en [`docs/02-setup-docker.md`](docs/02-setup-docker.md).

## Troubleshooting rápido
Si algo falla, ve a [`docs/08-troubleshooting.md`](docs/08-troubleshooting.md).
