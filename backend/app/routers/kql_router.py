from __future__ import annotations

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .. import schemas, search
from ..auth import get_current_user
from ..kql import KqlParseError, KqlQueryPlan, build_query_plan

router = APIRouter(prefix="/search", tags=["search"])


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


@router.post("/kql", response_model=KqlQueryResponse)
def execute_kql_query(
    payload: KqlQueryRequest,
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> KqlQueryResponse:
    del current_user  # FastAPI dependency check (value not used further)
    try:
        plan: KqlQueryPlan = build_query_plan(payload.query, payload.limit or 200)
    except KqlParseError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    body: dict[str, Any] = {
        "size": plan.size,
        "query": plan.query,
        "sort": [{"timestamp": {"order": "desc"}}],
    }
    if plan.fields:
        body["_source"] = plan.fields

    try:
        response = search.client.search(index=plan.index, body=body)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenSearch error: {exc}",
        ) from exc

    hits = [hit["_source"] for hit in response.get("hits", {}).get("hits", [])]
    total_meta = response.get("hits", {}).get("total", {"value": len(hits)})
    total = total_meta.get("value", total_meta if isinstance(total_meta, int) else len(hits))

    return KqlQueryResponse(
        query=payload.query,
        index=plan.index,
        took_ms=response.get("took", 0),
        total=total,
        hits=hits,
        fields=plan.fields,
    )

