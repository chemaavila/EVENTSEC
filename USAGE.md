# EventSec Documentation - Usage Guide

## Quick Start (Recommended - Docker)

### 1. Start the Application

From the project root directory:

> **Linux only:** OpenSearch necesita `vm.max_map_count` elevado. Antes del primer arranque:
> ```bash
> sudo sysctl -w vm.max_map_count=262144
> ```

```bash
docker compose up -d --build
```

> **Secrets & TLS**: For production, set `SECRET_KEY_FILE` and `AGENT_ENROLLMENT_KEY_FILE` (or their env fallbacks) to override the built-in dev defaults. Optional certificates can be dropped in `infra/certs/server.crt` and `server.key`, then enable HTTPS with `SERVER_HTTPS_ENABLED=true`.

Database migrations run automatically on container start.

This will:
- Build and start the backend (FastAPI) on port 8000
- Build and start the frontend (React) on port 5173
- Set up all dependencies automatically

### 2. Access the Application

- **Frontend UI**: Open http://localhost:5173 in your browser
- **Backend API Docs**: Open http://localhost:8000/docs (Swagger UI)

### 3. Stop the Application

```bash
docker compose down
```

To also remove volumes:
```bash
docker compose down -v
```

If you hit a container name conflict (for example, `/eventsec_opensearch` already in use), run:

```bash
docker compose down --remove-orphans
docker rm -f eventsec_opensearch eventsec_db eventsec_backend eventsec_frontend
```

---

## Manual Setup (Without Docker)

### Backend Setup

```bash
cd backend
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

pip install -r requirements.txt
alembic upgrade head
export OPENSEARCH_URL="http://localhost:9200"
export SECRET_KEY_FILE=./secrets/jwt_secret.txt
export AGENT_ENROLLMENT_KEY_FILE=./secrets/agent_enrollment_key.txt
python -m app.server
```

Backend will be available at: http://localhost:8000

> The default connection string is `postgresql+psycopg2://eventsec:eventsec@localhost:5432/eventsec`. Override it by setting the `DATABASE_URL` environment variable before running Alembic/Uvicorn.

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at: http://localhost:5173

---

## Running the Agent (Generate Test Data)

The agent sends test alerts, SIEM events, EDR events, and endpoint telemetry to the backend.

### Option 1: Standalone executable (recommended, double-click)

Scripts create a temporary `.build-venv`, install dependencies inside it, run PyInstaller, and remove the venv automatically (avoids macOS PEP‑668).

- **Windows (.exe)** — `agent/dist/eventsec-agent.exe` (double-click; logs in `agent.log`).
- **macOS (.app)** — `agent/dist/eventsec-agent.app` (double-click; if blocked once: `xattr -dr com.apple.quarantine dist/eventsec-agent.app`). CLI: `dist/eventsec-agent`.
- **Linux (binary)** — `chmod +x agent/dist/eventsec-agent && ./agent/dist/eventsec-agent` (some DEs allow double-click if executable). Logs in `agent.log` (fallback `~/.eventsec-agent/agent.log`).

After building on that OS, run `./agent-share/scripts/prepare_share.sh` (or `.ps1` on Windows) to copy the binary/.app plus `agent_config.json` into `agent-share/bin/`; zip and ship that folder.

### Option 2: Run with Python directly

```bash
cd agent
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python agent.py
```

### Option 3: Configure for remote backend, custom interval, and shared token

```bash
export EVENTSEC_API_URL="http://your-server-ip:8000"
export EVENTSEC_AGENT_INTERVAL=30
export EVENTSEC_AGENT_TOKEN="super-secret-token"
./dist/eventsec-agent
```

> El backend debe arrancarse con la misma variable `EVENTSEC_AGENT_TOKEN` (por defecto `eventsec-agent-token`). Esto permite que el agente acceda a `/alerts` sin necesidad de un usuario humano.

> Para registrar agentes de forma segura usa el endpoint `POST /agents/enroll` y especifica el `AGENT_ENROLLMENT_KEY`. El backend devolverá un `api_key` que deberá enviarse en cada petición mediante el header `X-Agent-Key`.

### Configuration file

Each build bundles (or creates on first run) an `agent_config.json` next to the executable (and inside `Contents/MacOS` for the `.app`). Edit it before shipping the agent to other devices. Runtime logs live in `agent.log` next to the binary; if that folder is read-only the agent uses `~/.eventsec-agent/agent.log` automatically.

```json
{
  "api_url": "http://your-server-ip:8000",
  "agent_token": "super-secret-token",
  "interval": 60,
  "enrollment_key": "eventsec-enroll",
  "log_paths": [
    "/var/log/syslog",
    "/var/log/system.log"
  ]
}
```

You can override the file with environment variables or point to an alternate config via `EVENTSEC_AGENT_CONFIG=/path/to/config.json`. The CLI binary asks once for backend URL/token/interval and persists the answers; the GUI builds (`eventsec-agent.exe`, `eventsec-agent.app`) skip that wizard and rely entirely on `agent_config.json`, which makes them ideal for “double-click to run” distributions.

### Quick run checklist
1. Copy the OS-specific binary from `agent/dist/` or `agent-share/bin/`.
2. Edit `agent_config.json` (api_url, agent_token, enrollment_key).
3. Run:
   - Windows: double-click `eventsec-agent.exe`
   - macOS: open `eventsec-agent.app`
   - Linux: `chmod +x eventsec-agent && ./eventsec-agent`
4. Verify the agent appears online in the dashboard; check `agent.log` for diagnostics.

---

## Authentication

**⚠️ IMPORTANT: All routes require authentication.**

### Default Credentials

- **Admin Account**: 
  - Email: `admin@example.com`
  - Password: `Admin123!`
  - Role: Full administrative access

- **Analyst Account**:
  - Email: `analyst@example.com`
  - Password: `Analyst123!`
  - Role: Standard analyst access

### User Roles

- **admin**: Full system access, can create/edit users and profiles
- **team_lead**: Can create work groups, manage teams
- **analyst**: Standard access to alerts and operations
- **senior_analyst**: Advanced analyst privileges

### First Login

1. Navigate to http://localhost:5173
2. You will be redirected to the login page
3. Use one of the default credentials above
4. After login, you'll have access to all features based on your role

## KQL Workbench (Sentinel-style)

1. Open **KQL workbench** from the sidebar (route `/advanced-search`).
2. Enter a KQL query such as `SecurityEvent | where severity == "high" and message contains "phish" | limit 100`.
3. Press **Run query** or hit `Ctrl/Cmd + Enter`. The frontend calls `POST /search/kql` and the backend translates the expression into OpenSearch DSL.
4. Use the limit slider (1‑500), saved templates, or your own history entries to iterate quickly.
5. Inspect the output via the hourly timeline, interactive table, and JSON inspector.

If the parser detects an unsupported clause or invalid syntax you’ll get a `400 Bad Request` describing exactly what to fix.

---

## Using the Application

### Dashboard (`/`)

- **Overview**: See total alerts, open alerts, in-progress alerts, and closed alerts
- **Severity Distribution**: View alerts grouped by severity (critical, high, medium, low)
- **Activity Feed**: Latest 5 alerts with their status and metadata
- **Network Telemetry**: Latest phishing clicks with modal detail
- **OpenSearch Feed**: Snapshot of indexed events with shortcut to the full explorer

### Alerts Page (`/alerts`)

**View Alerts:**
- See all alerts sorted by creation date (newest first)
- Click any alert to view details

**Create Manual Alert:**
- Fill out the form on the right side
- Required fields: Title, Source, Category, Severity
- Optional fields: Description, URL, Sender, Username, Hostname
- Click "Create alert"

**Alert Detail Page (`/alerts/:id`):**
- **Information Tab**: View all alert details with larger, more readable text
- **Workplan Tab**: Take notes (stored locally in browser)
- **Utilities Tab**: 
  - Block/Unblock URL (requires URL parameter)
  - Block/Unblock Sender (requires sender email parameter)
  - Revoke User Session (requires username parameter)
  - Isolate Device (requires hostname parameter)
  - All actions are logged for audit purposes
- **Delete Button**: Delete alerts (with confirmation)
- **Escalate Button**: Escalate alert to another user (coming soon in UI)

### SIEM Page (`/siem`)

- **Log Sources**: See all detected log sources with event counts
- **Recent Events**: View latest SIEM events with:
  - Timestamp
  - Source
  - Category
  - Host
  - Severity
- **Events by Category**: Statistics showing event distribution
- **Refresh Button**: Reload events from API

### EDR Page (`/edr`)

- **Endpoints**: See all detected endpoints with:
  - Hostname
  - Event count
  - User count
  - Severity status (Healthy/Suspicious/Alert)
- **Recent Events**: View latest EDR events with:
  - Timestamp
  - Hostname
  - Username
  - Event type
  - Process name
  - Action
  - Severity
- **Refresh Button**: Reload events from API

### Profile Page (`/profile`)

- View your user profile
- See: Full name, email, role, timezone
- See: Team, manager, computer, mobile phone (if set)
- **Admin users**: Can create and edit user profiles

### Handover Page (`/handover`)

- Create shift handover notes
- **Email Functionality**: 
  - Check "Send email" option
  - Add recipient email addresses
  - Handover will be sent via email (simulated, ready for production email service)

### Sandbox Page (`/sandbox`)

- Drag & drop files (hasta 100MB) o analiza URLs
- Ver veredicto (Malicious/Suspicious/Clean), tipo de amenaza, hash SHA‑256
- Lista de IOCs (IP, dominio, archivos generados, claves de registro, etc.)
- Coincidencias con endpoints del inventario (hostname, estado del agente, IP, ubicación)
- Historial de análisis previos y descarga simulada de reportes

### Endpoint Inventory (`/endpoints`)

- Catálogo de activos con filtrado rápido
- Ficha detallada: estado del agente, versión, propietario, ubicación, recursos (CPU/RAM/Disk)
- Procesos activos (nombre, PID, usuario, uso de CPU/RAM)
- Acciones simuladas: “Run scan” y “Isolate endpoint”

### Events Explorer (`/events`)

- Barra de búsqueda compatible con queries Lucene / WQL (`field:value AND field2:*error*`)
- Filtro rápido por severidad y tamaño de respuesta
- Resumen de severidades recuperadas
- Tabla cronológica con scroll infinito y botón de detalle
- Modal con el JSON completo de cada evento (ideal para hunting)

### User Management (`/admin/users`) — Solo administradores

- Métricas rápidas (total de usuarios, admins, leads)
- Directorio con búsqueda y selección
- Creación de usuarios (rol, contraseña temporal, equipo, manager, activos asignados)
- Vista rápida del perfil seleccionado

### Workplans (Backend Ready)

- Create workplans and assign to alerts
- Assign workplans to specific users
- Track workplan status

### War Room (Backend Ready)

- Create collaborative notes
- Associate notes with alerts
- Upload attachments

### Other Pages

- **IOC/BIOC** (`/ioc-bioc`): Indicators of Compromise (create/edit coming soon)
- **Analytics Rules** (`/analytics-rules`): Rule management (create/edit coming soon)
- **Correlation Rules** (`/correlation-rules`): Correlation rules (create/edit coming soon)
- **Advanced Search** (`/advanced-search`): Search interface (placeholder)

---

## API Endpoints

**⚠️ All endpoints require authentication.** The UI uses an HttpOnly `access_token` cookie
(`credentials: "include"`). For API tools, you can still pass a Bearer token in the
`Authorization` header or `X-Auth-Token`.

### Authentication

- `POST /auth/login` - Login (sets HttpOnly cookie and returns JWT for API tooling)
  - Body: `{ "email": "string", "password": "string" }`
  - Returns: `{ "access_token": "string", "user": UserProfile }`

### Users (Admin Only)

- `GET /users` - List all users (admin only)
- `POST /users` - Create new user (admin only)
- `PATCH /users/{id}` - Update user (admin only)

### Alerts

- `GET /alerts` - List all alerts (requires auth)
- `GET /alerts/{id}` - Get alert by ID (requires auth)
- `POST /alerts` - Create new alert (requires auth)
- `PATCH /alerts/{id}` - Update alert status (requires auth)
- `DELETE /alerts/{id}` - Delete alert (requires auth)
- `POST /alerts/{id}/escalate` - Escalate alert to user (requires auth)
- `POST /alerts/{id}/block-url?url={url}` - Block URL (requires URL parameter)
- `POST /alerts/{id}/unblock-url?url={url}` - Unblock URL (requires URL parameter)
- `POST /alerts/{id}/block-sender?sender={email}` - Block sender (requires sender parameter)
- `POST /alerts/{id}/unblock-sender?sender={email}` - Unblock sender (requires sender parameter)
- `POST /alerts/{id}/revoke-session?username={username}` - Revoke user session (requires username parameter)
- `POST /alerts/{id}/isolate-device?hostname={hostname}` - Isolate device (requires hostname parameter)

### SIEM Events

- `GET /siem/events` - List all SIEM events
- `POST /siem/events` - Create SIEM event

### EDR Events

- `GET /edr/events` - List all EDR events
- `POST /edr/events` - Create EDR event

### Profile

- `GET /me` - Get current user profile (requires auth)

### Handover

- `GET /handover` - List all handovers (requires auth)
- `POST /handover` - Create handover (requires auth)
  - Body includes: `send_email: boolean`, `recipient_emails: string[]`

### Work Groups

- `GET /workgroups` - List all work groups (requires auth)
- `POST /workgroups` - Create work group (team_lead/admin only)

### Workplans

- `GET /workplans` - List all workplans (requires auth)
- `POST /workplans` - Create workplan (requires auth)

### War Room

- `GET /warroom/notes` - List war room notes (requires auth)
- `POST /warroom/notes` - Create war room note (requires auth)

### Sandbox

- `POST /sandbox/analyze` - Analyze file/IP/URL/domain/hash (requires auth)
  - Body: `{ "type": "file|ip|url|domain|hash", "value": "string", "filename": "string?", "metadata": {...} }`
- `GET /sandbox/analyses` - List past analyses (requires auth)

### Events (OpenSearch-backed)

- `GET /events` - Query indexed events
  - Query params:
    - `query`: Lucene / WQL string (`event_type:logcollector AND severity:high`)
    - `severity`: Optional severity filter (low/medium/high/critical)
    - `size`: Max results (default 100, max 500)

### Data Lake (Tenant Scoped)

- `GET /tenants/{tenant_id}/storage-policy` - Get storage policy (tenant admin)
- `PUT /tenants/{tenant_id}/storage-policy` - Update storage policy + enable feature flag
- `GET /tenants/{tenant_id}/usage?from=&to=` - Tenant usage summary (requires data lake enabled)
- `GET /tenants/{tenant_id}/usage/export.csv` - CSV export of usage (requires data lake enabled)

### Inventory

- `POST /inventory/{agent_id}` - Agent pushes snapshots (`{"snapshots":[{ "category": "...", "data": {...}}]}`) using its `X-Agent-Key`
- `GET /inventory/{agent_id}` - Analysts retrieve grouped inventory (`category` and `limit` filters supported)

### Vulnerabilities

- `GET /vulnerabilities/definitions` - List/consume CVE definitions
- `POST /vulnerabilities/definitions` - Create definition (admin only)
- `GET /vulnerabilities/agents/{agent_id}` - View matches affecting a specific agent
- `POST /vulnerabilities/agents/{agent_id}/evaluate` - Run matching using latest software inventory snapshots

### SCA

- `POST /sca/{agent_id}/results` - Agent uploads Security Configuration Assessment results
- `GET /sca/{agent_id}/results` - Analysts inspect historical SCA evidence for an agent

### Endpoints

- `GET /endpoints` - List all endpoints with summary data (requires auth)
- `GET /endpoints/{id}` - Get detailed endpoint information (requires auth)

### Action Logs

- `GET /action-logs` - List all action logs (admin only)

---

## Maintenance & Monitoring

- `GET /metrics` exposes Prometheus metrics automatically.
- `python -m app.maintenance --days 30` prunes DB/OpenSearch entries older than N days.
- `python -m app.maintenance --days 30 --loop-seconds 86400` keeps running (the `retention` service in docker-compose uses this mode).
- Relevant env vars: `SERVER_HTTPS_ENABLED`, `SERVER_SSL_*`, `SECRET_KEY_FILE`, `AGENT_ENROLLMENT_KEY_FILE`, `RETENTION_DAYS`.

## Kubernetes / HA

- Templates live in `deploy/k8s/` (namespace, Postgres, OpenSearch, backend/frontend Deployments and secrets).
- Copy `secrets-example.yaml`, populate values, then run:
  ```bash
  kubectl apply -k deploy/k8s
  ```
- Update the `image` fields to point to your registry (or use an ImagePullSecret).

## CI/CD

`.github/workflows/ci.yml` runs three jobs on every push/PR:

1. Python backend: installs deps and executes `pytest`.
2. Frontend: `npm ci && npm run build`.
3. Agent: installs deps and runs `python -m py_compile agent.py`.

Extend the workflow with publish/deploy stages as needed.

## Example: Complete Workflow

1. **Start the application:**
   ```bash
   docker compose up -d --build
   ```

2. **Open the frontend:**
   - Go to http://localhost:5173
   - You'll be redirected to the login page

3. **Login:**
   - Use admin credentials: `admin@example.com` / `Admin123!`
   - Or analyst credentials: `analyst@example.com` / `Analyst123!`

4. **View the dashboard:**
   - You'll see the dashboard with sample alerts
   - Alerts are displayed with larger, more readable text

5. **Start the agent (in another terminal) to generate more data:**
   ```bash
   cd agent
   ./dist/eventsec-agent  # o python agent.py
   ```
   > La primera ejecución abre un pequeño asistente (URL del backend, token compartido, intervalo). Los valores se guardan en `agent_config.json` para reutilizarlos en otros equipos.

6. **View SIEM events:**
   - Click "SIEM" in the sidebar
   - You'll see events generated by the agent

7. **View EDR events:**
   - Click "EDR" in the sidebar
   - You'll see endpoint events generated by the agent

8. **Create a manual alert:**
   - Go to Alerts page
   - Fill out the form and click "Create alert"

9. **Investigate an alert / War room:**
   - Click on any alert
   - View details in the Information tab (larger text for better readability)
   - Use the **War room** tab to add collaborative notes and attach documents (links)
   - Take actions in the Utilities tab (all actions require parameters and are logged)

10. **Analyze a suspicious file/URL in the sandbox:**
    - Go to Sandbox
    - Drag & drop a file or paste a URL
    - Review verdict, hash, YARA matches, OSINT/VT data and impacted endpoints

11. **Inspect/control endpoints:**
    - Go to Endpoints
    - Select a host to view agent status, resource usage and active processes
    - Queue remote actions (isolate, release, reboot, run custom command). The agent fetches and acknowledges them automatically.

12. **Create a handover with email:**
    - Go to Handover page
    - Fill out the handover form
    - Check "Send email" and add recipient emails
    - Submit (email will be sent - simulated in demo)

13. **Admin: Onboard a new analyst:**
    - Login as admin
    - Navigate to Admin → User management
    - Use the form to create a user with team, manager and temporary password

---

## Troubleshooting

### Backend not starting

- Check if port 8000 is already in use
- Verify Python 3.11+ is installed
- Install dependencies: `pip install -r requirements.txt`
- Check Docker logs: `docker logs eventsec_backend`

### Authentication issues

- Make sure you're using the correct credentials
- Check browser console for authentication errors
- Verify the HttpOnly cookie `access_token` is set in the browser
- Verify the browser sends `Cookie: access_token=...` to `/me`
- Ensure `credentials: "include"` and `allow_credentials=true` on CORS
- Try logging out and logging back in

### Frontend not connecting to backend

- Verify backend is running on port 8000
- Check browser console for CORS errors
- Ensure backend CORS allows your frontend origin

### Agent not sending data

- Verify backend is running and accessible
- Check `EVENTSEC_API_URL` environment variable
- Check agent output for error messages
- Verify network connectivity

### No data showing

- Start the agent to generate test data
- Check browser console for API errors
- Verify backend is running: http://localhost:8000/docs

---

## Development Tips

### Backend Development

- API docs available at: http://localhost:8000/docs
- Auto-reload enabled with `--reload` flag
- Check logs for debugging

### Frontend Development

- Hot reload enabled in dev mode
- API base URL configurable via `VITE_API_BASE_URL` env var
- Check browser DevTools for errors

### Testing the API

Use the Swagger UI at http://localhost:8000/docs to:
- Test all endpoints
- See request/response schemas
- Try different parameters
- **Note**: Most endpoints require authentication
  - Click "Authorize" button in Swagger UI
  - Login first using `/auth/login` endpoint
  - Copy the `access_token` from response
  - Paste it in the "Value" field (format: `Bearer <token>`)
  - Or use the UI login so the `access_token` cookie is set automatically
  - Click "Authorize" to use authenticated requests

---

## Features Status

### ✅ Fully Implemented

- Authentication system with HttpOnly cookie (JWT)
- Role-based access control
- User management (admin)
- Enhanced user profiles (team, manager, computer, mobile phone)
- Alert deletion
- Action logging
- Handover email sending
- Work groups
- Sandbox analysis UI + history + endpoint correlation
- Endpoint inventory dashboard
- Admin-only user management view
- Responsive sidebar (auto-hide on navigation) and fullscreen login
- Utilities with required parameters
- Larger icons throughout the UI
- Alert detail text made larger

### 🚧 Backend Ready, Frontend UI Pending

- Alert escalation UI
- Donut chart for dashboard
- Workplans page UI
- War room page UI
- Rules editing UI (Analytics, Correlation, IoCs, BioCs)
- Profile creation/editing UI (admin)
- Persistent storage (DB) en lugar de memoria

## Next Steps

- Add donut chart visualization to dashboard
- Complete frontend UI for escalation, workplans, war room
- Add rules editing interface
- Implement database persistence (currently in-memory)
- Add real-time updates with WebSockets
- Implement search and filtering
- Connect to real SIEM/EDR systems
- Integrate production email service for handovers
- Integrate VirusTotal API for sandbox analysis
