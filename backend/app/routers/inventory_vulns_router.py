from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from .. import crud, models, schemas
from ..auth import get_current_user
from ..database import get_db

router = APIRouter(prefix="/api", tags=["inventory-vulns"])


def _risk_summary(db: Session, tenant_id: str, asset_id: int) -> schemas.AssetRiskSummary:
    stmt = (
        select(
            models.AssetVulnerability.risk_label,
            func.count(models.AssetVulnerability.id),
        )
        .where(
            models.AssetVulnerability.tenant_id == tenant_id,
            models.AssetVulnerability.asset_id == asset_id,
        )
        .group_by(models.AssetVulnerability.risk_label)
    )
    counts = {label: count for label, count in db.execute(stmt).all()}
    ordered = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    top_label = next((label for label in ordered if counts.get(label)), None)
    last_scan = db.execute(
        select(func.max(models.AssetVulnerability.last_seen_at)).where(
            models.AssetVulnerability.tenant_id == tenant_id,
            models.AssetVulnerability.asset_id == asset_id,
        )
    ).scalar_one_or_none()
    return schemas.AssetRiskSummary(
        asset_id=asset_id,
        critical_count=counts.get("CRITICAL", 0),
        high_count=counts.get("HIGH", 0),
        medium_count=counts.get("MEDIUM", 0),
        low_count=counts.get("LOW", 0),
        top_risk_label=top_label,
        last_scan_at=last_scan,
    )


def _risk_labels_from_min(min_risk: Optional[str]) -> Optional[List[str]]:
    if not min_risk:
        return None
    order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    min_risk = min_risk.upper()
    if min_risk not in order:
        return None
    return [label for label in order if order.index(label) >= order.index(min_risk)]


@router.post(
    "/inventory/assets/{asset_id}/software",
    response_model=schemas.InventoryIngestResponse,
)
def ingest_software_components(
    asset_id: int,
    payload: schemas.SoftwareInventoryIngestRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> schemas.InventoryIngestResponse:
    asset = crud.get_agent_by_id(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    tenant_id = current_user.tenant_id or "default"
    inserted = 0
    updated = 0
    collected_at = payload.collected_at or datetime.now(timezone.utc)
    for item in payload.items:
        existing = crud.get_software_component(
            db, tenant_id, asset_id, item.name, item.version, item.vendor
        )
        if existing:
            existing.last_seen_at = datetime.now(timezone.utc)
            existing.collected_at = collected_at
            existing.purl = item.purl or existing.purl
            existing.cpe = item.cpe or existing.cpe
            existing.raw = item.raw or existing.raw
            existing.source = item.source or existing.source
            crud.create_or_update_software_component(db, existing)
            updated += 1
            continue
        component = models.SoftwareComponent(
            tenant_id=tenant_id,
            asset_id=asset_id,
            name=item.name,
            version=item.version,
            vendor=item.vendor,
            source=item.source,
            purl=item.purl,
            cpe=item.cpe,
            raw=item.raw,
            collected_at=collected_at,
            last_seen_at=datetime.now(timezone.utc),
        )
        crud.create_or_update_software_component(db, component)
        inserted += 1
    risk = _risk_summary(db, tenant_id, asset_id)
    return schemas.InventoryIngestResponse(
        inserted=inserted, updated=updated, asset_risk=risk
    )


@router.get(
    "/inventory/assets", response_model=List[schemas.AssetInventorySummary]
)
def list_assets_with_risk(
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> List[schemas.AssetInventorySummary]:
    tenant_id = current_user.tenant_id or "default"
    asset_ids = [
        row[0]
        for row in db.execute(
            select(models.SoftwareComponent.asset_id)
            .where(models.SoftwareComponent.tenant_id == tenant_id)
            .distinct()
        ).all()
    ]
    assets = [crud.get_agent_by_id(db, asset_id) for asset_id in asset_ids]
    response: List[schemas.AssetInventorySummary] = []
    for asset in assets:
        if not asset:
            continue
        response.append(
            schemas.AssetInventorySummary(
                asset=schemas.Agent.model_validate(asset),
                risk=_risk_summary(db, tenant_id, asset.id),
            )
        )
    return response


@router.get(
    "/inventory/assets/{asset_id}", response_model=schemas.InventoryAssetDetail
)
def get_asset_inventory_detail(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> schemas.InventoryAssetDetail:
    asset = crud.get_agent_by_id(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    tenant_id = current_user.tenant_id or "default"
    software = crud.list_software_components(db, tenant_id, asset_id=asset_id)
    return schemas.InventoryAssetDetail(
        asset=schemas.Agent.model_validate(asset),
        software=[schemas.SoftwareComponent.model_validate(item) for item in software],
        risk=_risk_summary(db, tenant_id, asset_id),
    )


@router.get(
    "/inventory/assets/{asset_id}/vulnerabilities",
    response_model=schemas.AssetVulnerabilityListResponse,
)
def list_asset_vulnerabilities(
    asset_id: int,
    status: Optional[str] = Query(None),
    min_risk: Optional[str] = Query(None),
    kev: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> schemas.AssetVulnerabilityListResponse:
    tenant_id = current_user.tenant_id or "default"
    stmt = (
        select(models.AssetVulnerability)
        .options(
            joinedload(models.AssetVulnerability.vulnerability),
            joinedload(models.AssetVulnerability.software_component),
        )
        .where(
            models.AssetVulnerability.tenant_id == tenant_id,
            models.AssetVulnerability.asset_id == asset_id,
        )
    )
    if status:
        stmt = stmt.where(models.AssetVulnerability.status == status)
    if min_risk:
        labels = _risk_labels_from_min(min_risk)
        if labels:
            stmt = stmt.where(models.AssetVulnerability.risk_label.in_(labels))
    if kev is True:
        stmt = stmt.join(models.VulnerabilityRecord).where(
            models.VulnerabilityRecord.kev.is_(True)
        )
    if search:
        stmt = stmt.join(models.SoftwareComponent).where(
            models.SoftwareComponent.name.ilike(f"%{search}%")
        )
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar_one()
    rows = db.execute(stmt.limit(limit).offset(offset)).scalars().all()
    return schemas.AssetVulnerabilityListResponse(
        items=[schemas.AssetVulnerability.model_validate(item) for item in rows],
        total=total,
    )


@router.get(
    "/vulnerabilities", response_model=List[schemas.GlobalVulnerabilityRecord]
)
def list_global_vulnerabilities(
    min_risk: Optional[str] = Query(None),
    kev: Optional[bool] = Query(None),
    epss_min: Optional[float] = Query(None),
    cve_id: Optional[str] = Query(None),
    software_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> List[schemas.GlobalVulnerabilityRecord]:
    tenant_id = current_user.tenant_id or "default"
    stmt = (
        select(models.AssetVulnerability)
        .options(
            joinedload(models.AssetVulnerability.vulnerability),
            joinedload(models.AssetVulnerability.software_component),
        )
        .where(models.AssetVulnerability.tenant_id == tenant_id)
    )
    if min_risk:
        labels = _risk_labels_from_min(min_risk)
        if labels:
            stmt = stmt.where(models.AssetVulnerability.risk_label.in_(labels))
    if kev is True:
        stmt = stmt.join(models.VulnerabilityRecord).where(
            models.VulnerabilityRecord.kev.is_(True)
        )
    if epss_min is not None:
        stmt = stmt.join(models.VulnerabilityRecord).where(
            models.VulnerabilityRecord.epss_score >= epss_min
        )
    if cve_id:
        stmt = stmt.join(models.VulnerabilityRecord).where(
            models.VulnerabilityRecord.cve_id == cve_id
        )
    if software_name:
        stmt = stmt.join(models.SoftwareComponent).where(
            models.SoftwareComponent.name.ilike(f"%{software_name}%")
        )
    rows = db.execute(stmt.order_by(models.AssetVulnerability.last_seen_at.desc())).scalars().all()
    response: List[schemas.GlobalVulnerabilityRecord] = []
    for finding in rows:
        asset = crud.get_agent_by_id(db, finding.asset_id)
        response.append(
            schemas.GlobalVulnerabilityRecord(
                asset_id=finding.asset_id,
                asset_name=asset.name if asset else None,
                finding=schemas.AssetVulnerability.model_validate(finding),
            )
        )
    return response


@router.post(
    "/inventory/assets/{asset_id}/vulnerabilities/{finding_id}/status",
    response_model=schemas.AssetVulnerability,
)
def update_finding_status(
    asset_id: int,
    finding_id: int,
    payload: schemas.AssetVulnerabilityStatusUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> schemas.AssetVulnerability:
    tenant_id = current_user.tenant_id or "default"
    finding = db.execute(
        select(models.AssetVulnerability).where(
            models.AssetVulnerability.id == finding_id,
            models.AssetVulnerability.asset_id == asset_id,
            models.AssetVulnerability.tenant_id == tenant_id,
        )
    ).scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    finding.status = payload.status
    db.add(finding)
    db.commit()
    db.refresh(finding)
    return schemas.AssetVulnerability.model_validate(finding)
