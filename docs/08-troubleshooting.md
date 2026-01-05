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
