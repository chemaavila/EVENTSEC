# EventSec Documentation - Feature Checklist

This document tracks every change the user requested across the multi-phase rebuild. Each item references the current implementation status as of Section 5 (inventory/vulnerability/SCA) completion.

| Area | Requirement | Status | Notes / References |
| --- | --- | --- | --- |
| Authentication | Require login everywhere, JWT-based, admin can create users/profiles | ✅ | `backend/app/auth.py`, `/auth/login`, React `AuthContext` |
| RBAC & Roles | Roles: admin, team_lead, analyst, senior_analyst | ✅ | Enforced in frontend routes (`ProtectedRoute`, `AdminRoute`) |
| Profile Fields | Profile shows team/manager/computer/mobile; admin can edit | ✅ | `UserManagementPage`, profile schema |
| Handovers | Create handovers, optional email sending | ✅ | `/handover` endpoints, frontend page |
| Alert UX | Larger alert text & delete button | ✅ | `AlertDetailPage.tsx` |
| Escalation | Escalate alerts to specific users | ✅ | `/alerts/{id}/escalate`, UI form |
| Utilities | Require parameters (URL/sender/user/host) & log actions | ✅ | Utilities inputs + `log_action` helper |
| Icons & Sidebar | Bigger icons, responsive (auto-close on nav) | ✅ | `Sidebar.tsx` |
| Sandbox | VT/OSINT/YARA integration, dedicated tab | ✅ | `SandboxPage.tsx` (+ `/sandbox` APIs) |
| Notes/Documents | War Room with attachments | ✅ | `/warroom/notes`, alert War Room tab |
| Workplans | Create/assign/update workplans linked to alerts | ✅ | `/workplans`, `WorkplansPage.tsx` |
| Rules Editing | IOC/BIOC + Analytics rule CRUD | ✅ | `IocBiocPage`, `AnalyticsRulesPage`, backend routers |
| War Room vs Workplan | Notes moved from workplan to War Room | ✅ | Active tabs default to War Room |
| Endpoint Inventory | Dedicated page with stats, processes, remote actions | ✅ | `/endpoints` page & API |
| Endpoint Control | Isolate/release/reboot/command actions with agent acknowledgment | ✅ | `/endpoints/{id}/actions`, agent `process_actions()` |
| Agent Executable | PyInstaller builds w/ config wizard & token headers | ✅ | `build_*.sh`, agent config |
| Refresh Buttons | All sections refresh without logging out | ✅ | `loadEvents()` / `loadData()` changes |
| Login Page | Standalone full-screen form (no header/sidebar) | ✅ | `LoginPage.tsx`, conditional chrome |
| SIEM/EDR Details | Clicking events opens detailed modal | ✅ | `SiemPage.tsx`, `EdrPage.tsx` |
| YARA Integration | Sandbox lists YARA rules & matches | ✅ | `sandbox` API + UI |
| Network Telemetry | Agent sends phishing events, backend auto-alert | ✅ | `build_network_event`, `create_alert_from_network_event()` |
| Donut Chart | Dashboard severity donut chart | ✅ | `DashboardPage.tsx` |
| Dashboard Feed | Network telemetry modal + OpenSearch feed | ✅ | Added card + `searchEvents()` |
| Events Explorer | `/events` page with Lucene/WQL bar, modal JSON | ✅ | `EventsExplorerPage.tsx`, `search_events()` |
| OpenSearch Plane | Backend indexes events/alerts, dockerized OpenSearch | ✅ | `backend/app/search.py`, docker compose service |
| Inventory API | `/inventory/{agent}` ingest + overview (Section 5) | ✅ | `inventory_router`, agent snapshots |
| Vulnerability Module | CVE definitions, agent evaluation, storage | ✅ | `vulnerabilities_router`, new tables |
| SCA Module | Agent uploads CIS benchmark results, UI-ready API | ✅ | `sca_router`, agent periodic uploads |
| Documentation | README/USAGE updated with new sections | ✅ | Latest docs describe inventory/vuln/sca features |
| TLS & Secrets | HTTPS toggle, mTLS-ready cert mounts, secret files/ Docker secrets | ✅ | `app.server`, new env vars, Compose secrets |
| Kubernetes / HA | Manifests under `deploy/k8s/` (Namespace, Postgres, OpenSearch, backend/frontend) | ✅ | Kustomize-ready; mirrors Wazuh guidance |
| Monitoring & CI | `/metrics`, retention CLI/service, GitHub Actions pipeline | ✅ | `prometheus-fastapi-instrumentator`, `app.maintenance`, `.github/workflows/ci.yml` |

Legend: ✅ implemented · ⏳ planned/in progress · ❌ not started

