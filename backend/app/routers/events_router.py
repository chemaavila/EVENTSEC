from __future__ import annotations

import asyncio
import os
import uuid
from typing import Optional

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from .. import crud, models, schemas, search
from ..database import get_db
from ..auth import get_current_user, require_agent_auth
from ..services.endpoints import ensure_endpoint_registered
from ..metrics import (
    EVENTS_RECEIVED_TOTAL,
    EVENT_QUEUE_DROPPED,
    EVENT_QUEUE_RETRIES,
    EVENT_QUEUE_SIZE,
    PARSE_FAIL_TOTAL,
    PARSE_SUCCESS_TOTAL,
)

router = APIRouter(prefix="/events", tags=["events"])
logger = logging.getLogger("eventsec")

MAX_QUEUE_RETRIES = 3
QUEUE_RETRY_DELAY_SECONDS = 0.1


async def get_event_queue(request) -> asyncio.Queue:
    return request.app.state.event_queue


@router.post("", response_model=schemas.SecurityEvent)
async def ingest_event(
    payload: schemas.SecurityEventCreate,
    request: Request,
    db: Session = Depends(get_db),
    agent: models.Agent | None = Depends(require_agent_auth),
) -> schemas.SecurityEvent:
    details = payload.details or {}
    parse_error = None
    if not isinstance(details, dict):
        parse_error = "details_not_object"
        details = {"raw": details}
    correlation_id = details.get("correlation_id") or str(uuid.uuid4())
    details["correlation_id"] = correlation_id
    source_label = details.get("source") or payload.category or payload.event_type
    EVENTS_RECEIVED_TOTAL.labels(source=source_label).inc()
    if parse_error:
        PARSE_FAIL_TOTAL.labels(source=source_label, error_code=parse_error).inc()
    else:
        PARSE_SUCCESS_TOTAL.labels(source=source_label).inc()

    raw_id = str(uuid.uuid4())
    received_time = models.utcnow().isoformat()
    details["raw_ref"] = raw_id
    details["received_time"] = received_time
    raw_doc = {
        "raw_id": raw_id,
        "received_time": received_time,
        "source": source_label,
        "correlation_id": correlation_id,
        "collector_id": str(agent.id) if agent else None,
        "tenant_id": None,
        "raw_payload": payload.model_dump(),
        "transport_meta": {
            "client_host": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        },
        "parse_status": "failed" if parse_error else "ok",
    }
    hostname = details.get("hostname") or (agent.name if agent else None)
    if hostname:
        ensure_endpoint_registered(db, hostname, agent)
    if os.getenv("PYTEST_CURRENT_TEST") is None:
        try:
            search.index_raw_event(raw_doc)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to index raw event %s: %s", raw_id, exc)
    if parse_error:
        dlq_doc = {
            "dlq_id": str(uuid.uuid4()),
            "time": models.utcnow().isoformat(),
            "source": source_label,
            "raw_ref": raw_id,
            "error_stage": "ingest",
            "error_code": parse_error,
            "error_detail": "Event details must be an object",
            "replay_count": 0,
            "last_replay_time": None,
        }
        try:
            search.index_dlq_event(dlq_doc)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to index DLQ event %s: %s", raw_id, exc)

    event = models.Event(
        agent_id=agent.id if agent else None,
        event_type=payload.event_type,
        severity=payload.severity,
        category=payload.category,
        details=details,
    )
    event = crud.create_event(db, event)

    queue: asyncio.Queue = await get_event_queue(request)
    for attempt in range(1, MAX_QUEUE_RETRIES + 1):
        try:
            if hasattr(queue, "put_nowait"):
                queue.put_nowait(event.id)
            else:
                await queue.put(event.id)
            if hasattr(queue, "qsize"):
                EVENT_QUEUE_SIZE.set(queue.qsize())
            break
        except asyncio.QueueFull:
            EVENT_QUEUE_RETRIES.inc()
            logger.warning(
                "Event queue full (size=%s). Retry %s/%s for event %s.",
                queue.qsize(),
                attempt,
                MAX_QUEUE_RETRIES,
                event.id,
            )
            await asyncio.sleep(QUEUE_RETRY_DELAY_SECONDS)
    else:
        EVENT_QUEUE_DROPPED.inc()
        EVENT_QUEUE_SIZE.set(queue.qsize())
        logger.error(
            "Dropping event %s after queue reached maxsize (%s).",
            event.id,
            queue.maxsize,
        )

    return schemas.SecurityEvent.model_validate(event)


@router.get("", response_model=list[schemas.IndexedEvent])
def list_events(
    query: str = Query("", description="Lucene query string"),
    severity: str | None = Query(None),
    size: int = Query(100, ge=1, le=500),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> list[dict]:
    try:
        docs = search.search_events(query=query, severity=severity, size=size)
        return [schemas.IndexedEvent(**doc) for doc in docs]
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
