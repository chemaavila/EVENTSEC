# backend/app/routers/siem_router.py
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from .. import models, search
from ..auth import get_current_user
from ..database import SessionLocal
from ..schemas import UserProfile

router = APIRouter(prefix="/siem", tags=["siem"])


class SiemEvent(BaseModel):
    timestamp: datetime
    host: str
    source: str
    category: str
    severity: str
    message: str
    raw: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v: Union[str, datetime]) -> datetime:
        """Parse ISO string or datetime to datetime object."""
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v


def _parse_time_range(
    time_range: Optional[str], since_ms: Optional[int]
) -> tuple[Optional[datetime], Optional[datetime]]:
    if not time_range and since_ms is None:
        return None, None
    end = datetime.now(timezone.utc)
    if since_ms is not None:
        return end - timedelta(milliseconds=since_ms), end
    if not time_range:
        return None, end
    units = {"m": 60, "h": 3600, "d": 86400}
    unit = time_range[-1]
    value = time_range[:-1]
    if unit not in units or not value.isdigit():
        return None, end
    return end - timedelta(seconds=int(value) * units[unit]), end


def _resolve_agent_names(agent_ids: set[int]) -> Dict[int, str]:
    if not agent_ids:
        return {}
    with SessionLocal() as db:
        stmt = select(models.Agent).where(models.Agent.id.in_(agent_ids))
        return {agent.id: agent.name for agent in db.scalars(stmt)}


@router.post("/events", response_model=SiemEvent)
def create_siem_event(
    event: SiemEvent,
    current_user: UserProfile = Depends(get_current_user),
) -> SiemEvent:
    """Legacy no-op (clients should send events via /events)."""
    return event


@router.get("/events", response_model=List[SiemEvent])
def list_siem_events(
    q: str = Query("", description="KQL/Lucene search query"),
    severity: Optional[str] = Query(None),
    size: int = Query(200, ge=1, le=500),
    time_range: Optional[str] = Query(None, description="Range like 15m, 1h, 24h"),
    since_ms: Optional[int] = Query(None, ge=1),
    current_user: UserProfile = Depends(get_current_user),
) -> List[SiemEvent]:
    start, end = _parse_time_range(time_range, since_ms)
    docs = search.search_events(
        query=q,
        size=size,
        start=start,
        end=end,
        severity=severity,
    )
    agent_ids = {
        doc.get("agent_id")
        for doc in docs
        if isinstance(doc.get("agent_id"), int)
    }
    agent_names = _resolve_agent_names(agent_ids)
    events: List[SiemEvent] = []
    for doc in docs:
        details = doc.get("details") if isinstance(doc.get("details"), dict) else {}
        agent_name = agent_names.get(doc.get("agent_id")) if doc.get("agent_id") else None
        host = details.get("hostname") or agent_name or "unknown"
        message = (
            doc.get("message")
            or details.get("message")
            or f"{doc.get('event_type', 'event')} detected"
        )
        raw = {
            "event_id": doc.get("event_id"),
            "agent_id": doc.get("agent_id"),
            "event_type": doc.get("event_type"),
            "severity": doc.get("severity"),
            "category": doc.get("category"),
            "timestamp": doc.get("timestamp"),
            "details": details,
        }
        events.append(
            SiemEvent(
                timestamp=doc.get("timestamp") or details.get("received_time"),
                host=host,
                source=doc.get("source") or details.get("source") or doc.get("event_type", "event"),
                category=doc.get("category") or details.get("category") or "event",
                severity=doc.get("severity") or "low",
                message=message,
                raw=raw,
            )
        )
    return events


@router.delete("/events", response_model=Dict[str, int])
def clear_siem_events(
    current_user: UserProfile = Depends(get_current_user),
) -> Dict[str, int]:
    """Deletion of historical SIEM events is disabled by default."""
    del current_user
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Clearing SIEM history is disabled; use Clear view in the UI.",
    )
