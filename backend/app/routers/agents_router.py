from __future__ import annotations

import secrets
from datetime import datetime

import os

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..config import settings
from ..database import get_db
from ..auth import get_current_admin_user

router = APIRouter(prefix="/agents", tags=["agents"])


def generate_api_key() -> str:
    return secrets.token_hex(24)


@router.post("/enroll", response_model=schemas.AgentEnrollResponse)
def enroll_agent(payload: schemas.AgentEnrollRequest, db: Session = Depends(get_db)) -> schemas.AgentEnrollResponse:
    if payload.enrollment_key != settings.agent_enrollment_key:
        raise HTTPException(status_code=401, detail="Invalid enrollment key")

    existing = crud.get_agent_by_name(db, payload.name)
    if existing:
        raise HTTPException(status_code=400, detail="Agent name already registered")

    api_key = generate_api_key()
    agent = models.Agent(
        name=payload.name,
        os=payload.os,
        ip_address=payload.ip_address,
        version=payload.version,
        status="enrolled",
        api_key=api_key,
        last_seen=datetime.utcnow(),
        last_ip=payload.ip_address,
    )
    crud.create_agent(db, agent)
    return schemas.AgentEnrollResponse(agent_id=agent.id, api_key=api_key)


def get_agent_shared_token() -> str:
    return os.getenv("EVENTSEC_AGENT_TOKEN", "eventsec-agent-token")


def is_agent_request(agent_token: str | None) -> bool:
    shared = get_agent_shared_token()
    return bool(agent_token and secrets.compare_digest(agent_token, shared))


def get_agent_from_header(
    db: Session = Depends(get_db),
    agent_id: int | None = None,
    x_agent_key: str | None = Header(None, alias="X-Agent-Key"),
    x_agent_token: str | None = Header(None, alias="X-Agent-Token"),
) -> models.Agent | None:
    if x_agent_key:
        agent = crud.get_agent_by_api_key(db, x_agent_key)
        if not agent:
            raise HTTPException(status_code=401, detail="Invalid agent credentials")
        if agent_id and agent.id != agent_id:
            raise HTTPException(status_code=403, detail="Agent mismatch")
        return agent

    if x_agent_token and is_agent_request(x_agent_token):
        if agent_id is not None:
            raise HTTPException(
                status_code=401,
                detail="X-Agent-Key required for agent-specific endpoints",
            )
        return None

    raise HTTPException(status_code=401, detail="Missing or invalid agent credentials")


@router.post("/{agent_id}/heartbeat")
def agent_heartbeat(
    agent_id: int,
    payload: schemas.AgentHeartbeat,
    db: Session = Depends(get_db),
    agent: models.Agent = Depends(get_agent_from_header),
) -> dict:
    if agent.id != agent_id:
        raise HTTPException(status_code=403, detail="Agent mismatch")

    agent.status = payload.status or "online"
    agent.last_heartbeat = payload.last_seen
    agent.last_seen = payload.last_seen
    agent.version = payload.version or agent.version
    if payload.ip_address:
        agent.ip_address = payload.ip_address
        agent.last_ip = payload.ip_address
    crud.update_agent(db, agent)
    return {"detail": "Heartbeat acknowledged"}


@router.get("", response_model=list[schemas.Agent])
def list_agents(
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_admin_user),
) -> list[schemas.Agent]:
    return [schemas.Agent.model_validate(agent) for agent in crud.list_agents(db)]


@router.get("/{agent_id}", response_model=schemas.Agent)
def get_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_admin_user),
) -> schemas.Agent:
    agent = crud.get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return schemas.Agent.model_validate(agent)
