from __future__ import annotations

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

import logging
import time
import uuid

from .. import schemas, search
from ..metrics import QUERY_DURATION_SECONDS, QUERY_ERRORS_TOTAL
from ..auth import get_current_user
from ..kql import KqlParseError, KqlQueryPlan, build_query_plan


def _collect_mapping_fields(index_pattern: str) -> set[str]:
    mapping = search.client.indices.get_mapping(index=index_pattern)
    properties: dict[str, Any] = {}
    for index_data in mapping.values():
        props = index_data.get("mappings", {}).get("properties", {})
        if isinstance(props, dict):
            properties.update(props)
    return set(properties.keys())

router = APIRouter(prefix="/search", tags=["search"])
logger = logging.getLogger("eventsec.kql")


class KqlQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000)
    limit: Optional[int] = Field(default=None, ge=1, le=500)


class KqlQueryResponse(BaseModel):
    query: str
    index: str
    took_ms: int
    total: int
    hits: List[dict[str, Any]]
    fields: Optional[List[str]] = None
    error_type: Optional[str] = None


@router.post("/kql", response_model=KqlQueryResponse)
def execute_kql_query(
    payload: KqlQueryRequest,
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> KqlQueryResponse:
    del current_user  # FastAPI dependency check (value not used further)
    request_id = str(uuid.uuid4())
    start = time.monotonic()
    try:
        plan: KqlQueryPlan = build_query_plan(payload.query, payload.limit or 200)
    except KqlParseError as exc:
        QUERY_ERRORS_TOTAL.labels(error_type="SYNTAX_ERROR").inc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_type": "SYNTAX_ERROR", "message": str(exc)},
        ) from exc

    if not search.client.indices.exists(index=plan.index):
        QUERY_ERRORS_TOTAL.labels(error_type="TABLE_NOT_FOUND").inc()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_type": "TABLE_NOT_FOUND",
                "message": f"Index not found: {plan.index}",
            },
        )

    if plan.fields:
        props = _collect_mapping_fields(plan.index)
        if props:
            missing_fields = [field for field in plan.fields if field not in props]
            if missing_fields:
                QUERY_ERRORS_TOTAL.labels(error_type="FIELD_NOT_FOUND").inc()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_type": "FIELD_NOT_FOUND",
                        "message": f"Unknown fields: {', '.join(missing_fields)}",
                    },
                )

    body: dict[str, Any] = {
        "size": plan.size,
        "query": plan.query,
        "sort": [{plan.sort_field: {"order": "desc"}}],
    }
    if plan.fields:
        body["_source"] = plan.fields

    try:
        response = search.client.search(index=plan.index, body=body)
    except Exception as exc:  # noqa: BLE001
        QUERY_ERRORS_TOTAL.labels(error_type="OPENSEARCH_ERROR").inc()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"error_type": "OPENSEARCH_ERROR", "message": str(exc)},
        ) from exc

    hits = [hit["_source"] for hit in response.get("hits", {}).get("hits", [])]
    total_meta = response.get("hits", {}).get("total", {"value": len(hits)})
    total = total_meta.get(
        "value", total_meta if isinstance(total_meta, int) else len(hits)
    )

    duration = time.monotonic() - start
    QUERY_DURATION_SECONDS.observe(duration)
    logger.info(
        "kql_query",
        extra={
            "request_id": request_id,
            "index": plan.index,
            "duration_ms": int(duration * 1000),
            "rows": total,
        },
    )
    return KqlQueryResponse(
        query=payload.query,
        index=plan.index,
        took_ms=response.get("took", 0),
        total=total,
        hits=hits,
        fields=plan.fields,
    )
