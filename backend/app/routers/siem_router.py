# backend/app/routers/siem_router.py
import asyncio
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncIterable, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from .. import models, search
from ..auth import get_current_user
from ..database import SessionLocal
from ..integrations import SoftwareIndexerClient, software_indexer_enabled
from ..schemas import UserProfile

logger = logging.getLogger("eventsec.siem_stream")

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
    if software_indexer_enabled():
        client = SoftwareIndexerClient()
        result = client.search_alerts(
            query=q,
            size=size,
            start=start,
            end=end,
            severity=severity,
        )
        docs = [event for event in result.events]
    else:
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
        if "raw" in doc and "details" not in doc:
            raw_details = doc.get("raw", {}).get("data", {})
            details = raw_details if isinstance(raw_details, dict) else {}
        else:
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
                host=doc.get("host") or host,
                source=doc.get("source")
                or details.get("source")
                or doc.get("event_type", "event"),
                category=doc.get("category") or details.get("category") or "event",
                severity=doc.get("severity") or "low",
                message=doc.get("message") or message,
                raw=doc.get("raw") if isinstance(doc.get("raw"), dict) else raw,
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


@router.get("/stream")
async def stream_siem_events(
    q: str = Query("", description="KQL/Lucene search query"),
    severity: Optional[str] = Query(None),
    poll_seconds: float = Query(2.0, ge=0.5, le=30.0),
    heartbeat_seconds: float = Query(20.0, ge=5.0, le=60.0),
    current_user: UserProfile = Depends(get_current_user),
) -> StreamingResponse:
    del current_user
    if not software_indexer_enabled():
        raise HTTPException(status_code=503, detail="Software indexer not configured")

    client = SoftwareIndexerClient()

    async def event_generator() -> AsyncIterable[str]:
        search_after: Optional[List[Any]] = None
        last_emit = time.monotonic()
        backoff = 1.0
        while True:
            try:
                result = client.search_alerts(
                    query=q,
                    size=200,
                    severity=severity,
                    search_after=search_after,
                )
                for event in result.events:
                    payload = json.dumps(event, default=str)
                    yield f"data: {payload}\n\n"
                    last_emit = time.monotonic()
                search_after = result.last_sort or search_after
                backoff = 1.0
            except Exception as exc:  # noqa: BLE001
                logger.warning("SSE stream query failed: %s", exc)
                await asyncio.sleep(min(backoff, 10.0))
                backoff *= 2
                continue

            if time.monotonic() - last_emit >= heartbeat_seconds:
                yield "event: ping\ndata: {}\n\n"
                last_emit = time.monotonic()

            await asyncio.sleep(poll_seconds)

    response = StreamingResponse(event_generator(), media_type="text/event-stream")
    response.headers["Cache-Control"] = "no-cache, no-transform"
    response.headers["Connection"] = "keep-alive"
    response.headers["X-Accel-Buffering"] = "no"
    return response
