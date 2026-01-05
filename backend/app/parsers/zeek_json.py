from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class ZeekParseError(ValueError):
    pass


@dataclass
class ParsedZeekEvent:
    ts: datetime
    event_type: str
    src_ip: Optional[str]
    src_port: Optional[int]
    dst_ip: Optional[str]
    dst_port: Optional[int]
    proto: Optional[str]
    uid: Optional[str]
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
            return datetime.fromtimestamp(float(raw), tz=timezone.utc)
        except ValueError:
            try:
                return datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ZeekParseError("invalid_timestamp") from exc
    raise ZeekParseError("missing_timestamp")


def _infer_event_type(raw: Dict[str, Any]) -> str:
    for key in ("event_type", "log_type", "type", "_path"):
        value = raw.get(key)
        if isinstance(value, str) and value:
            return value
    return "conn"


def parse_zeek_event(raw: Dict[str, Any]) -> ParsedZeekEvent:
    if not isinstance(raw, dict):
        raise ZeekParseError("invalid_payload")

    ts = _parse_timestamp(raw.get("ts"))
    event_type = _infer_event_type(raw)

    tags = raw.get("tags") if isinstance(raw.get("tags"), list) else []

    return ParsedZeekEvent(
        ts=ts,
        event_type=event_type,
        src_ip=raw.get("id.orig_h") or raw.get("src_ip"),
        src_port=raw.get("id.orig_p") or raw.get("src_port"),
        dst_ip=raw.get("id.resp_h") or raw.get("dst_ip"),
        dst_port=raw.get("id.resp_p") or raw.get("dst_port"),
        proto=raw.get("proto"),
        uid=raw.get("uid"),
        community_id=raw.get("community_id"),
        http={
            "host": raw.get("host"),
            "url": raw.get("uri"),
            "method": raw.get("method"),
            "status": raw.get("status_code"),
            "user_agent": raw.get("user_agent"),
        },
        dns={
            "query": raw.get("query"),
            "type": raw.get("qtype_name") or raw.get("qtype"),
            "rcode": raw.get("rcode_name") or raw.get("rcode"),
        },
        tls={
            "sni": raw.get("server_name"),
            "ja3": raw.get("ja3"),
            "version": raw.get("version"),
        },
        tags=tags,
    )
