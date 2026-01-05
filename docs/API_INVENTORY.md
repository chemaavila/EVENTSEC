# EventSec API Inventory

Source of truth: FastAPI routes in `backend/app/main.py` and `backend/app/routers/*`.

## Service-level endpoints
| Method | Path | Auth | Description | Request | Response |
| --- | --- | --- | --- | --- | --- |
| GET | `/` | Public | Basic health | — | `{status, service}` (`backend/app/main.py`) |
| GET | `/healthz` | Public | Liveness | — | `{status}` (`backend/app/main.py`) |
| GET | `/readyz` | Public | Readiness (DB + OpenSearch) | — | `{status, db, opensearch, error?}` (`backend/app/main.py`) |
| GET | `/metrics` | Public | Prometheus metrics | — | text/plain (`backend/app/main.py`) |

## Auth & profile
| Method | Path | Auth | Description | Request | Response |
| --- | --- | --- | --- | --- | --- |
| POST | `/auth/login` | Public | Login (sets `access_token` cookie) | `LoginRequest` | `LoginResponse` (`backend/app/main.py`) |
| POST | `/auth/logout` | Public | Logout (clears cookie) | — | `{detail}` (`backend/app/main.py`) |
| GET | `/me` | User | Current user profile | — | `UserProfile` (`backend/app/main.py`) |

## Users
| Method | Path | Auth | Description | Request | Response |
| --- | --- | --- | --- | --- | --- |
| GET | `/users` | User | List users | — | `List[UserProfile]` (`backend/app/main.py`) |
| POST | `/users` | Admin | Create user | `UserCreate` | `UserProfile` (`backend/app/main.py`) |
| PATCH | `/users/{user_id}` | Admin | Update user | `UserUpdate` | `UserProfile` (`backend/app/main.py`) |

## Alerts
| Method | Path | Auth | Description | Request | Response |
| --- | --- | --- | --- | --- | --- |
| GET | `/alerts` | User | List alerts | — | `List[Alert]` (`backend/app/main.py`) |
| GET | `/alerts/{alert_id}` | User | Get alert | — | `Alert` (`backend/app/main.py`) |
| POST | `/alerts` | User or agent token | Create alert | `AlertCreate` | `Alert` (`backend/app/main.py`) |
| PATCH | `/alerts/{alert_id}` | User | Update alert | `AlertUpdate` | `Alert` (`backend/app/main.py`) |
| POST | `/alerts/{alert_id}/escalate` | User | Escalate alert | `AlertEscalationCreate` | `AlertEscalation` (`backend/app/main.py`) |
| DELETE | `/alerts/{alert_id}` | User | Delete alert | — | `{detail}` (`backend/app/main.py`) |
| POST | `/alerts/{alert_id}/block-url` | User | Block URL action | — | `{detail}` (`backend/app/main.py`) |
| POST | `/alerts/{alert_id}/unblock-url` | User | Unblock URL | — | `{detail}` (`backend/app/main.py`) |
| POST | `/alerts/{alert_id}/block-sender` | User | Block sender | — | `{detail}` (`backend/app/main.py`) |
| POST | `/alerts/{alert_id}/unblock-sender` | User | Unblock sender | — | `{detail}` (`backend/app/main.py`) |
| POST | `/alerts/{alert_id}/revoke-session` | User | Revoke session | — | `{detail}` (`backend/app/main.py`) |
| POST | `/alerts/{alert_id}/isolate-device` | User | Isolate device | — | `{detail}` (`backend/app/main.py`) |

## Incidents
| Method | Path | Auth | Description | Request | Response |
| --- | --- | --- | --- | --- | --- |
| GET | `/incidents` | User | List incidents | — | `List[Incident]` (`backend/app/routers/incidents_router.py`) |
| GET | `/incidents/{incident_id}` | User | Get incident | — | `Incident` (`backend/app/routers/incidents_router.py`) |
| POST | `/incidents` | User | Create incident | `IncidentCreate` | `Incident` (`backend/app/routers/incidents_router.py`) |
| PATCH | `/incidents/{incident_id}` | User | Update incident | `IncidentUpdate` | `Incident` (`backend/app/routers/incidents_router.py`) |
| POST | `/incidents/{incident_id}/items` | User | Attach incident item | `IncidentItemCreate` | `IncidentItem` (`backend/app/routers/incidents_router.py`) |
| POST | `/incidents/from-alert/{alert_id}` | User | Create incident from alert | — | `Incident` (`backend/app/routers/incidents_router.py`) |
| POST | `/incidents/from-network-event/{event_id}` | User | Create incident from network event | — | `Incident` (`backend/app/routers/incidents_router.py`) |

## Workplans & handovers
| Method | Path | Auth | Description | Request | Response |
| --- | --- | --- | --- | --- | --- |
| GET | `/handover` | User | List handovers | — | `List[Handover]` (`backend/app/main.py`) |
| POST | `/handover` | User | Create handover | `HandoverCreate` | `Handover` (`backend/app/main.py`) |
| GET | `/api/handovers` | User | List handovers (API alias) | — | `List[Handover]` (`backend/app/main.py`) |
| POST | `/api/handovers` | User | Create handover (API alias) | `HandoverCreate` | `Handover` (`backend/app/main.py`) |
| GET | `/api/handovers/{handover_id}` | User | Get handover | — | `Handover` (`backend/app/main.py`) |
| PATCH | `/api/handovers/{handover_id}` | User | Update handover | `HandoverUpdate` | `Handover` (`backend/app/main.py`) |
| GET | `/workplans` | User | List workplans | — | `List[Workplan]` (`backend/app/main.py`) |
| POST | `/workplans` | User | Create workplan | `WorkplanCreate` | `Workplan` (`backend/app/main.py`) |
| PATCH | `/workplans/{workplan_id}` | User | Update workplan | `WorkplanUpdate` | `Workplan` (`backend/app/main.py`) |
| GET | `/api/workplans` | User | List workplans (API alias) | — | `List[Workplan]` (`backend/app/main.py`) |
| GET | `/api/workplans/{workplan_id}` | User | Get workplan | — | `Workplan` (`backend/app/main.py`) |
| POST | `/api/workplans` | User | Create workplan (API alias) | `WorkplanCreate` | `Workplan` (`backend/app/main.py`) |
| PATCH | `/api/workplans/{workplan_id}` | User | Update workplan (API alias) | `WorkplanUpdate` | `Workplan` (`backend/app/main.py`) |
| GET | `/api/workplans/{workplan_id}/items` | User | List items | — | `List[WorkplanItem]` (`backend/app/main.py`) |
| POST | `/api/workplans/{workplan_id}/items` | User | Create item | `WorkplanItemCreate` | `WorkplanItem` (`backend/app/main.py`) |
| PATCH | `/api/workplans/{workplan_id}/items/{item_id}` | User | Update item | `WorkplanItemUpdate` | `WorkplanItem` (`backend/app/main.py`) |
| PATCH | `/api/workplans/{workplan_id}/items` | User | Bulk update items | `WorkplanItemUpdate` | `WorkplanItem` (`backend/app/main.py`) |
| DELETE | `/api/workplans/{workplan_id}/items/{item_id}` | User | Delete item | — | `{detail}` (`backend/app/main.py`) |
| DELETE | `/api/workplans/{workplan_id}/items` | User | Bulk delete items | — | `{detail}` (`backend/app/main.py`) |
| GET | `/api/workplans/{workplan_id}/flow` | User | Get flow | — | `WorkplanFlow` (`backend/app/main.py`) |
| PUT | `/api/workplans/{workplan_id}/flow` | User | Update flow | `WorkplanFlowUpdate` | `WorkplanFlow` (`backend/app/main.py`) |

## Rules & analytics
| Method | Path | Auth | Description | Request | Response |
| --- | --- | --- | --- | --- | --- |
| GET | `/rules/detections` | User | List detection rules | — | `List[DetectionRule]` (`backend/app/routers/rules_router.py`) |
| POST | `/rules/detections` | User | Create detection rule | `DetectionRuleCreate` | `DetectionRule` (`backend/app/routers/rules_router.py`) |
| GET | `/analytics/rules` | User | List analytics rules | — | `List[AnalyticsRule]` (`backend/app/main.py`) |
| GET | `/analytics/rules/{rule_id}` | User | Get analytics rule | — | `AnalyticsRule` (`backend/app/main.py`) |
| POST | `/analytics/rules` | User | Create analytics rule | `AnalyticsRuleCreate` | `AnalyticsRule` (`backend/app/main.py`) |
| PATCH | `/analytics/rules/{rule_id}` | User | Update analytics rule | `AnalyticsRuleUpdate` | `AnalyticsRule` (`backend/app/main.py`) |
| GET | `/api/rules` | User | List analytic/correlation rules | — | `List[AnalyticRule|CorrelationRule]` (`backend/app/main.py`) |
| GET | `/api/rules/{rule_id}` | User | Get analytic/correlation rule | — | `AnalyticRule|CorrelationRule` (`backend/app/main.py`) |
| PATCH | `/api/rules/{rule_id}` | User | Update analytic/correlation rule | `RuleToggleUpdate` | `AnalyticRule|CorrelationRule` (`backend/app/main.py`) |
| POST | `/api/rules/import` | User | Import rules | `RuleImportPayload` | `{detail}` (`backend/app/main.py`) |

## Search & events
| Method | Path | Auth | Description | Request | Response |
| --- | --- | --- | --- | --- | --- |
| POST | `/search/kql` | User | KQL search | `KqlQueryRequest` | `KqlQueryResponse` (`backend/app/routers/kql_router.py`) |
| GET | `/events` | User | Search indexed events | query params | `List[IndexedEvent]` (`backend/app/routers/events_router.py`) |
| POST | `/events` | Agent token/key | Ingest event | `SecurityEventCreate` | `SecurityEvent` (`backend/app/routers/events_router.py`) |
| POST | `/ingest/network/bulk` | User or agent token/key | Network bulk ingest | `NetworkBulkIngestRequest` | `NetworkBulkIngestResponse` (`backend/app/routers/network_router.py`) |
| GET | `/network/events` | User | List network events | query params | `List[NetworkEvent]` (`backend/app/routers/network_router.py`) |
| GET | `/network/sensors` | User | List sensors | — | `List[NetworkSensor]` (`backend/app/routers/network_router.py`) |
| GET | `/network/stats` | User | Network stats | — | `NetworkStats` (`backend/app/routers/network_router.py`) |
| POST | `/threatmap/ingest` | User or agent token/key | Threatmap ingest | `ThreatmapIngestPayload` | `{detail}` (`backend/app/routers/threatmap_router.py`) |

## Agents, EDR/SIEM, inventory, vulnerabilities, SCA
| Method | Path | Auth | Description | Request | Response |
| --- | --- | --- | --- | --- | --- |
| POST | `/agents/enroll` | Public | Agent enrollment | `AgentEnrollRequest` | `AgentEnrollResponse` (`backend/app/routers/agents_router.py`) |
| POST | `/agents/{agent_id}/heartbeat` | Agent token/key | Agent heartbeat | `AgentHeartbeat` | `{detail}` (`backend/app/routers/agents_router.py`) |
| GET | `/agents` | User | List agents | — | `List[Agent]` (`backend/app/routers/agents_router.py`) |
| GET | `/agents/{agent_id}` | User | Get agent | — | `Agent` (`backend/app/routers/agents_router.py`) |
| POST | `/edr/events` | User | Create EDR event | `EdrEventCreate` | `EdrEvent` (`backend/app/routers/edr_router.py`) |
| GET | `/edr/events` | User | List EDR events | — | `List[EdrEvent]` (`backend/app/routers/edr_router.py`) |
| DELETE | `/edr/events` | User | Clear EDR events | — | `{deleted}` (`backend/app/routers/edr_router.py`) |
| POST | `/siem/events` | User | Create SIEM event | `SiemEventCreate` | `SiemEvent` (`backend/app/routers/siem_router.py`) |
| GET | `/siem/events` | User | List SIEM events | — | `List[SiemEvent]` (`backend/app/routers/siem_router.py`) |
| DELETE | `/siem/events` | User | Clear SIEM events | — | `{deleted}` (`backend/app/routers/siem_router.py`) |
| POST | `/inventory/{agent_id}` | Agent token/key | Create inventory snapshot | `InventorySnapshotCreate` | `List[InventorySnapshot]` (`backend/app/routers/inventory_router.py`) |
| GET | `/inventory/{agent_id}` | User | Inventory overview | — | `InventoryOverview` (`backend/app/routers/inventory_router.py`) |
| POST | `/vulnerabilities/definitions` | User | Create vuln definition | `VulnerabilityDefinitionCreate` | `VulnerabilityDefinition` (`backend/app/routers/vulnerabilities_router.py`) |
| GET | `/vulnerabilities/definitions` | User | List vuln definitions | — | `List[VulnerabilityDefinition]` (`backend/app/routers/vulnerabilities_router.py`) |
| GET | `/vulnerabilities/agents/{agent_id}` | User | List agent vulnerabilities | — | `List[AgentVulnerability]` (`backend/app/routers/vulnerabilities_router.py`) |
| POST | `/vulnerabilities/agents/{agent_id}` | User | Add agent vulnerabilities | `List[AgentVulnerabilityCreate]` | `List[AgentVulnerability]` (`backend/app/routers/vulnerabilities_router.py`) |
| POST | `/sca/{agent_id}/results` | Agent token/key | Upload SCA result | `SCAResultCreate` | `SCAResult` (`backend/app/routers/sca_router.py`) |
| GET | `/sca/{agent_id}/results` | User | List SCA results | — | `List[SCAResult]` (`backend/app/routers/sca_router.py`) |

## Response actions, intel, sandbox
| Method | Path | Auth | Description | Request | Response |
| --- | --- | --- | --- | --- | --- |
| GET | `/actions` | User | List response actions | — | `List[ResponseAction]` (`backend/app/routers/actions_router.py`) |
| POST | `/actions` | User | Create response action | `ResponseActionCreate` | `ResponseAction` (`backend/app/routers/actions_router.py`) |
| PATCH | `/actions/{action_id}` | User | Update response action | `ResponseActionUpdate` | `ResponseAction` (`backend/app/routers/actions_router.py`) |
| GET | `/indicators` | User | List indicators | — | `List[Indicator]` (`backend/app/main.py`) |
| POST | `/indicators` | User | Create indicator | `IndicatorCreate` | `Indicator` (`backend/app/main.py`) |
| PATCH | `/indicators/{indicator_id}` | User | Update indicator | `IndicatorUpdate` | `Indicator` (`backend/app/main.py`) |
| GET | `/biocs` | User | List BIOC rules | — | `List[BiocRule]` (`backend/app/main.py`) |
| POST | `/biocs` | User | Create BIOC rule | `BiocRuleCreate` | `BiocRule` (`backend/app/main.py`) |
| PATCH | `/biocs/{rule_id}` | User | Update BIOC rule | `BiocRuleUpdate` | `BiocRule` (`backend/app/main.py`) |
| GET | `/yara/rules` | User | List YARA rules | — | `List[YaraRule]` (`backend/app/main.py`) |
| GET | `/action-logs` | User | List action logs | — | `List[ActionLog]` (`backend/app/main.py`) |
| GET | `/warroom/notes` | User | List warroom notes | — | `List[WarRoomNote]` (`backend/app/main.py`) |
| POST | `/warroom/notes` | User | Create warroom note | `WarRoomNoteCreate` | `WarRoomNote` (`backend/app/main.py`) |
| POST | `/sandbox/analyze` | User | Submit sandbox analysis | `SandboxAnalysisRequest` | `SandboxAnalysisResult` (`backend/app/main.py`) |
| GET | `/sandbox/analyses` | User | List analyses | — | `List[SandboxAnalysisResult]` (`backend/app/main.py`) |
| GET | `/endpoints` | User | List endpoints | — | `List[Endpoint]` (`backend/app/main.py`) |
| GET | `/endpoints/{endpoint_id}` | User | Get endpoint | — | `Endpoint` (`backend/app/main.py`) |
| GET | `/agent/actions` | User | List endpoint actions | — | `List[EndpointAction]` (`backend/app/main.py`) |
| POST | `/agent/actions` | User | Create endpoint action | `EndpointActionCreate` | `EndpointAction` (`backend/app/main.py`) |

## OpenAPI discovery
- FastAPI default `/docs` and `/openapi.json` are enabled unless disabled by config. No explicit override in `backend/app/main.py`.

## Example curl (login + authenticated request)
```bash
curl -s -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@example.com","password":"changeme"}' \
  -c /tmp/eventsec_cookies.txt

curl -s http://localhost:8000/alerts \
  -b /tmp/eventsec_cookies.txt
```
