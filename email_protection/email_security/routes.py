import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from email_security.models import (
    AnalyzerSubmit,
    AnalyzerVerdict,
    ConnectorCreate,
    DomainCreate,
    IdentityProviderConfig,
    IngestMessage,
    IngestResponse,
    PolicyCreate,
    TenantCreate,
)
from email_security.policy import evaluate_policies
from email_security.storage import (
    create_analyzer_job,
    create_connector,
    create_domain,
    create_policy,
    create_quarantine,
    create_tenant,
    enqueue_message,
    list_connectors,
    list_domains,
    list_policies,
    list_quarantine,
    list_siem_events,
    list_tenants,
    record_audit,
    record_message,
    record_siem_event,
    release_quarantine,
    report_summary,
    update_analyzer_job,
    upsert_identity_provider,
    get_identity_provider,
    verify_domain,
)

router = APIRouter(prefix="/email-protection", tags=["email-protection"])

URL_DEFENSE_BASE = os.getenv(
    "EMAIL_PROTECT_URL_DEFENSE_BASE", "https://linkprotect.eventsec.local/redirect"
)


@router.post("/tenants")
def create_tenant_endpoint(payload: TenantCreate):
    return create_tenant(payload)


@router.get("/tenants")
def list_tenants_endpoint():
    return list_tenants()


@router.post("/domains")
def create_domain_endpoint(payload: DomainCreate):
    return create_domain(payload)


@router.get("/domains")
def list_domains_endpoint(tenant_id: str):
    return list_domains(tenant_id)


@router.post("/domains/{domain_id}/verify")
def verify_domain_endpoint(domain_id: str, token: str):
    record = verify_domain(domain_id, token)
    if not record:
        raise HTTPException(status_code=400, detail="Invalid token")
    return record


@router.post("/policies")
def create_policy_endpoint(payload: PolicyCreate):
    return create_policy(payload)


@router.get("/policies")
def list_policies_endpoint(tenant_id: str, direction: Optional[str] = None):
    return list_policies(tenant_id, direction)


@router.post("/connectors")
def create_connector_endpoint(payload: ConnectorCreate):
    return create_connector(payload)


@router.get("/connectors")
def list_connectors_endpoint(tenant_id: str):
    return list_connectors(tenant_id)


@router.post("/ingest", response_model=IngestResponse)
def ingest_message(payload: IngestMessage):
    policies = [p.model_dump() if hasattr(p, "model_dump") else p for p in list_policies(payload.tenant_id)]
    score, verdict, actions, detections = evaluate_policies(payload, policies, URL_DEFENSE_BASE)
    message_id = record_message(payload, verdict, score, [a.model_dump() for a in actions])
    enqueue_message(payload.tenant_id, message_id, {"verdict": verdict, "score": score})
    quarantine_id: Optional[str] = None
    if verdict in {"quarantined", "blocked"}:
        record = create_quarantine(payload.tenant_id, message_id, detections.get("reasons", ["policy"])[-1])
        quarantine_id = record.id
    record_siem_event(
        payload.tenant_id,
        "message_received",
        message_id,
        {"verdict": verdict, "score": score, "detections": detections},
    )
    return IngestResponse(
        message_id=message_id,
        verdict=verdict,
        score=score,
        actions=actions,
        quarantine_id=quarantine_id,
    )


@router.get("/quarantine")
def list_quarantine_endpoint(tenant_id: str):
    return list_quarantine(tenant_id)


@router.post("/quarantine/{quarantine_id}/release")
def release_quarantine_endpoint(quarantine_id: str, tenant_id: str, actor: str = "system"):
    record = release_quarantine(quarantine_id)
    if not record:
        raise HTTPException(status_code=404, detail="Not found")
    record_audit(tenant_id, actor, "quarantine_release", quarantine_id, {"message_id": record.message_id})
    record_siem_event(tenant_id, "quarantine_released", record.message_id, {"quarantine_id": quarantine_id})
    return record


@router.get("/reports/summary")
def report_summary_endpoint(tenant_id: str):
    return report_summary(tenant_id)


@router.get("/health")
def health_endpoint(tenant_id: str):
    data = report_summary(tenant_id)
    data["gateway_status"] = "healthy"
    data["queue_depth"] = 0
    data["analyzer_status"] = "optional"
    return data


@router.post("/analyzer/submit")
def analyzer_submit(payload: AnalyzerSubmit):
    job_id = create_analyzer_job(payload)
    record_siem_event(
        payload.tenant_id,
        "analyzer_submitted",
        payload.message_id,
        {"job_id": job_id, "sample_type": payload.sample_type},
    )
    return {"job_id": job_id, "status": "submitted"}


@router.post("/analyzer/verdict")
def analyzer_verdict(payload: AnalyzerVerdict):
    job_id = update_analyzer_job(payload)
    if not job_id:
        raise HTTPException(status_code=404, detail="Job not found")
    record_siem_event(
        payload.tenant_id,
        "analyzer_verdict",
        None,
        {"job_id": job_id, "verdict": payload.verdict, "iocs": payload.iocs},
    )
    return {"job_id": job_id, "status": "completed"}


@router.get("/siem/events")
def siem_events_endpoint(tenant_id: str, limit: int = 100):
    return list_siem_events(tenant_id, limit)


@router.post("/identity/entra")
def upsert_entra_config(payload: IdentityProviderConfig):
    upsert_identity_provider(payload.tenant_id, payload.issuer, payload.client_id, payload.metadata)
    return {"status": "saved"}


@router.get("/identity/entra")
def get_entra_config(tenant_id: str):
    config = get_identity_provider(tenant_id)
    if not config:
        raise HTTPException(status_code=404, detail="Not configured")
    return config
