from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..database import get_db
from ..auth import get_current_admin_user

router = APIRouter(prefix="/rules/detections", tags=["rules"])


@router.get("", response_model=list[schemas.DetectionRule])
def list_detection_rules(
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_admin_user),
) -> list[schemas.DetectionRule]:
    rules = crud.list_detection_rules(db)
    return [schemas.DetectionRule.model_validate(r) for r in rules]


@router.post("", response_model=schemas.DetectionRule, status_code=201)
def create_detection_rule(
    payload: schemas.DetectionRuleCreate,
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_admin_user),
) -> schemas.DetectionRule:
    rule = models.DetectionRule(
        name=payload.name,
        description=payload.description,
        severity=payload.severity,
        enabled=payload.enabled,
        conditions=payload.conditions,
    )
    rule = crud.create_detection_rule(db, rule)
    return schemas.DetectionRule.model_validate(rule)

