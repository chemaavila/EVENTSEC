from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..auth import get_current_user
from ..database import get_db
from .agents_router import get_agent_from_header

router = APIRouter(prefix="/sca", tags=["sca"])


@router.post("/{agent_id}/results", response_model=schemas.SCAResult)
def ingest_sca_result(
    agent_id: int,
    payload: schemas.SCAResultCreate,
    db: Session = Depends(get_db),
    agent: models.Agent = Depends(get_agent_from_header),
) -> schemas.SCAResult:
    if agent.id != agent_id:
        raise HTTPException(status_code=403, detail="Agent ID mismatch")
    result = models.SCAResult(
        agent_id=agent_id,
        policy_id=payload.policy_id,
        policy_name=payload.policy_name,
        score=payload.score,
        status=payload.status,
        passed_checks=payload.passed_checks,
        failed_checks=payload.failed_checks,
        details=payload.details,
    )
    created = crud.create_sca_result(db, result)
    return schemas.SCAResult.model_validate(created)


@router.get("/{agent_id}/results", response_model=List[schemas.SCAResult])
def list_sca_results(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> List[schemas.SCAResult]:
    if not crud.get_agent_by_id(db, agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    results = crud.list_sca_results(db, agent_id)
    return [schemas.SCAResult.model_validate(item) for item in results]
