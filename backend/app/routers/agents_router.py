from __future__ import annotations

import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..config import settings
from ..integrations import SoftwareApiClient
from ..database import get_db
from ..auth import get_current_user, require_agent_key
from ..services.endpoints import ensure_endpoint_registered

router = APIRouter(prefix="/agents", tags=["agents"])


def generate_api_key() -> str:
    return secrets.token_hex(24)


@router.post("/enroll", response_model=schemas.AgentEnrollResponse)
def enroll_agent(
    payload: schemas.AgentEnrollRequest, db: Session = Depends(get_db)
) -> schemas.AgentEnrollResponse:
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
    ensure_endpoint_registered(db, payload.name, agent)
    return schemas.AgentEnrollResponse(agent_id=agent.id, api_key=api_key)


@router.post("/{agent_id}/heartbeat")
def agent_heartbeat(
    agent_id: int,
    payload: schemas.AgentHeartbeat,
    db: Session = Depends(get_db),
    agent: models.Agent = Depends(require_agent_key),
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
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> list[schemas.Agent]:
    del current_user
    if settings.software_api_url:
        try:
            client = SoftwareApiClient()
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        try:
            response = client.get_agents()
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail="Software API unavailable") from exc
        items = response.get("data", {}).get("affected_items") or response.get("data") or []
        mapped: list[schemas.Agent] = []
        for item in items:
            agent_id = item.get("id")
            if isinstance(agent_id, str) and agent_id.isdigit():
                agent_id = int(agent_id)
            if not isinstance(agent_id, int):
                agent_id = abs(hash(str(agent_id))) % 1_000_000_000
            mapped.append(
                schemas.Agent(
                    id=int(agent_id),
                    name=item.get("name") or item.get("node_name") or "unknown",
                    os=(item.get("os") or {}).get("name") if isinstance(item.get("os"), dict) else item.get("os", "unknown"),
                    ip_address=item.get("ip") or item.get("register_ip") or "unknown",
                    version=item.get("version"),
                    tags=item.get("groups") or [],
                    status=item.get("status") or "unknown",
                    last_heartbeat=item.get("last_keepalive"),
                    last_seen=item.get("last_keepalive"),
                    last_ip=item.get("last_ip"),
                )
            )
        return mapped
    return [schemas.Agent.model_validate(agent) for agent in crud.list_agents(db)]


@router.get("/{agent_id}", response_model=schemas.Agent)
def get_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> schemas.Agent:
    del current_user
    agent = crud.get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return schemas.Agent.model_validate(agent)
