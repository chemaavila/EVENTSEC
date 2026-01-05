from __future__ import annotations

import csv
from datetime import date, timedelta
from io import StringIO
from typing import Iterable

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..auth import get_current_user
from ..database import get_db

router = APIRouter(prefix="/tenants/{tenant_id}", tags=["datalake"])


def _require_tenant_access(current_user: schemas.UserProfile, tenant_id: str) -> None:
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant access requires an assigned tenant",
        )
    if current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Tenant access denied"
        )


def _require_storage_admin(current_user: schemas.UserProfile) -> None:
    if current_user.role not in {"admin", "team_lead"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )


def _require_usage_role(current_user: schemas.UserProfile) -> None:
    if current_user.role not in {"admin", "senior_analyst", "analyst"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )


def _get_or_create_policy(
    db: Session, tenant_id: str
) -> schemas.TenantStoragePolicy:
    policy = crud.get_tenant_storage_policy(db, tenant_id)
    if policy is None:
        policy = crud.upsert_tenant_storage_policy(db, tenant_id, {})
    return policy


def _require_data_lake_enabled(policy: schemas.TenantStoragePolicy) -> None:
    if not policy.data_lake_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Data lake feature is disabled for this tenant",
        )


def _default_from_day() -> date:
    return date.today() - timedelta(days=30)


def _stream_usage_csv(items: Iterable[schemas.TenantUsageDaily]) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "tenant_id",
            "day",
            "bytes_ingested",
            "docs_ingested",
            "query_count",
            "hot_est",
            "cold_est",
        ]
    )
    for row in items:
        writer.writerow(
            [
                row.tenant_id,
                row.day.isoformat(),
                row.bytes_ingested,
                row.docs_ingested,
                row.query_count,
                row.hot_est,
                row.cold_est,
            ]
        )
    return buffer.getvalue()


@router.get("/storage-policy", response_model=schemas.TenantStoragePolicy)
def get_storage_policy(
    tenant_id: str,
    current_user: schemas.UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.TenantStoragePolicy:
    _require_tenant_access(current_user, tenant_id)
    return _get_or_create_policy(db, tenant_id)


@router.put("/storage-policy", response_model=schemas.TenantStoragePolicy)
def update_storage_policy(
    tenant_id: str,
    payload: schemas.TenantStoragePolicyUpdate,
    current_user: schemas.UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.TenantStoragePolicy:
    _require_storage_admin(current_user)
    _require_tenant_access(current_user, tenant_id)
    updates = payload.model_dump(exclude_unset=True)
    return crud.upsert_tenant_storage_policy(db, tenant_id, updates)


@router.get("/usage", response_model=schemas.TenantUsageResponse)
def get_usage(
    tenant_id: str,
    from_day: date | None = Query(None, alias="from"),
    to_day: date | None = Query(None, alias="to"),
    current_user: schemas.UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.TenantUsageResponse:
    _require_usage_role(current_user)
    _require_tenant_access(current_user, tenant_id)
    policy = _get_or_create_policy(db, tenant_id)
    _require_data_lake_enabled(policy)
    start_day = from_day or _default_from_day()
    end_day = to_day or date.today()
    if start_day > end_day:
        raise HTTPException(status_code=400, detail="Invalid date range")
    items = crud.list_tenant_usage(db, tenant_id, start_day, end_day)
    return schemas.TenantUsageResponse(
        tenant_id=tenant_id,
        from_day=start_day,
        to_day=end_day,
        items=items,
    )


@router.get("/usage/export.csv")
def export_usage_csv(
    tenant_id: str,
    from_day: date | None = Query(None, alias="from"),
    to_day: date | None = Query(None, alias="to"),
    current_user: schemas.UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    _require_usage_role(current_user)
    _require_tenant_access(current_user, tenant_id)
    policy = _get_or_create_policy(db, tenant_id)
    _require_data_lake_enabled(policy)
    start_day = from_day or _default_from_day()
    end_day = to_day or date.today()
    if start_day > end_day:
        raise HTTPException(status_code=400, detail="Invalid date range")
    items = crud.list_tenant_usage(db, tenant_id, start_day, end_day)
    csv_payload = _stream_usage_csv(items)
    return Response(
        content=csv_payload,
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f"attachment; filename=tenant_usage_{tenant_id}.csv"
            )
        },
    )
