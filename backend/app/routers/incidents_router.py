from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..auth import get_current_user
from ..database import get_db
from ..notifications import NotificationService, resolve_manager_recipients

router = APIRouter(prefix="/incidents", tags=["incidents"])
notification_service = NotificationService()


def _hydrate_incident(
    db: Session, incident: models.Incident
) -> schemas.Incident:
    items = crud.list_incident_items(db, incident.id)
    return schemas.Incident(
        id=incident.id,
        tenant_id=incident.tenant_id,
        title=incident.title,
        description=incident.description,
        severity=incident.severity,
        status=incident.status,
        assigned_to=incident.assigned_to,
        tags=incident.tags or [],
        created_by=incident.created_by,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        items=[schemas.IncidentItem.model_validate(item) for item in items],
    )


@router.get("", response_model=List[schemas.Incident])
def list_incidents(
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> List[schemas.Incident]:
    del current_user
    incidents = crud.list_incidents(db)
    return [_hydrate_incident(db, incident) for incident in incidents]


@router.get("/{incident_id}", response_model=schemas.Incident)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> schemas.Incident:
    del current_user
    incident = crud.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return _hydrate_incident(db, incident)


@router.post("", response_model=schemas.Incident, status_code=201)
def create_incident(
    payload: schemas.IncidentCreate,
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> schemas.Incident:
    incident = models.Incident(
        tenant_id=None,
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        status=payload.status,
        assigned_to=payload.assigned_to,
        created_by=current_user.id,
        tags=payload.tags or [],
    )
    incident = crud.create_incident(db, incident)

    if payload.items:
        for item in payload.items:
            crud.create_incident_item(
                db,
                models.IncidentItem(
                    incident_id=incident.id,
                    kind=item.kind,
                    ref_id=item.ref_id,
                ),
            )

    recipients = resolve_manager_recipients(db)
    if recipients:
        notification_service.emit(
            db,
            event_type="incident_created",
            entity_type="incident",
            entity_id=incident.id,
            recipients=recipients,
            payload={
                "subject": f"[EventSec] Incident created: {incident.title}",
                "body": f"Incident {incident.id} created with severity {incident.severity}.",
            },
        )
    return _hydrate_incident(db, incident)


@router.patch("/{incident_id}", response_model=schemas.Incident)
def update_incident(
    incident_id: int,
    payload: schemas.IncidentUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> schemas.Incident:
    del current_user
    incident = crud.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(incident, field, value)
    incident.updated_at = datetime.now(timezone.utc)
    incident = crud.update_incident(db, incident)

    recipients = resolve_manager_recipients(db)
    if recipients:
        notification_service.emit(
            db,
            event_type="incident_updated",
            entity_type="incident",
            entity_id=incident.id,
            recipients=recipients,
            payload={
                "subject": f"[EventSec] Incident updated: {incident.title}",
                "body": f"Incident {incident.id} updated. Status: {incident.status}.",
            },
        )
    return _hydrate_incident(db, incident)


@router.post("/{incident_id}/items", response_model=schemas.IncidentItem, status_code=201)
def attach_incident_item(
    incident_id: int,
    payload: schemas.IncidentItemCreate,
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> schemas.IncidentItem:
    del current_user
    incident = crud.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    item = models.IncidentItem(
        incident_id=incident.id,
        kind=payload.kind,
        ref_id=payload.ref_id,
    )
    item = crud.create_incident_item(db, item)
    return schemas.IncidentItem.model_validate(item)


@router.post("/from-alert/{alert_id}", response_model=schemas.Incident, status_code=201)
def create_incident_from_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> schemas.Incident:
    alert = crud.get_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    incident = models.Incident(
        tenant_id=None,
        title=f"Alert {alert.id}: {alert.title}",
        description=alert.description,
        severity=alert.severity,
        status="new",
        assigned_to=alert.assigned_to,
        created_by=current_user.id,
        tags=["alert"],
    )
    incident = crud.create_incident(db, incident)
    crud.create_incident_item(
        db,
        models.IncidentItem(
            incident_id=incident.id,
            kind="alert",
            ref_id=str(alert.id),
        ),
    )
    return _hydrate_incident(db, incident)


@router.post(
    "/from-network-event/{event_id}",
    response_model=schemas.Incident,
    status_code=201,
)
def create_incident_from_network_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> schemas.Incident:
    event = db.get(models.NetworkEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Network event not found")

    title = f"Network event {event.id} ({event.source}/{event.event_type})"
    incident = models.Incident(
        tenant_id=None,
        title=title,
        description=event.signature or "Network IDS event flagged for review.",
        severity="medium",
        status="new",
        created_by=current_user.id,
        tags=["network"],
    )
    incident = crud.create_incident(db, incident)
    crud.create_incident_item(
        db,
        models.IncidentItem(
            incident_id=incident.id,
            kind="event",
            ref_id=str(event.id),
        ),
    )
    return _hydrate_incident(db, incident)
