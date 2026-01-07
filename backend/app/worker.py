from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from . import crud, models
from .config import settings
from .database import SessionLocal, engine, get_missing_tables
from .jobs.vuln_matcher import match_and_score
from .jobs.vuln_notifications import create_alerts_for_critical, notify_admins
from .notifications import NotificationService

logger = logging.getLogger("eventsec.worker")


async def _run_match_and_notify() -> None:
    if not settings.vuln_intel_enabled:
        return
    notification_service = NotificationService()
    with SessionLocal() as db:
        since = datetime.now(timezone.utc) - timedelta(minutes=15)
        components = (
            db.query(models.SoftwareComponent)
            .filter(models.SoftwareComponent.last_seen_at >= since)
            .all()
        )
        findings = await match_and_score(db, components)
        create_alerts_for_critical(db, findings)
        notify_admins(db, findings, notification_service)


async def _run_digest() -> None:
    if not settings.vuln_intel_enabled or not settings.vuln_intel_notify_digest_enabled:
        return
    tz = ZoneInfo(settings.vuln_intel_timezone)
    now_local = datetime.now(tz)
    if now_local.hour != settings.vuln_intel_notify_digest_hour_local:
        return
    with SessionLocal() as db:
        notification_service = NotificationService()
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        findings = (
            db.query(models.AssetVulnerability)
            .filter(
                models.AssetVulnerability.last_seen_at >= since,
                models.AssetVulnerability.risk_label.in_(["HIGH", "MEDIUM"]),
            )
            .all()
        )
        notify_admins(db, findings, notification_service)


async def loop_worker() -> None:
    last_digest_date: str | None = None
    while True:
        await _run_match_and_notify()
        tz = ZoneInfo(settings.vuln_intel_timezone)
        now_local = datetime.now(tz)
        digest_key = now_local.strftime("%Y-%m-%d")
        if digest_key != last_digest_date:
            await _run_digest()
            if now_local.hour == settings.vuln_intel_notify_digest_hour_local:
                last_digest_date = digest_key
        await asyncio.sleep(300)


def wait_for_required_tables() -> bool:
    attempts = settings.db_ready_wait_attempts
    interval = settings.db_ready_wait_interval_seconds
    for attempt in range(1, attempts + 1):
        try:
            with engine.connect() as conn:
                missing = get_missing_tables(conn)
        except Exception as exc:  # noqa: BLE001
            logger.warning("DB readiness check failed: %s", exc)
            missing = ["db_unreachable"]
        if not missing:
            logger.info("Database schema ready for worker.")
            return True
        logger.warning(
            "Database not migrated yet; missing tables: %s (attempt %s/%s)",
            ", ".join(missing),
            attempt,
            attempts,
        )
        time.sleep(interval)
    logger.error(
        "Database schema still missing required tables. "
        "Run alembic upgrade head before starting the worker."
    )
    return False


def main() -> None:
    if settings.vuln_intel_worker_role != "worker":
        return
    if not wait_for_required_tables():
        return
    asyncio.run(loop_worker())


if __name__ == "__main__":
    main()
