# backend/app/routers/siem_router.py
from collections import defaultdict

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Any, Dict, List, Union

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


# En memoria (para demo). En producción → BD.
_SIEM_EVENTS: Dict[int, List[SiemEvent]] = defaultdict(list)


@router.post("/events", response_model=SiemEvent)
def create_siem_event(
    event: SiemEvent,
    current_user: UserProfile = Depends(get_current_user),
) -> SiemEvent:
    _SIEM_EVENTS[current_user.id].append(event)
    return event


@router.get("/events", response_model=List[SiemEvent])
def list_siem_events(
    current_user: UserProfile = Depends(get_current_user),
) -> List[SiemEvent]:
    # Devuelve los más recientes primero
    return list(reversed(_SIEM_EVENTS.get(current_user.id, [])))


@router.delete("/events", response_model=Dict[str, int])
def clear_siem_events(
    current_user: UserProfile = Depends(get_current_user),
) -> Dict[str, int]:
    """Remove all SIEM events from the in-memory store."""
    deleted = len(_SIEM_EVENTS.get(current_user.id, []))
    _SIEM_EVENTS[current_user.id] = []
    return {"deleted": deleted}
