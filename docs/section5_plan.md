# EventSec Documentation - Section 5 – Advanced Modules & Security Hardening

This document captures the scope, priorities, and implementation plan for the final phase of the EventSec architectural rebuild. The goal is to move from the current single-node manager into an enterprise-grade deployment that mirrors the Wazuh reference architecture: advanced endpoint modules, hardened communications, and production-ready clustering/observability.

---

## 1. Objectives & Deliverables

| Track | Objective | Deliverables |
| --- | --- | --- |
| 1. Advanced Modules | End-to-end data pipeline for inventory, vulnerability detection, SCA, and command monitoring | New agent modules, backend ingestion endpoints, persistence schemas, UI surfacing |
| 2. Secure Transport | TLS/mTLS across API, agent channel, indexer, dashboards; secrets handling | Cert generation utility, config flags, cert mounting in Docker/K8s, key vault integration |
| 3. Cluster & HA | Manager worker pool + DAPI style routing, config distribution, Kubernetes manifests | Leader election or static master/worker roles, state sync, Helm-style manifests |
| 4. Observability & Hygiene | Retention policies, housekeeping jobs, health metrics, CI | Scheduled cleanup services, Prometheus/OpenTelemetry exporters, GitHub Actions smoke tests |

---

## 2. Module Expansion Roadmap

1. **Syscollector / Inventory**
   - Agent: collect hardware, OS, software, network adapters, running processes (extend current telemetry loop).
   - Transport: batch JSON snapshots per category, send via `/agents/{id}/inventory`.
   - Backend: add tables (`agent_inventory_{hardware,software,network,process}`) with versioning; expose `/inventory/agents/:id`.
   - UI: rework `/endpoints` to pull live inventory objects and include timeline (baseline vs. latest).

2. **Vulnerability Detection**
   - Content: seed CVE metadata (mock CTI feed) stored in `vuln_definitions`.
   - Engine: compare inventory software versions → `agent_vulnerabilities`.
   - UI: new dashboard card + `/endpoints/:id` vulnerability tab.

3. **SCA (Security Configuration Assessment)**
   - Agent: run YAML policies (subset) on schedule; send pass/fail results.
   - Backend: store in `sca_results` + `sca_checks`.
   - UI: per-endpoint compliance widget + global summary.

4. **Command Monitoring**
   - Config-driven commands (per group) executed agent-side.
   - Results forwarded as events (already handled by OpenSearch) with special `event_type`.
   - UI: add "Command monitor" stream to events explorer filters.

---

## 3. Security Hardening Plan

1. **TLS Everywhere**
   - Generate CA + server/client certs (mkcert or cfssl) in `infra/certs/`.
   - FastAPI: enable HTTPS (uvicorn w/ certs) + optional `FORCE_HTTPS`.
   - Agent: mutual TLS using client cert & `requests` session pinned to CA.
   - OpenSearch: enable security plugin (or run behind nginx) with cert trust.

2. **Secrets & Config**
   - Move secrets to `.env` + Docker secrets, load via `pydantic-settings`.
   - Support HashiCorp Vault (optional) for agent enrollment keys / JWT secret.

3. **Agent Anti-Tamper**
   - Local file permissions tightening (config + log directories).
   - Process watchdog to relaunch agent modules if killed.

---

## 4. Cluster / HA

1. **Manager Topology**
   - Master node hosts API, scheduler, config store.
   - Worker nodes run agent sockets + processing queues.
   - Introduce lightweight internal message bus (Redis or Postgres LISTEN/NOTIFY) for queue distribution.

2. **Configuration Distribution**
   - Store agent group configs in DB (YAML/JSON).
   - Worker nodes pull config cache; push deltas to agents over `/agents/{id}/config`.

3. **Kubernetes**
   - Add `deploy/k8s/` with:
     - StatefulSet for OpenSearch (single node by default).
     - Deployment + HPA for manager.
     - ConfigMaps/Secrets for certs and env vars.
     - Service mesh annotations (optional) for mTLS.

---

## 5. Observability & Maintenance

1. **Metrics & Logging**
   - Expose `/metrics` (Prometheus) from backend queue, DB, OpenSearch health.
   - Agent: optional StatsD output for resource usage.

2. **Retention Policies**
   - Nightly job to expire old alerts/events from OpenSearch (ILM) and Postgres tables.
   - CLI `eventsecctl prune --alerts --days=30`.

3. **CI / Testing**
   - GitHub Actions pipeline:
     - `backend` lint + pytest (unit tests for CRUD + search integration using OpenSearch test container).
     - `frontend` lint + vitest coverage on key pages.
     - `agent` static checks (flake8, mypy).

---

## 6. Next Actions

1. Expand DB schema (Alembic) for inventory/SCA/vulns tables.
2. Implement agent modules & payload schemas.
3. Add REST endpoints + background jobs for enrichment & vulnerability matching.
4. Wire UI components (inventory tabs, vulnerability widgets, SCA dashboard).
5. Harden transport (TLS, secrets) and publish K8s manifests.
6. Add monitoring endpoints + CI workflows.

---

## 7. Recent Deliverables (Wazuh-inspired)

1. **TLS/mTLS + Secure Secret Storage (Done)**
   - Implemented `SECRET_KEY_FILE`/`AGENT_ENROLLMENT_KEY_FILE`, Docker secrets, optional HTTPS via `SERVER_SSL_*`, and a new `app.server` launcher that enforces cert requirements.
   - Documentation now references the Wazuh docker/k8s practices and explains how to rotate certs/secrets.
   - Reference: still aligned with the public repositories in [Wazuh’s GitHub org](https://github.com/orgs/wazuh/repositories?q=visibility%3Apublic+archived%3Afalse) for future enhancements.

2. **Cluster/HA Configuration & Kubernetes Manifests (Done)**
   - Added `deploy/k8s/` containing Namespace, Postgres, OpenSearch StatefulSet, backend/frontend Deployments, and secret templates mirroring the Wazuh topology (see `wazuh-kubernetes`, `wazuh-docker`).
   - Kustomize-ready; `kubectl apply -k deploy/k8s` now bootstraps an HA-friendly stack.

3. **Monitoring, Retention Jobs, and CI Tests (Done)**
   - `/metrics` is exposed via `prometheus-fastapi-instrumentator`.
   - Created `app.maintenance` (manual or looped) and wired it into a `retention` service + CLI.
   - Introduced `.github/workflows/ci.yml` running backend `pytest`, frontend build, and agent compilation checks—following the QA ethos documented in the Wazuh repos.

> This document serves as the living blueprint for Section 5. Each deliverable above will be broken into PR-sized tasks in subsequent steps.

