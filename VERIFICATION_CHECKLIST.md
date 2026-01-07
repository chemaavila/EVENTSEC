# EventSec Documentation - Verification Checklist

## ✅ Backend Verification

### Authentication
- ✅ JWT generation and validation (stored in HttpOnly cookie for UI)
- ✅ Password hashing with bcrypt
- ✅ Login endpoint (`/auth/login`)
- ✅ Protected routes with `get_current_user` dependency
- ✅ Admin-only routes with `get_current_admin_user` dependency
- ✅ Default users created on startup (admin, analyst)

### User Management
- ✅ User creation endpoint (admin only)
- ✅ User update endpoint (admin only)
- ✅ User listing endpoint (admin only)
- ✅ Enhanced user profile schema (team, manager, computer, mobile_phone)

### Alerts
- ✅ All alert endpoints require authentication
- ✅ Alert deletion endpoint
- ✅ Alert escalation endpoint
- ✅ Utility actions require query parameters:
  - ✅ `block-url` requires `url` parameter
  - ✅ `unblock-url` requires `url` parameter
  - ✅ `block-sender` requires `sender` parameter
  - ✅ `unblock-sender` requires `sender` parameter
  - ✅ `revoke-session` requires `username` parameter
  - ✅ `isolate-device` requires `hostname` parameter
- ✅ All utility actions are logged

### Handovers
- ✅ Handover creation with email support
- ✅ `send_email` and `recipient_emails` fields in schema
- ✅ Email sending simulated (ready for production service)

### Work Groups
- ✅ Work group creation (team_lead/admin only)
- ✅ Work group listing

### Workplans
- ✅ Workplan creation
- ✅ Workplan assignment to alerts and users

### War Room
- ✅ War room note creation
- ✅ Notes can be associated with alerts
- ✅ Attachment support in schema

### Sandbox
- ✅ Sandbox analysis endpoint
- ✅ Support for file, IP, URL, domain, hash
- ✅ VT and OSINT results structure

### Action Logging
- ✅ All utility actions logged
- ✅ Admin can view action logs

### Data Lake (Tenant Scoped)
- ✅ Tenant storage policy endpoints respond (GET/PUT `/tenants/{tenant_id}/storage-policy`)
- ✅ Usage endpoints return 403 until `data_lake_enabled` is true
- ✅ Usage export CSV works (`/tenants/{tenant_id}/usage/export.csv`)

## ✅ Frontend Verification

### Authentication
- ✅ Login page created
- ✅ AuthContext for state management
- ✅ Protected routes wrapper
- ✅ HttpOnly cookie (`access_token`) used for auth
- ✅ Automatic session validation on app load (`/me`)
- ✅ Logout functionality

### API Integration
- ✅ All API calls include credentials (`credentials: "include"`)
- ✅ Login function implemented
- ✅ Error handling for authentication failures

### Alert Detail Page
- ✅ Larger text for alert details
- ✅ Delete button with confirmation
- ✅ Utilities tab with parameter inputs:
  - ✅ URL input field
  - ✅ Sender email input field
  - ✅ Username input field
  - ✅ Hostname input field
- ✅ All action buttons disabled until parameters provided
- ✅ Success/error messages displayed

### Topbar
- ✅ User information displayed
- ✅ Logout button
- ✅ User initials in avatar

### Sidebar
- ✅ Icons increased to 28x28 (from 24x24)
- ✅ All navigation links working

### Handover Page
- ✅ Email sending fields in form (backend ready)
- ⚠️ Frontend UI for email fields needs to be added

## ⚠️ Known Issues / Pending

### Frontend UI Pending
- ⚠️ Handover email fields UI (backend ready)
- ⚠️ Alert escalation UI (backend ready)
- ⚠️ Donut chart for dashboard
- ⚠️ Sandbox page UI
- ⚠️ Workplans page UI
- ⚠️ War room page UI
- ⚠️ Rules editing UI
- ⚠️ Profile creation/editing UI (admin)

### Minor Issues
- ⚠️ Sidebar route: `/handovers` vs `/handover` (check consistency)
- ⚠️ Circular import in auth.py (lazy import, should work but could be improved)

## 🔧 Testing Recommendations

1. **Test Authentication Flow:**
   - Login with admin credentials
   - Login with analyst credentials
   - Try accessing protected route without login
   - Test logout

2. **Test Alert Actions:**
   - Create an alert
   - Try utility actions without parameters (should fail)
   - Try utility actions with parameters (should succeed)
   - Delete an alert

3. **Test User Management (as admin):**
   - List users
   - Create new user
   - Update user

4. **Test API Endpoints:**
   - Use Swagger UI at `/docs`
   - Test with and without authentication
   - Verify all query parameters work

## 📝 Notes

- All backend endpoints are properly protected
- All utility actions require parameters and are logged
- Authentication is required for all routes
- Default credentials are seeded on startup
- Email sending is simulated (ready for production integration)
- Sandbox analysis is simulated (ready for VT/OSINT API integration)

## 🧪 Agent Verification in UTM VM

1. **Create VM**: In UTM, create a new VM with a supported OS (Ubuntu 22.04 or Windows 10/11). Allocate at least 2 vCPU, 4 GB RAM.
2. **Networking**: Use shared networking or bridged mode so the VM can reach the EventSec backend (default `http://host:8000`). Confirm `ping <host>` works.
3. **Install prerequisites (if needed)**:
   - Linux/macOS VM: none required for the packaged agent; just make it executable (`chmod +x eventsec-agent`).
   - Windows VM: none required; the `.exe` is self-contained.
4. **Copy agent artifacts**: From `agent-share/bin/`, copy the OS-appropriate binary (`eventsec-agent` or `eventsec-agent.exe` or `eventsec-agent.app`) and `agent_config.json` into the VM (e.g., `~/eventsec-agent/` or `C:\EventSecAgent\`).
5. **Configure**: Edit `agent_config.json` inside the VM:
   - `api_url`: URL to your backend (e.g., `http://<host-ip>:8000`)
   - `agent_token`: must match backend `EVENTSEC_AGENT_TOKEN`
   - `enrollment_key`: must match backend `AGENT_ENROLLMENT_KEY`
6. **Run**:
   - Windows: double-click `eventsec-agent.exe`
   - macOS: open `eventsec-agent.app`
   - Linux: `chmod +x eventsec-agent && ./eventsec-agent`
7. **Verify connectivity**:
   - Check VM logs: `agent.log` next to the binary (fallback `~/.eventsec-agent/agent.log`)
   - In backend: agent appears under Endpoints; status online; heartbeats received.
8. **Generate activity**:
   - Create a small test log line in a monitored path (e.g., `echo "test warning" | sudo tee -a /var/log/syslog`) and confirm it arrives as an event.
9. **Disconnection test**:
   - Stop the agent and confirm it transitions to offline within the UI (or fails heartbeats).
10. **Repeat for each OS profile you support** (Windows, Linux, macOS) to validate packaging and connectivity inside UTM.
