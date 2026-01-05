from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..auth import get_current_user
from ..database import get_db

router = APIRouter(prefix="/actions", tags=["actions"])


@router.get("", response_model=list[schemas.ResponseAction])
def list_actions(
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> list[schemas.ResponseAction]:
    del current_user
    actions = crud.list_response_actions(db)
    return [schemas.ResponseAction.model_validate(action) for action in actions]


@router.post("", response_model=schemas.ResponseAction, status_code=201)
def create_action(
    payload: schemas.ResponseActionCreate,
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> schemas.ResponseAction:
    action = models.ResponseAction(
        tenant_id=None,
        action_type=payload.action_type,
        target=payload.target,
        ttl_minutes=payload.ttl_minutes,
        status=payload.status or "requested",
        requested_by=current_user.id,
        details=payload.details or {},
    )
    action = crud.create_response_action(db, action)
    return schemas.ResponseAction.model_validate(action)


@router.patch("/{action_id}", response_model=schemas.ResponseAction)
def update_action(
    action_id: int,
    payload: schemas.ResponseActionUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> schemas.ResponseAction:
    del current_user
    action = crud.get_response_action(db, action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    if payload.status is not None:
        action.status = payload.status
    if payload.details is not None:
        action.details = payload.details
    action = crud.update_response_action(db, action)
    return schemas.ResponseAction.model_validate(action)
