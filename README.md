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

### Opción 1: Ejecutable (Recomendado)

Puedes usar el ejecutable pre-compilado o compilarlo tú mismo:

**Windows:**
```cmd
cd agent
build_windows.bat
dist\eventsec-agent.exe
```

**Linux/macOS:**
```bash
cd agent
chmod +x build_linux.sh  # o build_macos.sh
./build_linux.sh         # ./build_macos.sh
./dist/eventsec-agent
```

> Los scripts crean un entorno virtual temporal `.build-venv`, instalan PyInstaller dentro de él y lo eliminan al finalizar. Esto evita el error de “externally managed environment” en macOS/Homebrew.

Ver `agent/README_BUILD.md` para más detalles sobre la compilación y distribución (incluye firmas/notarización opcional).

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
ubicado junto al ejecutable. Edita ese archivo para que los agentes desplegados en
otros equipos sepan a qué backend conectarse:

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

**Enrollment:** los nuevos agentes se registran via `POST /agents/enroll` enviando su nombre/OS/IP y el `enrollment_key`. Define el valor esperado con la variable `AGENT_ENROLLMENT_KEY` en el backend (por defecto `eventsec-enroll`). El backend devuelve un `api_key` que el agente debe enviar en el header `X-Agent-Key` para heartbeats y envío de eventos.

## Autenticación

La aplicación requiere autenticación para acceder. Credenciales por defecto:

- **Admin**: `admin@example.com` / `Admin123!`
- **Analyst**: `analyst@example.com` / `Analyst123!`

### Roles disponibles:
- **admin**: Acceso completo, puede crear/editar usuarios y perfiles
- **team_lead**: Puede crear grupos de trabajo y operar en endpoints
- **analyst**: Acceso estándar a alertas y operaciones
- **senior_analyst**: Acceso avanzado

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
