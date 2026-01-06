# Troubleshooting

## OpenSearch no inicia (Linux)
**Síntoma**
```
max virtual memory areas vm.max_map_count [65530] is too low, increase to at least [262144]
```

**Causa**
OpenSearch requiere un límite de memoria virtual mayor en Linux.

**Solución**
```bash
sudo sysctl -w vm.max_map_count=262144
```

**Verificación**
```bash
curl -sSf http://localhost:9200
```

---

## Backend no levanta por migraciones
**Síntoma**
```
Alembic migrations failed after X attempts.
```

**Causa**
Postgres aún no está listo cuando arranca el `backend`.

**Solución**
1. Revisa logs:
   ```bash
   docker compose logs -f --tail=200 backend
   ```
2. Espera a que `db` esté listo o reinicia:
   ```bash
   docker compose restart backend
   ```
3. Opcional: aumenta reintentos con `MIGRATION_ATTEMPTS`.

**Verificación**
```bash
docker compose exec backend alembic upgrade head
```

---

## DuplicateColumn en users.tenant_id (backend unhealthy)
**Síntoma**
```
psycopg2.errors.DuplicateColumn: column "tenant_id" of relation "users" already exists
```

**Causa**
- Volumen persistido con esquema adelantado (tenant_id ya existe).
- Ejecuciones concurrentes de migraciones sin lock.

**Solución rápida (dev, borra datos)**
```bash
docker compose down -v --remove-orphans
docker compose up -d --build
```

**Solución sin borrar datos (avanzada)**
1. Inspecciona el esquema:
   ```bash
   docker compose exec db psql -U eventsec -d eventsec -c "\d users"
   ```
2. Revisa el estado de alembic:
   ```bash
   docker compose exec backend alembic current
   docker compose exec backend alembic history --verbose
   ```
3. Si el esquema coincide con el código, estampa la revisión (con cuidado):
   ```bash
   docker compose exec backend alembic stamp <revision>
   docker compose exec backend alembic upgrade head
   ```

**Advertencia**
`alembic stamp` puede dejar la DB inconsistente si se usa con un esquema que no coincide.

---

## 401 Unauthorized en la API
**Síntoma**
```
{"detail":"Invalid authentication credentials"}
```

**Causa**
No estás autenticado o el token JWT/`X-Auth-Token` es inválido.

**Solución**
- Autentica en `/auth/login` desde la UI.
- Asegura que el navegador conserve la cookie `access_token`.

**Verificación**
```bash
curl -I http://localhost:8000/
```

---

## Frontend build falla por Rollup native package
**Síntoma**
```
Error: Cannot find module @rollup/rollup-linux-...
```

**Causa**
Dependencia opcional nativa no instalada en contenedor.

**Solución**
- El `Dockerfile.frontend` ya instala el paquete correcto por arquitectura.
- Rebuild completo:
  ```bash
  docker compose build --no-cache frontend
  docker compose up -d frontend
  ```

**Verificación**
```bash
docker compose logs -f --tail=200 frontend
```

---

## Threat Map no muestra eventos
**Síntoma**
UI sin telemetría en `/threat-intel`.

**Causa**
`TELEMETRY_MODE` por defecto es `live`; no genera eventos sintéticos.

**Solución**
- Envía eventos reales vía `/ingest`.
- (Dev) Cambia `TELEMETRY_MODE=mock` en el backend.

**Verificación**
```bash
docker compose logs -f --tail=200 backend
```

---

## Puertos ocupados
**Síntoma**
```
bind: address already in use
```

**Solución**
1. Identifica el proceso.
2. Libera o cambia el puerto en `docker-compose.yml`.

**Verificación**
```bash
docker compose ps
```

---

## Diagnóstico rápido
```bash
docker compose ps
```

```bash
docker compose logs -f --tail=200 backend
```

```bash
docker compose logs -f --tail=200 frontend
```

```bash
curl http://localhost:8000/
```
