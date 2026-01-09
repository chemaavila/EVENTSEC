from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from .. import crud, models, schemas, search
from ..auth import get_current_user, require_agent_auth
from ..config import settings
from ..database import get_db
from ..metrics import (
    NETWORK_INGEST_ACCEPTED_TOTAL,
    NETWORK_INGEST_REJECTED_TOTAL,
    NETWORK_INGEST_LATENCY_MS,
)
from ..parsers import parse_suricata_event, parse_zeek_event
from ..parsers.suricata_eve import SuricataParseError
from ..parsers.zeek_json import ZeekParseError

logger = logging.getLogger("eventsec.network")

router = APIRouter(prefix="/network", tags=["network"])
ingest_router = APIRouter(prefix="/ingest/network", tags=["network-ingest"])


def _map_severity(value: Optional[int]) -> str:
    if value is None:
        return "medium"
    if value <= 1:
        return "critical"
    if value == 2:
        return "high"
    if value == 3:
        return "medium"
    return "low"


def _sensor_status(last_seen_at: Optional[datetime]) -> str:
    if not last_seen_at:
        return "offline"
    now = datetime.now(timezone.utc)
    if last_seen_at >= now - timedelta(minutes=5):
        return "healthy"
    if last_seen_at >= now - timedelta(minutes=30):
        return "degraded"
    return "offline"


@ingest_router.post("/bulk", response_model=schemas.NetworkBulkIngestResponse)
async def ingest_network_bulk(
    payload: schemas.NetworkBulkIngestRequest,
    request: Request,
    db: Session = Depends(get_db),
    agent_auth: Optional[models.Agent] = Depends(require_agent_auth),
) -> schemas.NetworkBulkIngestResponse:
    del agent_auth

    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.network_ingest_max_bytes:
        raise HTTPException(status_code=413, detail="Payload too large")

    if len(payload.events) > settings.network_ingest_max_events:
        raise HTTPException(status_code=413, detail="Too many events in batch")

    start_time = time.monotonic()
    sensor = crud.get_network_sensor_by_name(db, payload.sensor.name)
    created_sensor_id = None
    if not sensor:
        sensor = models.NetworkSensor(
            tenant_id=None,
            name=payload.sensor.name,
            kind=payload.sensor.kind,
            location=payload.sensor.location,
            last_seen_at=datetime.now(timezone.utc),
        )
        sensor = crud.create_network_sensor(db, sensor)
        created_sensor_id = sensor.id
    else:
        sensor.kind = payload.sensor.kind
        sensor.location = payload.sensor.location
        sensor.last_seen_at = datetime.now(timezone.utc)
        crud.update_network_sensor(db, sensor)

    parsed_events: List[models.NetworkEvent] = []
    parser_errors: List[schemas.NetworkIngestErrorDetail] = []
    ingest_errors: List[models.NetworkIngestError] = []
    indexed_docs: List[Dict[str, object]] = []
    event_records: List[models.Event] = []

    for idx, raw in enumerate(payload.events):
        try:
            if payload.source == "suricata":
                parsed = parse_suricata_event(raw)
            else:
                parsed = parse_zeek_event(raw)
        except (SuricataParseError, ZeekParseError) as exc:
            reason = str(exc)
            parser_errors.append(
                schemas.NetworkIngestErrorDetail(index=idx, reason=reason)
            )
            ingest_errors.append(
                models.NetworkIngestError(
                    tenant_id=None,
                    source=payload.source,
                    sensor_name=payload.sensor.name,
                    ts=datetime.now(timezone.utc),
                    reason=reason,
                    raw_snippet=str(raw)[:500],
                )
            )
            continue

        event_id = str(uuid.uuid4())
        network_event = models.NetworkEvent(
            id=event_id,
            tenant_id=None,
            source=payload.source,
            event_type=parsed.event_type,
            ts=parsed.ts,
            src_ip=parsed.src_ip,
            src_port=parsed.src_port,
            dst_ip=parsed.dst_ip,
            dst_port=parsed.dst_port,
            proto=parsed.proto,
            direction=None,
            sensor_id=sensor.id,
            signature=getattr(parsed, "signature", None),
            category=getattr(parsed, "category", None),
            severity=getattr(parsed, "severity", None),
            flow_id=getattr(parsed, "flow_id", None),
            uid=getattr(parsed, "uid", None),
            community_id=getattr(parsed, "community_id", None),
            http_host=parsed.http.get("host"),
            http_url=parsed.http.get("url"),
            http_method=parsed.http.get("method"),
            http_status=parsed.http.get("status"),
            dns_query=parsed.dns.get("query"),
            dns_type=parsed.dns.get("type"),
            dns_rcode=parsed.dns.get("rcode"),
            tls_sni=parsed.tls.get("sni"),
            tls_ja3=parsed.tls.get("ja3"),
            tls_version=parsed.tls.get("version"),
            tags=parsed.tags,
            raw=raw,
        )
        parsed_events.append(network_event)

        details = {
            "source": payload.source,
            "event_type": parsed.event_type,
            "src_ip": parsed.src_ip,
            "src_port": parsed.src_port,
            "dst_ip": parsed.dst_ip,
            "dst_port": parsed.dst_port,
            "proto": parsed.proto,
            "signature": getattr(parsed, "signature", None),
            "category": getattr(parsed, "category", None),
            "severity": getattr(parsed, "severity", None),
            "http": parsed.http,
            "dns": parsed.dns,
            "tls": parsed.tls,
            "http.method": parsed.http.get("method"),
            "http.user_agent": parsed.http.get("user_agent"),
            "http.url": parsed.http.get("url"),
            "dns.query": parsed.dns.get("query"),
            "dns.rcode": parsed.dns.get("rcode"),
            "tls.sni": parsed.tls.get("sni"),
            "tls.ja3": parsed.tls.get("ja3"),
            "sensor": payload.sensor.name,
            "network_event_id": event_id,
        }
        event_records.append(
            models.Event(
                agent_id=None,
                event_type="network",
                severity=_map_severity(getattr(parsed, "severity", None)),
                category="network",
                details=details,
            )
        )

        indexed_docs.append(
            {
                "id": event_id,
                "tenant_id": None,
                "source": payload.source,
                "event_type": parsed.event_type,
                "ts": parsed.ts.isoformat(),
                "src_ip": parsed.src_ip,
                "src_port": parsed.src_port,
                "dst_ip": parsed.dst_ip,
                "dst_port": parsed.dst_port,
                "proto": parsed.proto,
                "direction": None,
                "sensor_name": payload.sensor.name,
                "signature": getattr(parsed, "signature", None),
                "category": getattr(parsed, "category", None),
                "severity": getattr(parsed, "severity", None),
                "flow_id": getattr(parsed, "flow_id", None),
                "uid": getattr(parsed, "uid", None),
                "community_id": getattr(parsed, "community_id", None),
                "http": parsed.http,
                "dns": parsed.dns,
                "tls": parsed.tls,
                "tags": parsed.tags,
                "raw": raw,
            }
        )

    if parsed_events:
        db.add_all(parsed_events)
        db.commit()

    if event_records:
        db.add_all(event_records)
        db.commit()

    if ingest_errors:
        crud.create_network_ingest_errors(db, ingest_errors)

    if indexed_docs:
        try:
            search.bulk_index_network_events(indexed_docs)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to index network events: %s", exc)

    queue = request.app.state.event_queue
    for event in event_records:
        try:
            queue.put_nowait(event.id)
        except Exception:  # noqa: BLE001
            logger.warning("Network event queue full, dropping event %s", event.id)

    accepted = len(parsed_events)
    rejected = len(parser_errors)
    NETWORK_INGEST_ACCEPTED_TOTAL.labels(source=payload.source).inc(accepted)
    NETWORK_INGEST_REJECTED_TOTAL.labels(source=payload.source).inc(rejected)
    NETWORK_INGEST_LATENCY_MS.observe((time.monotonic() - start_time) * 1000)
    logger.info(
        "network_ingest",
        extra={
            "source": payload.source,
            "sensor": payload.sensor.name,
            "accepted": accepted,
            "rejected": rejected,
        },
    )

    return schemas.NetworkBulkIngestResponse(
        accepted=accepted,
        rejected=rejected,
        errors=parser_errors,
        created_sensor_id=created_sensor_id,
    )


@router.get("/events", response_model=List[schemas.NetworkEvent])
def list_network_events(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    source: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    severity: Optional[int] = Query(None, ge=0, le=10),
    src_ip: Optional[str] = Query(None),
    dst_ip: Optional[str] = Query(None),
    src_port: Optional[int] = Query(None, ge=0, le=65535),
    dst_port: Optional[int] = Query(None, ge=0, le=65535),
    size: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> List[schemas.NetworkEvent]:
    del current_user
    try:
        docs = search.search_network_events(
            start_time=start_time,
            end_time=end_time,
            source=source,
            event_type=event_type,
            severity=severity,
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            size=size,
            offset=offset,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return [schemas.NetworkEvent(**doc) for doc in docs]


@router.get("/sensors", response_model=List[schemas.NetworkSensor])
def list_network_sensors(
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> List[schemas.NetworkSensor]:
    del current_user
    sensors = crud.list_network_sensors(db)
    payload: List[schemas.NetworkSensor] = []
    for sensor in sensors:
        error_count = (
            db.query(models.NetworkIngestError)
            .filter(models.NetworkIngestError.sensor_name == sensor.name)
            .count()
        )
        payload.append(
            schemas.NetworkSensor(
                id=sensor.id,
                tenant_id=sensor.tenant_id,
                name=sensor.name,
                kind=sensor.kind,
                location=sensor.location,
                last_seen_at=sensor.last_seen_at,
                status=_sensor_status(sensor.last_seen_at),
                error_count=error_count,
                created_at=sensor.created_at,
                updated_at=sensor.updated_at,
            )
        )
    return payload


@router.get("/stats", response_model=schemas.NetworkStats)
def get_network_stats(
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> schemas.NetworkStats:
    del current_user
    body = {
        "size": 0,
        "query": {"range": {"ts": {"gte": "now-24h", "lte": "now"}}},
        "aggs": {
            "total_events": {"value_count": {"field": "ts"}},
            "top_signatures": {"terms": {"field": "signature", "size": 5}},
            "top_destinations": {"terms": {"field": "dst_ip", "size": 5}},
            "top_severities": {"terms": {"field": "severity", "size": 5}},
        },
    }
    try:
        response = search.client.search(index="network-events-*", body=body)
    except Exception:  # noqa: BLE001
        return schemas.NetworkStats(
            total_events=0,
            events_last_24h=0,
            top_signatures=[],
            top_destinations=[],
            top_severities=[],
        )
    aggs = response.get("aggregations", {})
    total = aggs.get("total_events", {}).get("value", 0)
    return schemas.NetworkStats(
        total_events=total,
        events_last_24h=total,
        top_signatures=aggs.get("top_signatures", {}).get("buckets", []),
        top_destinations=aggs.get("top_destinations", {}).get("buckets", []),
        top_severities=aggs.get("top_severities", {}).get("buckets", []),
    )
