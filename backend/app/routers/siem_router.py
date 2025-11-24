# backend/app/routers/siem_router.py
from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Any, Dict, List, Union

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
_SIEM_EVENTS: List[SiemEvent] = []


@router.post("/events", response_model=SiemEvent)
def create_siem_event(event: SiemEvent) -> SiemEvent:
    _SIEM_EVENTS.append(event)
    return event


@router.get("/events", response_model=List[SiemEvent])
def list_siem_events() -> List[SiemEvent]:
    # Devuelve los más recientes primero
    return list(reversed(_SIEM_EVENTS))
