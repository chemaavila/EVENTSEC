from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .. import crud, models
from ..auth import get_current_user
from ..config import settings
from ..database import get_db
from ..integrations import SoftwareApiClient
from ..schemas import UserProfile

router = APIRouter(prefix="/xdr", tags=["xdr"])


class XdrActionRequest(BaseModel):
    agent_id: str = Field(..., description="Software agent ID")
    command: str = Field(..., description="Active response command")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    alert_id: Optional[str] = None


class XdrActionResponse(BaseModel):
    action_id: int
    status: str
    software_response: Dict[str, Any]


@router.post("/actions", response_model=XdrActionResponse)
def trigger_xdr_action(
    payload: XdrActionRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> XdrActionResponse:
    if payload.agent_id in {"all", "*"}:
        raise HTTPException(status_code=400, detail="Active response requires a specific agent_id")
    if not settings.software_api_url:
        raise HTTPException(status_code=503, detail="Software API not configured")

    action = models.EndpointAction(
        endpoint_id=None,
        action_type=payload.command,
        parameters={
            "agent_id": payload.agent_id,
            "alert_id": payload.alert_id,
            **payload.parameters,
        },
        status="pending",
        requested_by=current_user.id,
        requested_at=datetime.now(timezone.utc),
    )
    action = crud.create_endpoint_action(db, action)

    try:
        client = SoftwareApiClient()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    try:
        response = client.active_response_command(
            {
                "command": payload.command,
                "custom": True,
                "arguments": payload.parameters,
                "agents": [payload.agent_id],
            }
        )
        action.status = "completed"
        action.completed_at = datetime.now(timezone.utc)
        action.output = str(response)
        action = crud.update_endpoint_action(db, action)
    except Exception as exc:  # noqa: BLE001
        action.status = "failed"
        action.completed_at = datetime.now(timezone.utc)
        action.output = str(exc)
        crud.update_endpoint_action(db, action)
        raise HTTPException(status_code=502, detail="Software Active Response failed") from exc

    crud.create_action_log(
        db,
        models.ActionLog(
            user_id=current_user.id,
            action_type="software_active_response",
            target_type="agent",
            target_id=int(payload.agent_id) if payload.agent_id.isdigit() else 0,
            parameters={
                "command": payload.command,
                "agent_id": payload.agent_id,
                "alert_id": payload.alert_id,
                "response": response,
            },
        ),
    )

    return XdrActionResponse(action_id=action.id, status=action.status, software_response=response)
