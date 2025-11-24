# backend/app/routers/edr_router.py
from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Any, Dict, List, Union

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


_EDR_EVENTS: List[EdrEvent] = []


@router.post("/events", response_model=EdrEvent)
def create_edr_event(event: EdrEvent) -> EdrEvent:
    _EDR_EVENTS.append(event)
    return event


@router.get("/events", response_model=List[EdrEvent])
def list_edr_events() -> List[EdrEvent]:
    return list(reversed(_EDR_EVENTS))
