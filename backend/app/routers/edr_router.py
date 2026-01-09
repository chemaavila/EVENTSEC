# backend/app/routers/edr_router.py
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from .. import models, search
from ..auth import get_current_user
from ..database import SessionLocal
from ..schemas import UserProfile

router = APIRouter(prefix="/edr", tags=["edr"])


class EdrEvent(BaseModel):
    timestamp: datetime
    hostname: str
    username: str
    event_type: str
    process_name: str
    action: str
    severity: str
    details: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v: Union[str, datetime]) -> datetime:
        """Parse ISO string or datetime to datetime object."""
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v


def _resolve_agent_names(agent_ids: set[int]) -> Dict[int, str]:
    if not agent_ids:
        return {}
    with SessionLocal() as db:
        stmt = select(models.Agent).where(models.Agent.id.in_(agent_ids))
        return {agent.id: agent.name for agent in db.scalars(stmt)}


@router.post("/events", response_model=EdrEvent)
def create_edr_event(
    event: EdrEvent,
    current_user: UserProfile = Depends(get_current_user),
) -> EdrEvent:
    """Legacy no-op (clients should send events via /events)."""
    return event


@router.get("/events", response_model=List[EdrEvent])
def list_edr_events(
    size: int = Query(200, ge=1, le=500),
    current_user: UserProfile = Depends(get_current_user),
) -> List[EdrEvent]:
    docs = search.search_events(size=size, event_type_prefix="edr.")
    category_docs = search.search_events(size=size, category="edr")
    merged: Dict[str, Dict[str, object]] = {}
    for doc in docs + category_docs:
        key = str(doc.get("event_id") or doc.get("timestamp") or id(doc))
        merged[key] = doc

    agent_ids = {
        doc.get("agent_id")
        for doc in merged.values()
        if isinstance(doc.get("agent_id"), int)
    }
    agent_names = _resolve_agent_names(agent_ids)
    events: List[EdrEvent] = []
    for doc in merged.values():
        details = doc.get("details") if isinstance(doc.get("details"), dict) else {}
        agent_name = agent_names.get(doc.get("agent_id")) if doc.get("agent_id") else None
        hostname = details.get("hostname") or agent_name or "unknown"
        events.append(
            EdrEvent(
                timestamp=doc.get("timestamp") or details.get("received_time"),
                hostname=hostname,
                username=details.get("username") or "unknown",
                event_type=doc.get("event_type") or details.get("event_type") or "edr.event",
                process_name=details.get("process_name")
                or details.get("browser")
                or details.get("process")
                or "unknown",
                action=details.get("action") or "event",
                severity=doc.get("severity") or "low",
                details=details if isinstance(details, dict) else {},
            )
        )
    events.sort(key=lambda item: item.timestamp, reverse=True)
    return events


@router.delete("/events", response_model=Dict[str, int])
def clear_edr_events(
    current_user: UserProfile = Depends(get_current_user),
) -> Dict[str, int]:
    """Deletion of historical EDR events is disabled by default."""
    del current_user
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Clearing EDR history is disabled; use Clear view in the UI.",
    )
