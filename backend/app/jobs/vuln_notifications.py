from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .. import crud, models
from ..config import settings
from ..notifications import NotificationService
from ..services.notifications.vuln_email import (
    build_digest_email,
    build_immediate_email,
)


def _risk_rank(label: str) -> int:
    return {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}.get(label, 0)


def _admin_recipients(db: Session, tenant_id: str) -> List[str]:
    return sorted(
        {
            user.email
            for user in crud.list_users(db)
            if user.role == "admin"
            and user.tenant_id == tenant_id
            and user.email
        }
    )


def _load_findings(
    db: Session, tenant_id: str, finding_ids: List[int]
) -> List[models.AssetVulnerability]:
    stmt = (
        select(models.AssetVulnerability)
        .options(
            joinedload(models.AssetVulnerability.software_component),
            joinedload(models.AssetVulnerability.vulnerability),
        )
        .where(
            models.AssetVulnerability.tenant_id == tenant_id,
            models.AssetVulnerability.id.in_(finding_ids),
        )
    )
    return list(db.scalars(stmt))


def notify_admins(
    db: Session,
    findings: List[models.AssetVulnerability],
    notification_service: NotificationService,
) -> None:
    if not findings:
        return
    immediate_threshold = settings.vuln_intel_notify_immediate_min_risk.upper()
    now = datetime.now(timezone.utc)

    grouped: Dict[str, List[models.AssetVulnerability]] = {}
    for finding in findings:
        if finding.status != "open":
            continue
        if finding.last_notified_at and finding.notified_risk_label:
            if _risk_rank(finding.notified_risk_label) >= _risk_rank(
                finding.risk_label
            ):
                continue
        grouped.setdefault(finding.tenant_id, []).append(finding)

    for tenant_id, tenant_findings in grouped.items():
        recipients = _admin_recipients(db, tenant_id)
        if not recipients:
            continue
        immediate = [
            finding
            for finding in tenant_findings
            if _risk_rank(finding.risk_label) >= _risk_rank(immediate_threshold)
            and (
                finding.confidence >= 0.7
                or (
                    finding.vulnerability
                    and finding.vulnerability.kev
                )
                or (
                    not finding.vulnerability
                    and db.execute(
                        select(models.VulnerabilityRecord.kev).where(
                            models.VulnerabilityRecord.id == finding.vulnerability_id
                        )
                    ).scalar_one_or_none()
                    is True
                )
            )
        ]
        if immediate:
            loaded = _load_findings(db, tenant_id, [f.id for f in immediate])
            payload = build_immediate_email(tenant_id, loaded)
            notification_service.emit(
                db,
                event_type="vuln_immediate",
                entity_type="asset_vulnerability",
                entity_id=loaded[0].id,
                recipients=recipients,
                payload=payload,
            )
            for finding in immediate:
                finding.last_notified_at = now
                finding.notified_risk_label = finding.risk_label
                db.add(finding)
            db.commit()

        if settings.vuln_intel_notify_digest_enabled:
            digest = [
                finding
                for finding in tenant_findings
                if finding.risk_label in {"HIGH", "MEDIUM"}
            ]
            if digest:
                loaded = _load_findings(db, tenant_id, [f.id for f in digest])
                payload = build_digest_email(tenant_id, loaded)
                notification_service.emit(
                    db,
                    event_type="vuln_digest",
                    entity_type="asset_vulnerability",
                    entity_id=loaded[0].id,
                    recipients=recipients,
                    payload=payload,
                )
                for finding in digest:
                    finding.last_notified_at = now
                    finding.notified_risk_label = finding.risk_label
                    db.add(finding)
                db.commit()


def create_alerts_for_critical(
    db: Session, findings: List[models.AssetVulnerability]
) -> None:
    if not settings.vuln_intel_create_alerts_for_critical:
        return
    now = datetime.now(timezone.utc)
    recent_window = now - timedelta(hours=6)
    critical = [
        finding
        for finding in findings
        if finding.risk_label == "CRITICAL"
        and (
            finding.confidence >= 0.7
            or (
                finding.vulnerability
                and finding.vulnerability.kev
            )
            or (
                not finding.vulnerability
                and db.execute(
                    select(models.VulnerabilityRecord.kev).where(
                        models.VulnerabilityRecord.id == finding.vulnerability_id
                    )
                ).scalar_one_or_none()
                is True
            )
        )
    ]
    if not critical:
        return
    for finding in critical:
        agent = crud.get_agent_by_id(db, finding.asset_id)
        hostname = agent.name if agent else f"asset-{finding.asset_id}"
        existing = db.execute(
            select(models.Alert).where(
                models.Alert.source == "vuln_intel",
                models.Alert.hostname == hostname,
                models.Alert.created_at >= recent_window,
            )
        ).scalar_one_or_none()
        if existing:
            continue
        alert = models.Alert(
            title=f"Critical vulnerabilities detected on {hostname}",
            description="Automatic alert generated from vulnerability intelligence.",
            source="vuln_intel",
            category="vulnerability",
            severity="critical",
            status="open",
            hostname=hostname,
        )
        crud.create_alert(db, alert)
