from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

from .. import crud, models, schemas, search
from ..database import get_db
from ..auth import get_current_user
from .agents_router import get_agent_from_header

router = APIRouter(prefix="/events", tags=["events"])


async def get_event_queue(request) -> asyncio.Queue:
    return request.app.state.event_queue


@router.post("", response_model=schemas.SecurityEvent)
async def ingest_event(
    payload: schemas.SecurityEventCreate,
    request: Request,
    db: Session = Depends(get_db),
    agent: models.Agent = Depends(get_agent_from_header),
) -> schemas.SecurityEvent:
    event = models.Event(
        agent_id=agent.id,
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

