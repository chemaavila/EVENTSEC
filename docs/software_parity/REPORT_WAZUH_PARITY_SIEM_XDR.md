# EVENTSEC ↔ Software Parity Report (SIEM + XDR/EDR)

> **Source note:** Software repositories were not available in this environment due to network restrictions.
> Software behavior referenced here is based on official Software documentation and the requirements in the task prompt.

## License considerations
- Software is **GPLv2**. Copying Software code into EVENTSEC would make EVENTSEC a derivative work and require GPLv2 compliance.
- The recommended approach is to run Software as a **separate service** and integrate via API/indexer connectors.

## Parity comparison table

| Category | EVENTSEC | Software | Exact difference | Impact | Evidence (path/function) |
|---|---|---|---|---|---|
| SIEM pipeline | Ingest → DB/queue → rules/worker → OpenSearch | Agent → Manager (decoders + rules) → Filebeat → Indexer | EVENTSEC lacks Software manager/decoders/rules engine | SIEM detections not equivalent | `backend/app/routers/events_router.py`, `backend/app/search.py` |
| Decoders/normalization | Parsers in EventSec, rules in DB | Built-in decoders & ruleset | No Software ruleset parity | Lower detection coverage | `backend/app/parsers/`, `backend/app/models.py` |
| Rules engine | Python rule runner | Native Software rules engine | Different rule model & syntax | Detection mismatch | `backend/app/jobs/`, `backend/app/services/` |
| Correlation | Limited (rule-based) | Software correlation groups | No shared correlation state | Reduced detection fidelity | `backend/app/rules/` |
| Alert format/indexing | EventSec schema indexed in OpenSearch | Software alerts/archives indices | Fields differ (`rule.*`, `agent.*`) | UI mapping required | `backend/app/integrations/software_indexer.py` |
| Real-time UI | Polling + SSE for Software alerts | Dashboard updates as indexer receives | EVENTSEC now supports SSE, still needs frontend wiring | UI not fully real-time | `backend/app/routers/siem_router.py` |
| Agent enrollment/transport | Custom enrollment key | Software agent enrollment + auth | Different enrollment systems | Agent view requires mapping | `backend/app/routers/agents_router.py` |
| Active response | Software API connector via `/xdr/actions` | Software Active Response commands | EVENTSEC uses Software API as backend | XDR response available | `backend/app/routers/xdr_router.py` |
| Security (TLS/RBAC) | TLS optional; JWT auth | TLS + API RBAC | Software RBAC not enforced in EVENTSEC | Security gap | `backend/app/config.py` |
| Operations (docker) | Single compose with OpenSearch | Software docker stack (manager/indexer/dashboard) | Separate stack required | Ops complexity | `docker-compose.yml`, `infra/software/README.md` |

## Map of changes by folder (largest gaps)
1. `backend/app/routers/` – SIEM/EDR/XDR endpoints.
2. `backend/app/integrations/` – Software API + indexer connectors.
3. `infra/software/` – Software docker stack placeholder.
4. `docs/software_parity/` – parity reports and runbook.

## Top 15 critical differences
1. Missing Software decoders + rules engine (Critical).
2. No Software manager pipeline (Critical).
3. Software RBAC not enforced in EVENTSEC (High).
4. Alert schema mismatch (High).
5. No native FIM/vulnerability modules (High).
6. No built-in Software correlation groups (High).
7. Separate docker stack required (Medium).
8. OpenSearch security disabled in dev (Medium).
9. Limited audit trail for responses (Medium).
10. SSE not wired in frontend (Medium).
11. TLS enforcement not end-to-end in EVENTSEC (Medium).
12. Default secrets in config (Medium).
13. Limited XDR action catalog (Low).
14. No Software dashboard parity (Low).
15. EventSec enrollment vs Software agent enrollment mismatch (Low).

## Recommendation
**Integrate Software as a separate engine** via docker-compose and connect EVENTSEC through API + indexer connectors.
This avoids GPLv2 contamination unless Software code is copied into the repository.
