# backend/app/routers/edr_router.py
from collections import defaultdict

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Any, Dict, List, Union

from ..auth import get_current_user
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


_EDR_EVENTS: Dict[int, List[EdrEvent]] = defaultdict(list)


@router.post("/events", response_model=EdrEvent)
def create_edr_event(
    event: EdrEvent,
    current_user: UserProfile = Depends(get_current_user),
) -> EdrEvent:
    _EDR_EVENTS[current_user.id].append(event)
    return event


@router.get("/events", response_model=List[EdrEvent])
def list_edr_events(
    current_user: UserProfile = Depends(get_current_user),
) -> List[EdrEvent]:
    return list(reversed(_EDR_EVENTS.get(current_user.id, [])))


@router.delete("/events", response_model=Dict[str, int])
def clear_edr_events(
    current_user: UserProfile = Depends(get_current_user),
) -> Dict[str, int]:
    """Remove all EDR events from the in-memory store."""
    deleted = len(_EDR_EVENTS.get(current_user.id, []))
    _EDR_EVENTS[current_user.id] = []
    return {"deleted": deleted}
