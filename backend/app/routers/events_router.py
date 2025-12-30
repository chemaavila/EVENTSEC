from __future__ import annotations

import asyncio
import os
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Query, Header
from sqlalchemy.orm import Session

from .. import crud, models, schemas, search
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/events", tags=["events"])


async def get_event_queue(request) -> asyncio.Queue:
    return request.app.state.event_queue


def is_shared_agent_token(token: Optional[str]) -> bool:
    if not token:
        return False
    shared = os.getenv("EVENTSEC_AGENT_TOKEN", "eventsec-agent-token")
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
    agent: Optional[models.Agent] = Depends(get_event_agent),
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
    await queue.put(event.id)

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
