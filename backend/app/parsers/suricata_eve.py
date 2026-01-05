from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class SuricataParseError(ValueError):
    pass


@dataclass
class ParsedSuricataEvent:
    ts: datetime
    event_type: str
    src_ip: Optional[str]
    src_port: Optional[int]
    dst_ip: Optional[str]
    dst_port: Optional[int]
    proto: Optional[str]
    signature: Optional[str]
    category: Optional[str]
    severity: Optional[int]
    flow_id: Optional[str]
    community_id: Optional[str]
    http: Dict[str, Any]
    dns: Dict[str, Any]
    tls: Dict[str, Any]
    tags: list[str]


def _parse_timestamp(raw: Any) -> datetime:
    if isinstance(raw, datetime):
        return raw
    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(float(raw), tz=timezone.utc)
    if isinstance(raw, str):
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            raise SuricataParseError("invalid_timestamp") from exc
    raise SuricataParseError("missing_timestamp")


def parse_suricata_event(raw: Dict[str, Any]) -> ParsedSuricataEvent:
    if not isinstance(raw, dict):
        raise SuricataParseError("invalid_payload")

    event_type = raw.get("event_type")
    if not event_type:
        raise SuricataParseError("missing_event_type")

    ts = _parse_timestamp(raw.get("timestamp"))
    alert = raw.get("alert") or {}
    http = raw.get("http") or {}
    dns = raw.get("dns") or {}
    tls = raw.get("tls") or {}

    tags = raw.get("tags") if isinstance(raw.get("tags"), list) else []

    return ParsedSuricataEvent(
        ts=ts,
        event_type=str(event_type),
        src_ip=raw.get("src_ip"),
        src_port=raw.get("src_port"),
        dst_ip=raw.get("dest_ip") or raw.get("dst_ip"),
        dst_port=raw.get("dest_port") or raw.get("dst_port"),
        proto=raw.get("proto"),
        signature=alert.get("signature"),
        category=alert.get("category"),
        severity=alert.get("severity"),
        flow_id=str(raw.get("flow_id")) if raw.get("flow_id") is not None else None,
        community_id=raw.get("community_id"),
        http={
            "host": http.get("hostname"),
            "url": http.get("url"),
            "method": http.get("http_method"),
            "status": http.get("status"),
            "user_agent": http.get("http_user_agent"),
        }
        if isinstance(http, dict)
        else {},
        dns={
            "query": dns.get("rrname"),
            "type": dns.get("rrtype"),
            "rcode": dns.get("rcode"),
        }
        if isinstance(dns, dict)
        else {},
        tls={
            "sni": tls.get("sni"),
            "ja3": tls.get("ja3"),
            "version": tls.get("version"),
        }
        if isinstance(tls, dict)
        else {},
        tags=tags,
    )
