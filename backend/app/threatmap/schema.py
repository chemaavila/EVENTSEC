from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


class AttackType(str, Enum):
    Web = "Web"
    DDoS = "DDoS"
    Intrusion = "Intrusion"
    Scanner = "Scanner"
    Anonymizer = "Anonymizer"
    Bot = "Bot"
    Malware = "Malware"
    Phishing = "Phishing"
    DNS = "DNS"
    Email = "Email"


class Geo(BaseModel):
    lat: float | None = None
    lon: float | None = None
    country: str | None = None
    city: str | None = None

    @model_validator(mode="after")
    def _latlon_consistency(self) -> "Geo":
        # Deterministic rule: if one of lat/lon is missing, treat both as unknown.
        if (self.lat is None) ^ (self.lon is None):
            self.lat = None
            self.lon = None
        return self


class Asn(BaseModel):
    asn: str | None = None
    org: str | None = None


class Endpoint(BaseModel):
    ip: str | None = None
    asn: Asn | None = None
    geo: Geo | None = None


class Volume(BaseModel):
    pps: int | None = None
    bps: int | None = None


class AttackEvent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    ts: datetime
    src: Endpoint
    dst: Endpoint
    attack_type: AttackType
    severity: int = Field(ge=1, le=10)
    volume: Volume | None = None
    tags: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    source: str
    real: bool = True

    # Server-derived stability fields (authoritative for clients)
    ttl_ms: int = Field(ge=1_000, le=600_000)
    expires_at: datetime
    is_major: bool

    # Server stream envelope (assigned on publish)
    seq: int | None = None
    server_ts: datetime | None = None

    @field_validator("ts", mode="before")
    @classmethod
    def _parse_ts(cls, v: Any) -> datetime:
        if isinstance(v, datetime):
            dt = v
        else:
            dt = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @model_validator(mode="after")
    def _derive_fields(self) -> "AttackEvent":
        self.is_major = bool(self.severity >= 7)
        if self.expires_at is None:
            self.expires_at = self.ts + timedelta(milliseconds=int(self.ttl_ms))
        if self.expires_at.tzinfo is None:
            self.expires_at = self.expires_at.replace(tzinfo=timezone.utc)
        self.expires_at = self.expires_at.astimezone(timezone.utc)
        return self


class IngestEventIn(BaseModel):
    # Allow ingest without id/ttl/expires; server will normalize deterministically.
    id: UUID | None = None
    ts: datetime
    src_ip: str | None = None
    dst_ip: str | None = None
    attack_type: AttackType
    severity: int = Field(ge=1, le=10)
    volume: Volume | None = None
    tags: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    source: str = "ingest"

    @field_validator("ts", mode="before")
    @classmethod
    def _parse_ts(cls, v: Any) -> datetime:
        if isinstance(v, datetime):
            dt = v
        else:
            dt = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)


class HeatBucket(BaseModel):
    # simple fixed grid bucket
    lat_bin: int
    lon_bin: int
    count: int
    severity_sum: int


class Aggregates(BaseModel):
    window: str
    server_ts: datetime
    seq: int

    count: int
    eps: float
    top_sources: list[tuple[str, int]]
    top_targets: list[tuple[str, int]]
    top_types: list[tuple[str, int]]
    by_severity: list[tuple[int, int]]
    heat: list[HeatBucket]


class WsHb(BaseModel):
    type: str = "hb"
    server_ts: datetime
    seq: int


class WsMode(BaseModel):
    type: str = "mode"
    server_ts: datetime
    mode: str
    reason: str


class WsEvent(BaseModel):
    type: str = "event"
    server_ts: datetime
    seq: int
    payload: AttackEvent


class WsAgg(BaseModel):
    type: str = "agg"
    server_ts: datetime
    seq: int
    payload: Aggregates


class ClientTelemetry(BaseModel):
    type: str = "client_telemetry"
    render_fps: float | None = None
    queue_len: int | None = None
    dropped_events: int | None = None


class ClientSetFilters(BaseModel):
    type: str = "set_filters"
    window: str | None = None  # "5m"|"15m"|"1h"
    types: list[AttackType] | None = None
    min_severity: int | None = Field(default=None, ge=1, le=10)
    major_only: bool | None = None
    country: str | None = None  # filter destination country code or name (best-effort)
