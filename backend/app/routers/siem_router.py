# backend/app/routers/siem_router.py
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from .. import search
from ..auth import get_current_user
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


def _event_time_range(
    last_ms: Optional[int],
    start_time: Optional[str],
    end_time: Optional[str],
) -> tuple[Optional[str], Optional[str]]:
    if last_ms and not start_time:
        start_dt = datetime.now(timezone.utc) - timedelta(milliseconds=last_ms)
        return start_dt.isoformat(), end_time
    return start_time, end_time


def _map_siem_event(doc: Dict[str, Any]) -> SiemEvent:
    details = doc.get("details") or {}
    if not isinstance(details, dict):
        details = {"raw": details}
    host = (
        details.get("hostname")
        or details.get("host")
        or details.get("computer")
        or "unknown"
    )
    source = doc.get("source") or details.get("source") or doc.get("event_type") or "event"
    category = doc.get("category") or details.get("category") or "uncategorized"
    message = doc.get("message") or details.get("message") or str(details)
    timestamp = doc.get("timestamp") or details.get("timestamp") or datetime.now(timezone.utc)
    return SiemEvent(
        timestamp=timestamp,
        host=host,
        source=str(source),
        category=str(category),
        severity=str(doc.get("severity") or "low"),
        message=str(message),
        raw=details,
    )


@router.get("/events", response_model=List[SiemEvent])
def list_siem_events(
    query: str = Query("", description="Query string for OpenSearch"),
    severity: Optional[str] = Query(None),
    last_ms: Optional[int] = Query(None, ge=1, le=7 * 24 * 60 * 60 * 1000),
    start_time: Optional[str] = Query(None, description="ISO start time"),
    end_time: Optional[str] = Query(None, description="ISO end time"),
    size: int = Query(200, ge=1, le=500),
    current_user: UserProfile = Depends(get_current_user),
) -> List[SiemEvent]:
    del current_user
    start_time, end_time = _event_time_range(last_ms, start_time, end_time)
    try:
        docs = search.search_events(
            query=query,
            severity=severity,
            size=size,
            start_time=start_time,
            end_time=end_time,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return [_map_siem_event(doc) for doc in docs]


@router.delete("/events", response_model=Dict[str, int])
def clear_siem_events(
    current_user: UserProfile = Depends(get_current_user),
) -> Dict[str, int]:
    del current_user
    deleted = search.delete_events_by_query({"match_all": {}})
    return {"deleted": deleted}
