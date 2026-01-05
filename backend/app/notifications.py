from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import crud, models
from .config import settings

logger = logging.getLogger("eventsec.notifications")


def bucket_time(now: Optional[datetime] = None) -> datetime:
    timestamp = now or datetime.now(timezone.utc)
    bucket_minutes = max(settings.notification_dedup_minutes, 1)
    minute_bucket = (timestamp.minute // bucket_minutes) * bucket_minutes
    return timestamp.replace(minute=minute_bucket, second=0, microsecond=0)


def parse_recipients(raw: str) -> List[str]:
    return [value.strip() for value in raw.split(",") if value.strip()]


class EmailService:
    def send(self, event: models.NotificationEvent) -> None:
        subject = event.payload.get("subject", f"[EventSec] {event.event_type}")
        body = event.payload.get("body", "")
        if settings.environment.lower() == "production":
            logger.info(
                "[EMAIL] (stub) Would send %s to %s",
                event.event_type,
                event.recipient_email,
            )
        else:
            logger.info(
                "[EMAIL-OUTBOX] %s -> %s subject=%s body=%s",
                event.event_type,
                event.recipient_email,
                subject,
                body,
            )


class NotificationService:
    def __init__(self, email_service: Optional[EmailService] = None) -> None:
        self.email_service = email_service or EmailService()

    def emit(
        self,
        db: Session,
        *,
        event_type: str,
        entity_type: str,
        entity_id: int,
        recipients: Iterable[str],
        payload: Dict[str, Any],
    ) -> List[models.NotificationEvent]:
        created_events: List[models.NotificationEvent] = []
        bucket = bucket_time()
        recipient_list = sorted({r for r in recipients if r})
        for recipient in recipient_list:
            event = models.NotificationEvent(
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                recipient_email=recipient,
                recipients=recipient_list,
                payload=payload,
                status="queued",
                bucket_time=bucket,
            )
            try:
                crud.create_notification_event(db, event)
            except IntegrityError:
                db.rollback()
                existing = db.execute(
                    select(models.NotificationEvent).where(
                        models.NotificationEvent.event_type == event_type,
                        models.NotificationEvent.entity_type == entity_type,
                        models.NotificationEvent.entity_id == entity_id,
                        models.NotificationEvent.recipient_email == recipient,
                        models.NotificationEvent.bucket_time == bucket,
                    )
                ).scalar_one_or_none()
                if existing and existing.status == "queued":
                    existing.status = "skipped_dedup"
                    db.add(existing)
                    db.commit()
                continue

            try:
                self.email_service.send(event)
                event.status = "sent"
                event.sent_at = datetime.now(timezone.utc)
            except Exception as exc:  # noqa: BLE001
                event.status = "failed"
                event.error = str(exc)
            db.add(event)
            db.commit()
            db.refresh(event)
            created_events.append(event)
        return created_events


def resolve_manager_recipients(db: Session) -> List[str]:
    managers = [
        user.email
        for user in crud.list_users(db)
        if user.role in {"team_lead", "admin"} and user.email
    ]
    managers += parse_recipients(settings.manager_emails)
    return sorted({email for email in managers if email})


def resolve_level_recipients(db: Session, level: int) -> List[str]:
    if level == 1:
        roles = {"analyst"}
        fallback = parse_recipients(settings.level1_dl)
    else:
        roles = {"senior_analyst"}
        fallback = parse_recipients(settings.level2_dl)
    recipients = [
        user.email
        for user in crud.list_users(db)
        if user.role in roles and user.email
    ]
    recipients += fallback
    return sorted({email for email in recipients if email})


def resolve_user_email(db: Session, user_id: Optional[int]) -> Optional[str]:
    if not user_id:
        return None
    user = crud.get_user_by_id(db, user_id)
    if not user or not user.email:
        return None
    return user.email


def build_alert_url(alert_id: int) -> str:
    return f"{settings.ui_base_url.rstrip('/')}/alerts/{alert_id}"
