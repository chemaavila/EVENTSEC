from __future__ import annotations

import asyncio
import os
import secrets
from typing import Optional

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Query
from sqlalchemy.orm import Session

from .. import crud, models, schemas, search
from ..database import get_db
from ..auth import get_current_user
from ..metrics import EVENT_QUEUE_DROPPED, EVENT_QUEUE_RETRIES, EVENT_QUEUE_SIZE
from .agents_router import get_agent_from_header

router = APIRouter(prefix="/events", tags=["events"])
logger = logging.getLogger("eventsec")

MAX_QUEUE_RETRIES = 3
QUEUE_RETRY_DELAY_SECONDS = 0.1


async def get_event_queue(request) -> asyncio.Queue:
    return request.app.state.event_queue


def is_shared_agent_token(token: Optional[str]) -> bool:
    if not token:
        return False
    shared = os.getenv("EVENTSEC_AGENT_TOKEN")
    if not shared:
        return False
    return secrets.compare_digest(token, shared)


def get_event_agent(
    db: Session = Depends(get_db),
    agent_key: Optional[str] = Header(None, alias="X-Agent-Key"),
    agent_token: Optional[str] = Header(None, alias="X-Agent-Token"),
) -> Optional[models.Agent]:
    if agent_key:
        agent = crud.get_agent_by_api_key(db, agent_key)
        if agent:
            return agent
    if is_shared_agent_token(agent_token):
        return None
    raise HTTPException(status_code=401, detail="Invalid agent credentials")


@router.post("", response_model=schemas.SecurityEvent)
async def ingest_event(
    payload: schemas.SecurityEventCreate,
    request: Request,
    db: Session = Depends(get_db),
    agent: models.Agent | None = Depends(get_agent_from_header),
) -> schemas.SecurityEvent:
    event = models.Event(
        agent_id=agent.id if agent else None,
        event_type=payload.event_type,
        severity=payload.severity,
        category=payload.category,
        details=payload.details,
    )
    event = crud.create_event(db, event)

    queue: asyncio.Queue = await get_event_queue(request)
    for attempt in range(1, MAX_QUEUE_RETRIES + 1):
        try:
            queue.put_nowait(event.id)
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
