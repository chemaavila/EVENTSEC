# EventSec Enterprise (Fixed)

Plataforma completa de SIEM / EDR con:
- **Backend** FastAPI con autenticación JWT, sandbox y API de inventario de endpoints
- **Frontend** React + TypeScript + Vite con vistas para Sandbox, Endpoint Inventory y gestión de usuarios
- **Agente** ligero (PyInstaller) para enviar alertas, eventos SIEM/EDR y telemetría de endpoints
- **Docker Compose** para levantar frontend + backend
- **Autenticación** completa con roles y permisos
- **Gestión de usuarios** con perfiles avanzados y panel administrador
- **Workplans** y asignación de tareas
- **War Room** para notas y colaboración
- **Sandbox** para análisis de archivos/IPs/URLs con VT + OSINT simulados
- **Inventario de endpoints** basado en telemetría del agente
- **Escalación de alertas** y grupos de trabajo
- **KQL Workbench** estilo Microsoft Sentinel para búsquedas avanzadas sobre OpenSearch

## Requisitos

- Docker y Docker Compose
- (Opcional) Node.js >= 18 y npm si quieres ejecutar el frontend fuera de Docker
- Python 3.11+ si quieres ejecutar el agente fuera de Docker

## Ejecutar con Docker

Desde la carpeta raíz `eventsec_enterprise_fixed`:

```bash
docker compose up -d --build
```

> **Linux only:** OpenSearch necesita `vm.max_map_count >= 262144`. Ajusta una vez con:
> ```bash
> sudo sysctl -w vm.max_map_count=262144
> ```

> **Secrets & TLS:** Los contenedores leen los secretos desde `backend/secrets/*.txt` (montados como Docker secrets). Actualiza esos archivos antes de desplegar. Los certificados opcionales pueden copiarse a `infra/certs/server.crt` y `infra/certs/server.key`, habilitando HTTPS con `SERVER_HTTPS_ENABLED=true`.

- Tras levantar los contenedores ejecuta las migraciones:

```bash
docker compose exec backend alembic upgrade head
```

- Backend: http://localhost:8000/docs (usa `OPENSEARCH_URL=http://opensearch:9200` por defecto)
- Frontend: http://localhost:5173/

Para parar los contenedores:

```bash
docker compose down -v
```

## Ejecutar backend sin Docker

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # en macOS / Linux
# .venv\Scripts\activate  # en Windows

pip install -r requirements.txt
alembic upgrade head  # aplica la migración inicial
export OPENSEARCH_URL="http://localhost:9200"
export SECRET_KEY_FILE=./secrets/jwt_secret.txt
export AGENT_ENROLLMENT_KEY_FILE=./secrets/agent_enrollment_key.txt
python -m app.server  # usa HTTPS/mTLS si defines SERVER_HTTPS_ENABLED=true
```

Por defecto la API se conecta a `postgresql+psycopg2://eventsec:eventsec@localhost:5432/eventsec`. Puedes
sobrescribirlo definiendo la variable `DATABASE_URL` antes de ejecutar Alembic o Uvicorn.

## Ejecutar frontend sin Docker

```bash
cd frontend
npm install
npm run dev
```

El frontend usará por defecto la API en `http://localhost:8000`.

## Ejecutar el agente

### Opción 1: Launcher y doble clic (recomendado)

- Usa `agent/scripts/build_macos.sh` / `agent/scripts/build_windows.ps1` / `agent/scripts/build_linux.sh` para generar los binarios.
- Cada script compila `eventsec-agent` (core) y el launcher (`EventSec Agent.app` o launcher EXE) además de preparar el servicio/LaunchAgent (o la unidad systemd).

El launcher (`agent/launcher.py`) inicia en la bandeja y maneja:

1. Registro del servicio (launchd en macOS, `sc` en Windows, `systemd` en Linux).
2. Comandos Start / Stop en el menú y el estado “Running / Stopped” con el último latido.
3. Accesos directos a “View Logs”, “Settings” (abre el config), y “Uninstall”.
4. Validación de `agent_config.json` guardado en las rutas OS-nativas (`~/Library/Application Support/EventSec Agent/` en macOS, `%PROGRAMDATA%\EventSec Agent\` en Windows, `/etc/eventsec-agent/` o `~/.config/eventsec-agent/` en Linux).

Consulta `docs/double_click.md` para más detalles, `docs/release_process.md` para firmas y artefactos, y `docs/qa_plan.md` para la matriz de pruebas que incluye instalación limpia, reinicio y desinstalación.

### Opción 2: Python (Desarrollo)

```bash
cd agent
python -m venv .venv
source .venv/bin/activate  # en macOS / Linux
# .venv\Scripts\activate  # en Windows

pip install -r requirements.txt
python agent.py
```

El agente creará alertas de ejemplo periódicamente en el backend.

### Configuración del agente

Cada binario incluye (o genera en el primer arranque) un archivo `agent_config.json`
ubicado junto al ejecutable (y dentro de `Contents/MacOS` para la versión `.app`). Edita ese archivo para que los agentes desplegados en otros equipos sepan a qué backend conectarse. Los logs se guardan en `agent.log` junto al binario; si la carpeta es de solo lectura el agente usa automáticamente `~/.eventsec-agent/agent.log`.

```json
{
  "api_url": "http://tu-servidor:8000",
  "agent_token": "mi-token-compartido",
  "interval": 60,
  "enrollment_key": "eventsec-enroll",
  "log_paths": [
    "/var/log/syslog",
    "/var/log/system.log"
  ]
}
```

- `api_url`: URL completa donde vive el backend EventSec.
- `agent_token`: Debe coincidir con la variable `EVENTSEC_AGENT_TOKEN` utilizada por el backend.
- `interval`: Frecuencia del heartbeat (en segundos).
- `enrollment_key`: Clave usada para registrarse automáticamente contra `/agents/enroll`.
- `log_paths`: Archivos que el agente vigila para generar eventos (se pueden añadir rutas específicas por host).

También puedes definir un archivo alternativo mediante `EVENTSEC_AGENT_CONFIG=/ruta/al/config` o sobrescribir los campos con variables de entorno (ver más abajo).

El binario CLI muestra un asistente la primera vez que se ejecuta (URL del backend, token compartido, intervalo) y persiste las respuestas en `agent_config.json`. Las versiones GUI (`eventsec-agent.exe`, `eventsec-agent.app`) omiten ese asistente y dependen exclusivamente del archivo de configuración para que el usuario solo tenga que hacer doble clic.

### Pasos rápidos para ejecutar el agente
1. Copia el binario adecuado para tu OS desde `agent/dist/` o `agent-share/bin/`.
2. Edita `agent_config.json` (api_url, agent_token, enrollment_key).
3. Ejecuta:
   - Windows: doble clic a `eventsec-agent.exe`
   - macOS: abre `eventsec-agent.app`
   - Linux: `chmod +x eventsec-agent && ./eventsec-agent`
4. Verifica en el dashboard que el agente aparece online y revisa `agent.log` si necesitas diagnóstico.

**Enrollment:** los nuevos agentes se registran via `POST /agents/enroll` enviando su nombre/OS/IP y el `enrollment_key`. Define el valor esperado con la variable `AGENT_ENROLLMENT_KEY` en el backend (por defecto `eventsec-enroll`). El backend devuelve un `api_key` que el agente debe enviar en el header `X-Agent-Key` para heartbeats y envío de eventos.

## Threat Map (Live-only)

The Threat Map UI is **strict live-only** by default:
- **No synthetic/mock events**
- **No placeholder KPIs**
- The UI shows **NO LIVE TELEMETRY** until real events arrive

### Backend configuration
- `TELEMETRY_MODE=live` (default) or `TELEMETRY_MODE=mock` (explicit dev opt-in)
  - In `live` mode the backend emits **zero** threat-map events unless ingested via `/ingest` (or future legal connectors/sensors).
- `MAXMIND_DB_PATH=/path/to/GeoIP.mmdb` for deterministic IP→Geo/ASN enrichment
  - If missing/unreadable, geo is **unknown** and no random coordinates are ever generated.

### Frontend configuration
- `VITE_THREATMAP_WS_URL=ws://localhost:8000/ws/threatmap`

### Telemetry contract + examples
See `docs/threat_map.md` for schema, semantics, and `curl` examples.

## Autenticación

La aplicación requiere autenticación para acceder. Credenciales por defecto:

- **Admin**: `admin@example.com` / `Admin123!`
- **Analyst**: `analyst@example.com` / `Analyst123!`

### Roles disponibles:
- **admin**: Acceso completo, puede crear/editar usuarios y perfiles
- **team_lead**: Puede crear grupos de trabajo y operar en endpoints
- **analyst**: Acceso estándar a alertas y operaciones
- **senior_analyst**: Acceso avanzado

## KQL Workbench (Sentinel style)

- Abre **KQL workbench** (`/advanced-search`) para lanzar la ventana de caza tipo Microsoft Sentinel.
- Escribe consultas KQL como `SecurityEvent | where severity == "high" and message contains "phish" | limit 50`.
- Pulsa **Run query** o `Ctrl/Cmd + Enter`. El backend ejecuta la consulta mediante `POST /search/kql` contra OpenSearch.
- El panel incluye editor monoespaciado, historial, plantillas guardadas, timeline por hora, tabla interactiva y visor JSON del documento seleccionado.
- Puedes proyectar campos (`project campo1, campo2`) y ajustar `limit` (1-500) para controlar el volumen devuelto.

Los errores de sintaxis o límites inválidos responden con `400 Bad Request` para facilitar el ajuste rápido de consultas.

## Características Principales

### Autenticación y Usuarios
- ✅ Sistema de autenticación JWT
- ✅ Roles y permisos basados en roles
- ✅ Gestión de usuarios (solo admin)
- ✅ Perfiles con: equipo, manager, computadora, teléfono móvil

### Alertas
- ✅ Visualización y gestión de alertas
- ✅ Escalación de alertas a otros usuarios
- ✅ Eliminación de alertas
- ✅ Acciones de contención (bloquear URL, sender, aislar dispositivo, etc.)
- ✅ Logging de todas las acciones

### Handovers
- ✅ Creación de handovers de turno
- ✅ Envío por email (simulado, listo para servicio de email)

### Workplans
- ✅ Creación de planes de trabajo
- ✅ Asignación a alertas y usuarios

### War Room
- ✅ Notas colaborativas
- ✅ Asociación con alertas
- ✅ Soporte para adjuntos

### Sandbox
- ✅ Análisis de archivos, URLs, IPs, dominios, hashes
- ✅ Integración simulada con VirusTotal, OSINT y reglas YARA
- ✅ Resultado con veredicto, hash, tipo de amenaza e IOCs
- ✅ Asociación con endpoints del inventario

### Inventario de Endpoints
- ✅ Estado del agente, propietario, localización y métricas de recursos
- ✅ Procesos activos y alertas abiertas
- ✅ Integración directa con el agente (heartbeat)
- ✅ Acciones remotas (aislar, liberar, reiniciar, ejecutar comandos) con confirmación del agente

### Telemetría de red
- ✅ Registro de clics en URLs de phishing y tráfico sospechoso
- ✅ Generación automática de alertas cuando el agente detecta eventos maliciosos
- ✅ Panel en el dashboard para revisar eventos recientes y abrirlos en un modal

### Inventario, Vulnerabilidades y SCA
- ✅ API `/inventory/{agent_id}` para que los agentes reporten hardware/software/red/procesos
- ✅ API `/vulnerabilities` con definiciones (CVE) y evaluación automática por agente
- ✅ API `/sca/{agent_id}` para subir resultados de Security Configuration Assessment
- ✅ El agente de muestra envía inventario y resultados SCA periódicamente para demostrar el flujo completo

### Seguridad, TLS y Operaciones
- ✅ TLS/mTLS opcional (certificados configurables vía `SERVER_SSL_*`)
- ✅ Secrets externos (`SECRET_KEY_FILE`, `AGENT_ENROLLMENT_KEY_FILE`, Docker secrets, Vault-ready)
- ✅ Endpoint `/metrics` para Prometheus
- ✅ Job de retención (`python -m app.maintenance`) + servicio `retention` en docker-compose
- ✅ Pipeline CI (GitHub Actions) que valida backend, frontend y agente
- ✅ Manifiestos Kubernetes (`deploy/k8s`) inspirados en las topologías públicas de Wazuh

### OpenSearch + Explorador de eventos
- ✅ OpenSearch single-node incluido en `docker compose` (con seguridad deshabilitada para desarrollo)
- ✅ Indexación en tiempo real de eventos del agente y alertas (stream directo desde el manager)
- ✅ API `/events` con filtros Lucene/WQL (`query`, `severity`, `size`)
- ✅ Página **Events explorer** con barra de búsqueda, filtros por severidad, tabla cronológica y modal con JSON completo
- ✅ Dashboard muestra feed resumido y enlace rápido al explorador

### Grupos de Trabajo
- ✅ Creación y gestión de grupos
- ✅ Asignación de miembros

### Configuración del agente

Además del archivo de configuración, puedes sobrescribir valores mediante variables de entorno:

```bash
# Cambiar URL del backend
export EVENTSEC_API_URL="http://tu-servidor:8000"

# Cambiar intervalo (segundos)
export EVENTSEC_AGENT_INTERVAL=30

# Token compartido para autenticarse desde el agente
export EVENTSEC_AGENT_TOKEN="mi-token-secreto"

# Ejecutar
./dist/eventsec-agent  # o python agent.py
```

> El backend debe lanzarse con el mismo valor en `EVENTSEC_AGENT_TOKEN`. El ejecutable incluye un `agent_config.json` que puedes personalizar para que otros dispositivos apunten automáticamente al backend correcto.

En sistemas interactivos, el binario pregunta la primera vez por la URL del backend, el token compartido y el intervalo, guardando las respuestas en `agent_config.json`. Solo tienes que copiar el ejecutable y ese archivo a otra máquina para que empiece a reportar telemetría sin editar scripts.

## Mantenimiento & Monitorización

- `GET /metrics`: expuesto automáticamente gracias a `prometheus-fastapi-instrumentator`.
- `python -m app.maintenance --days 30`: elimina eventos antiguos bajo demanda.
- `python -m app.maintenance --days 30 --loop-seconds 86400`: modo daemon (el servicio `retention` del docker-compose ejecuta esto diariamente).
- Variables relevantes:
  - `SERVER_HTTPS_ENABLED`, `SERVER_SSL_CERTFILE`, `SERVER_SSL_KEYFILE`, `SERVER_SSL_CA_FILE`, `SERVER_SSL_CLIENT_CERT_REQUIRED`
  - `SECRET_KEY_FILE`, `AGENT_ENROLLMENT_KEY_FILE`
  - `RETENTION_DAYS` (para el servicio `retention`)

## Email Protection service

- `email_protection` implements Gmail/Microsoft OAuth connectors, inbox sync and a phishing analyzer; it stores refresh tokens in `email_protection/tokens.db`.
- Configure credentials and run the service via `docker compose up -d --build` (the new `email_protection` container listens on port `8100`).
- OAuth flows: `http://localhost:8100/auth/google/start`, `http://localhost:8100/auth/microsoft/start`. Sync endpoints live under `/sync/*` for both providers.

## Threat Intelligence design

- The planned Threat Intelligence tab is documented in `docs/threat_intel_design.md`, which covers the hero layout, KPI cards, filter bar, tabs (Cuarentena, Informes, etc.), the quarantined-messages table, and the integrations required to surface data from the Email Protection service.

## Endpoint scanner (PROTOXOL)

- `protoxol_triage_package` runs a defensive triage, collecting host/process/network info, suspicious files, hashes, optional YARA, and optional VT/OTX lookups.
- Build it via `docker compose --profile scanner build scanner` and invoke with `docker compose --profile scanner run --rm scanner python protoxol_triage.py --out triage_out --since-days 14 --max-files 4000`.
- Output is dropped under `scanner_out/<host>_<timestamp>/`; pass `--zip` to produce `triage_out/*.zip`.
- Supply `VT_API_KEY`, `OTX_API_KEY`, and YARA rules (e.g., `rules_sample.yar`) via env or CLI arguments.
## Kubernetes & HA

- Plantillas en `deploy/k8s/` (Namespace, Postgres, OpenSearch StatefulSet, backend/frontend Deployments y secretos).
- Copia `deploy/k8s/secrets-example.yaml`, rellena las claves/certs y aplica:
  ```bash
  kubectl apply -k deploy/k8s
  ```
- Actualiza los campos `image` para apuntar a tu registry (por ejemplo `ghcr.io/<org>/eventsec-backend`).
- El diseño replica la arquitectura documentada por Wazuh (k8s + docker) para facilitar clusterización y futuras integraciones.

## CI/CD

El workflow `.github/workflows/ci.yml` ejecuta:

1. **Backend:** `pytest` + instalación limpia.
2. **Frontend:** `npm ci && npm run build`.
3. **Agent:** `pip install` + `py_compile` para detectar errores sintácticos.

Amplía el pipeline con steps adicionales (push de imágenes, pruebas E2E) según tus necesidades.
