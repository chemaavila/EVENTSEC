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
Postgres u OpenSearch aún no están listos cuando arranca el `backend`.

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

## Worker de vulnerabilidades falla por tabla faltante
**Síntoma**
```
psycopg2.errors.UndefinedTable: relation "software_components" does not exist
```

**Causa**
El worker arrancó antes de que el backend completara las migraciones y el schema requerido.

**Solución**
1. Revisa el estado de alembic:
   ```bash
   docker compose exec backend alembic current
   ```
2. Verifica que el backend esté healthy:
   ```bash
   curl -fsS http://localhost:8000/readyz
   ```
3. Reinicia el worker:
   ```bash
   docker compose restart vuln_worker
   ```

**Verificación**
```bash
docker compose exec db psql -U eventsec -d eventsec -c \
  "SELECT to_regclass('public.software_components');"
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
No estás autenticado o el token JWT (cookie `access_token` o `X-Auth-Token`) es inválido.

**Solución**
- Autentica en `/auth/login` desde la UI.
- Asegura que el navegador conserve la cookie `access_token`.

**Verificación**
```bash
curl -I http://localhost:8000/
```

---

## Troubleshooting Sign-in

### Credenciales y reset (dev)
- **Credenciales por defecto**:
  - Admin: `admin@example.com` / `Admin123!`
  - Analyst: `analyst@example.com` / `Analyst123!`
- **Reset con borrado total (dev)**:
  ```bash
  docker compose down -v --remove-orphans
  docker compose up -d --build
  ```
- **Reset de password sin borrar datos**:
  ```bash
  EVENTSEC_ADMIN_PASSWORD='Admin123!' docker compose up -d --build backend
  ```
  Esto fuerza el hash del usuario `admin@example.com` durante el seed.

### A) 500 al hacer login o /me
- ¿DB schema existe?
  - `SELECT to_regclass('public.alembic_version')`
  - `SELECT to_regclass('public.users')`
- Logs backend: errores SQL “relation does not exist” => migraciones no corrieron.
- Arreglar compose/entrypoint/migraciones.

### B) 401 siempre aunque credenciales correctas
- ¿seed admin se ejecutó?
- ¿password hashing usa la misma función que login?
- ¿JWT secret/env correcto?
- ¿email exacto coincide (case/trim)?

### C) Login OK pero /me falla (401)
- ¿cookie se está enviando?
  - DevTools > Network > request headers: `Cookie: access_token=...`
- Si no se envía:
  - Frontend usa `credentials: "include"` / `withCredentials`?
  - CORS `allow_credentials=True` y `allow_origins` NO `"*"`
  - Revisa `CORS_ORIGINS` (lista separada por comas, incluye localhost/127.0.0.1)
  - Cookie SameSite/Secure:
    - `SameSite=None` requiere `Secure=True` (rompe en http local)
    - Recomendado dev: `SameSite=Lax` + `Secure=False`
  - ¿Dominio/Path mal fijados?
    - `COOKIE_DOMAIN`, `COOKIE_PATH`, `COOKIE_SAMESITE`, `COOKIE_SECURE`

### D) CORS blocked
- `allow_origins` incluye el origin real del frontend.
- No `"*"` con `allow_credentials`.
- Verificar preflight OPTIONS.

### E) En Docker funciona, en local no
- Variables de entorno diferentes (`FRONTEND_URL`, `CORS_ORIGINS`, `COOKIE_SECURE`).
- Puertos distintos.

### F) Reset de password admin en dev
- Si necesitas forzar el password del admin en un entorno dev sin borrar datos:
  - Define `EVENTSEC_ADMIN_PASSWORD` antes de arrancar el backend.
  - El seed actualizará el hash del usuario `admin@example.com`.

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
