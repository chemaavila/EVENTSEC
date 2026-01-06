from __future__ import annotations

import logging
import os
import secrets
import threading
import time
from collections import deque
from datetime import datetime
from typing import Deque, Dict, Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request
from sqlalchemy.orm import Session

from .. import crud, models, schemas, search
from ..auth import get_optional_user
from ..config import settings
from ..database import get_db
from ..notifications import (
    NotificationService,
    build_alert_url,
    resolve_level_recipients,
    resolve_manager_recipients,
)

logger = logging.getLogger("eventsec.passwordguard")

router = APIRouter(prefix="/api/v1/password-guard", tags=["password-guard"])
notification_service = NotificationService()

_RATE_LIMIT_LOCK = threading.Lock()
_RATE_LIMIT_BUCKETS: Dict[str, Deque[float]] = {}
_RATE_LIMIT_WINDOW_SECONDS = 60


def _shared_agent_token() -> Optional[str]:
    return os.getenv("EVENTSEC_AGENT_TOKEN")


def _verify_agent_token(token: Optional[str]) -> bool:
    if not token:
        return False
    shared = _shared_agent_token()
    if not shared:
        return False
    return secrets.compare_digest(token, shared)


def _require_agent_auth(
    current_user: Optional[schemas.UserProfile],
    agent_token: Optional[str],
    agent_key: Optional[str],
    db: Session,
) -> Optional[models.Agent]:
    if current_user:
        return None
    if agent_key:
        agent = crud.get_agent_by_api_key(db, agent_key)
        if agent:
            return agent
    if agent_token and settings.environment.lower() == "production":
        raise HTTPException(
            status_code=401,
            detail="Shared agent token authentication is disabled in production.",
        )
    if _verify_agent_token(agent_token):
        return None
    raise HTTPException(status_code=401, detail="Invalid authentication credentials")


def _resolve_tenant_id(
    current_user: Optional[schemas.UserProfile],
    tenant_header: Optional[str],
) -> str:
    if current_user and current_user.tenant_id:
        return current_user.tenant_id
    if tenant_header:
        return tenant_header
    return "default"


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:  # pragma: no cover - validation fallback
        raise HTTPException(status_code=400, detail="Invalid datetime format") from exc


def _enforce_rate_limit(host_id: str) -> None:
    now = time.monotonic()
    with _RATE_LIMIT_LOCK:
        bucket = _RATE_LIMIT_BUCKETS.setdefault(host_id, deque())
        while bucket and now - bucket[0] > _RATE_LIMIT_WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= settings.password_guard_rate_limit_per_minute:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded for host_id",
            )
        bucket.append(now)


def _event_to_schema(event: models.PasswordGuardEvent) -> schemas.PasswordGuardEvent:
    return schemas.PasswordGuardEvent(
        id=event.id,
        tenant_id=event.tenant_id,
        host_id=event.host_id,
        user=event.user,
        entry_id=event.entry_id,
        entry_label=event.entry_label,
        exposure_count=event.exposure_count,
        action=event.action,
        timestamp=event.event_ts,
        client_version=event.client_version,
        alert_id=event.alert_id,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


def _resolve_alert_level(severity: str) -> int:
    return 2 if severity in {"high", "critical"} else 1


@router.post(
    "/events",
    response_model=schemas.PasswordGuardEvent,
    status_code=201,
    summary="Ingest PasswordGuard events",
)
async def ingest_password_guard_event(
    request: Request,
    payload: schemas.PasswordGuardEventCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: Optional[schemas.UserProfile] = Depends(get_optional_user),
    agent_token: Optional[str] = Header(None, alias="X-Agent-Token"),
    agent_key: Optional[str] = Header(None, alias="X-Agent-Key"),
    tenant_id: Optional[str] = Header(None, alias="X-Tenant-Id"),
) -> schemas.PasswordGuardEvent:
    agent = _require_agent_auth(current_user, agent_token, agent_key, db)
    resolved_tenant = _resolve_tenant_id(current_user, tenant_id)

    _enforce_rate_limit(payload.host_id)

    event = models.PasswordGuardEvent(
        tenant_id=resolved_tenant,
        host_id=payload.host_id,
        user=payload.user,
        entry_id=payload.entry_id,
        entry_label=payload.entry_label,
        exposure_count=payload.exposure_count,
        action=payload.action,
        event_ts=payload.timestamp,
        client_version=payload.client_version,
    )
    event = crud.create_password_guard_event(db, event)

    if payload.action == "DETECTED" and payload.exposure_count > 0:
        description = (
            "PasswordGuard detected a compromised password entry."
            f" Entry='{payload.entry_label}', host='{payload.host_id}', user='{payload.user}',"
            f" exposures={payload.exposure_count}."
        )
        alert = models.Alert(
            title="Pwned password detected",
            description=description,
            source="passwordguard",
            category="credential",
            severity="high",
            status="open",
            username=payload.user,
            hostname=payload.host_id,
        )
        alert = crud.create_alert(db, alert)
        event.alert_id = alert.id
        db.add(event)
        db.commit()
        db.refresh(event)

        try:
            search.index_alert(
                {
                    "alert_id": alert.id,
                    "title": alert.title,
                    "severity": alert.severity,
                    "status": alert.status,
                    "category": alert.category,
                    "timestamp": alert.created_at.isoformat() if alert.created_at else None,
                    "details": schemas.Alert.model_validate(alert).model_dump(),
                }
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to index PasswordGuard alert %s: %s", alert.id, exc)

        level = _resolve_alert_level(alert.severity)
        recipients = resolve_manager_recipients(db) + resolve_level_recipients(db, level)
        notification_service.emit(
            db,
            event_type="ALERT_CREATED",
            entity_type="alert",
            entity_id=alert.id,
            recipients=recipients,
            payload={
                "subject": f"New alert #{alert.id}: {alert.title}",
                "body": f"Alert created with severity {alert.severity}.",
                "title": alert.title,
                "severity": alert.severity,
                "status": alert.status,
                "level": level,
                "owner_id": alert.owner_id,
                "alert_url": build_alert_url(alert.id),
            },
        )

    token_id = "unknown"
    if current_user:
        token_id = f"user:{current_user.id}"
    elif agent:
        token_id = f"agent:{agent.id}"
    elif agent_key:
        token_id = f"agent-key:{agent_key[:6]}***"
    elif agent_token:
        token_id = "shared-agent-token"

    audit = models.PasswordGuardIngestAudit(
        event_id=event.id,
        tenant_id=resolved_tenant,
        ingested_by_user_id=current_user.id if current_user else None,
        agent_id=agent.id if agent else None,
        token_id=token_id,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    crud.create_password_guard_ingest_audit(db, audit)

    return _event_to_schema(event)


@router.get(
    "/events",
    response_model=list[schemas.PasswordGuardEvent],
    summary="List PasswordGuard events",
)
def list_password_guard_events(
    db: Session = Depends(get_db),
    current_user: Optional[schemas.UserProfile] = Depends(get_optional_user),
    tenant_id: Optional[str] = Query(None),
    host_id: Optional[str] = Query(None),
    user: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    time_from: Optional[str] = Query(None, alias="from"),
    time_to: Optional[str] = Query(None, alias="to"),
) -> list[schemas.PasswordGuardEvent]:
    resolved_tenant = _resolve_tenant_id(current_user, tenant_id)
    events = crud.list_password_guard_events(
        db,
        tenant_id=resolved_tenant if resolved_tenant else None,
        host_id=host_id,
        user=user,
        action=action,
        time_from=_parse_datetime(time_from),
        time_to=_parse_datetime(time_to),
    )
    return [_event_to_schema(event) for event in events]


@router.get(
    "/alerts",
    response_model=list[schemas.PasswordGuardAlert],
    summary="List PasswordGuard alerts",
)
def list_password_guard_alerts(
    db: Session = Depends(get_db),
    current_user: Optional[schemas.UserProfile] = Depends(get_optional_user),
    tenant_id: Optional[str] = Query(None),
    host_id: Optional[str] = Query(None),
    user: Optional[str] = Query(None),
) -> list[schemas.PasswordGuardAlert]:
    resolved_tenant = _resolve_tenant_id(current_user, tenant_id)
    alerts = crud.list_password_guard_alerts(
        db,
        tenant_id=resolved_tenant if resolved_tenant else None,
        host_id=host_id,
        user=user,
    )
    return [
        schemas.PasswordGuardAlert(
            alert=schemas.Alert.model_validate(alert),
            event=_event_to_schema(event) if event else None,
        )
        for alert, event in alerts
    ]
