from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..auth import get_current_user
from ..database import get_db
from .agents_router import get_agent_from_header

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/{agent_id}", response_model=List[schemas.InventorySnapshot])
def ingest_inventory_snapshots(
    agent_id: int,
    payload: schemas.InventoryIngestRequest,
    db: Session = Depends(get_db),
    agent: models.Agent = Depends(get_agent_from_header),
) -> List[schemas.InventorySnapshot]:
    if agent.id != agent_id:
        raise HTTPException(status_code=403, detail="Agent ID mismatch")
    if not payload.snapshots:
        return []

    created: List[schemas.InventorySnapshot] = []
    for item in payload.snapshots:
        snapshot = models.InventorySnapshot(
            agent_id=agent_id, category=item.category, data=item.data
        )
        record = crud.create_inventory_snapshot(db, snapshot)
        created.append(schemas.InventorySnapshot.model_validate(record))
    return created


@router.get("/{agent_id}", response_model=schemas.InventoryOverview)
def get_inventory_overview(
    agent_id: int,
    category: Optional[str] = Query(None, description="Filter by inventory category"),
    limit: Optional[int] = Query(
        100, ge=1, le=1000, description="Max snapshots per category"
    ),
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> schemas.InventoryOverview:
    # Ensure agent exists
    agent = crud.get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    snapshots = crud.list_inventory_snapshots(
        db, agent_id=agent_id, category=category, limit=limit
    )
    grouped: Dict[str, List[schemas.InventorySnapshot]] = defaultdict(list)
    for snap in snapshots:
        grouped[snap.category].append(schemas.InventorySnapshot.model_validate(snap))
    return schemas.InventoryOverview(agent_id=agent_id, categories=dict(grouped))
