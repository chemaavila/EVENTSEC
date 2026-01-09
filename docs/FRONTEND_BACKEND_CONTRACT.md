# Frontend ↔ Backend Contract

This document maps UI pages to API calls and DTOs as implemented in `frontend/src/services/*` and `backend/app/*`.

## Shared assumptions
- Auth uses cookie `access_token` set by `POST /auth/login` (`backend/app/main.py`).
- Frontend uses `credentials: "include"` in `apiFetch` (`frontend/src/services/http.ts`).
- Base URL comes from `VITE_API_BASE_URL` or falls back to `http://localhost:8000` in `frontend/src/config/endpoints.ts`.

## Page → API mappings

### Auth & profile
| Page | API calls | DTOs |
| --- | --- | --- |
| Login (`frontend/src/pages/LoginPage.tsx`) | `POST /auth/login`, `POST /auth/logout` | `LoginResponse`, `UserProfile` (`frontend/src/services/api.ts`) |
| Profile (`frontend/src/pages/Profile/ProfilePage.tsx`) | `GET /me` | `UserProfile` |

### Alerts
| Page | API calls | DTOs |
| --- | --- | --- |
| Alerts list (`frontend/src/pages/Alerts/AlertsPage.tsx`) | `GET /alerts`, `POST /alerts` | `Alert`, `AlertCreatePayload` |
| Alert detail (`frontend/src/pages/Alerts/AlertDetailPage.tsx`) | `GET /alerts/{id}`, `PATCH /alerts/{id}`, `POST /alerts/{id}/escalate`, `POST /warroom/notes` | `Alert`, `AlertUpdatePayload`, `AlertEscalationPayload`, `WarRoomNote` |

### Incidents
| Page | API calls | DTOs |
| --- | --- | --- |
| Incidents list (`frontend/src/pages/Incidents/IncidentsPage.tsx`) | `GET /incidents` | `Incident` (`frontend/src/services/incidents.ts`) |
| Incident detail (`frontend/src/pages/Incidents/IncidentDetailPage.tsx`) | `GET /incidents/{id}`, `PATCH /incidents/{id}`, `POST /incidents/{id}/items` | `Incident`, `IncidentUpdatePayload`, `IncidentItem` |

### Workplans & handovers
| Page | API calls | DTOs |
| --- | --- | --- |
| Workplans (`frontend/src/pages/WorkplansPage.tsx`) | `GET /api/workplans`, `POST /api/workplans` | `Workplan`, `WorkplanCreatePayload` |
| Workplan detail (`frontend/src/pages/WorkplanDetailPage.tsx`) | `GET /api/workplans/{id}`, items/flow endpoints | `WorkplanItem`, `WorkplanFlowResponse` |
| Handovers (`frontend/src/pages/Handover/HandoverPage.tsx`) | `GET /api/handovers`, `POST /api/handovers` | `Handover`, `HandoverCreatePayload` |

### Analytics, rules, and intel
| Page | API calls | DTOs |
| --- | --- | --- |
| Analytics rules (`frontend/src/pages/AnalyticsRulesPage.tsx`) | `GET /analytics/rules` | `AnalyticsRule` |
| Correlation rules (`frontend/src/pages/CorrelationRulesPage.tsx`) | `GET /api/rules` | `RuleEntry` |
| Rule library (`frontend/src/pages/RuleLibraryPage.tsx`) | `GET /rules/detections` | `DetectionRule` |
| Indicators/BIOCs (`frontend/src/pages/IocBiocPage.tsx`) | `GET /indicators`, `GET /biocs` | `Indicator`, `BiocRule` |

### Network & search
| Page | API calls | DTOs |
| --- | --- | --- |
| Network overview (`frontend/src/pages/NetworkSecurity/NetworkSecurityOverviewPage.tsx`) | `GET /network/stats`, `GET /network/events` | `NetworkStats`, `NetworkEvent` |
| Network events (`frontend/src/pages/NetworkSecurity/NetworkSecurityEventsPage.tsx`) | `GET /network/events` | `NetworkEvent` |
| Network sensors (`frontend/src/pages/NetworkSecurity/NetworkSecuritySensorsPage.tsx`) | `GET /network/sensors` | `NetworkSensor` |
| Advanced search (`frontend/src/pages/AdvancedSearchPage.tsx`) | `POST /search/kql` | `KqlQueryResponse` |
| Events explorer (`frontend/src/pages/EventsExplorerPage.tsx`) | `GET /events` | `IndexedEvent` |

### EDR/SIEM/Endpoints
| Page | API calls | DTOs |
| --- | --- | --- |
| EDR (`frontend/src/pages/EdrPage.tsx`) | `GET /edr/events`, `DELETE /edr/events` | `EdrEvent` |
| SIEM (`frontend/src/pages/SiemPage.tsx`) | `GET /siem/events`, `DELETE /siem/events` | `SiemEvent` |
| Endpoints (`frontend/src/pages/EndpointsPage.tsx`) | `GET /endpoints`, `GET /endpoints/{id}` | `Endpoint` |
| Software inventory (`frontend/src/pages/SoftwareInventoryPage.tsx`) | `GET /inventory/{agent_id}` | `InventoryOverview` |

### Sandbox
| Page | API calls | DTOs |
| --- | --- | --- |
| Sandbox (`frontend/src/pages/SandboxPage.tsx`) | `POST /sandbox/analyze`, `GET /sandbox/analyses` | `SandboxAnalysisResult` |

### Email protection
| Page | API calls | DTOs |
| --- | --- | --- |
| Email protection (`frontend/src/pages/EmailProtectionPage.tsx`) | `VITE_EMAIL_PROTECT_BASE_URL` endpoints from `frontend/src/lib/emailProtectionApi.ts` | `EmailProtect*` DTOs |

## Contract gaps & mismatches
- **Alert status default mismatch**: DB model default was `draft`, while API schema/TS types expect `open|in_progress|closed`. This can create response model validation failures or UI status handling issues. Fix: align model default to `open` in `backend/app/models.py`.
- **CTI adapter**: API adapter throws when `VITE_CTI_USE_MOCK=false` (`frontend/src/services/cti/apiAdapter.ts`), so real CTI endpoints are not available. Keep mock or implement a real adapter.

## Recommendations
- Keep API DTOs in `frontend/src/services/api.ts` aligned with Pydantic schemas in `backend/app/schemas.py`.
- Consider a single API client that handles 401 globally (redirect to login) for all pages.
