from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(_type, _compiler, **_kw):  # type: ignore[override]
    return "JSON"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(64))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512))
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Madrid")
    tenant_id: Mapped[str] = mapped_column(
        String(64), default="default", index=True
    )
    team: Mapped[Optional[str]] = mapped_column(String(128))
    manager: Mapped[Optional[str]] = mapped_column(String(128))
    computer: Mapped[Optional[str]] = mapped_column(String(128))
    mobile_phone: Mapped[Optional[str]] = mapped_column(String(64))

    alerts = relationship(
        "Alert",
        back_populates="owner",
        cascade="all, delete-orphan",
        foreign_keys="Alert.owner_id",
    )
    assigned_alerts = relationship(
        "Alert",
        back_populates="assignee",
        foreign_keys="Alert.assigned_to",
    )
    incidents_assigned = relationship(
        "Incident",
        back_populates="assignee",
        foreign_keys="Incident.assigned_to",
    )
    incidents_created = relationship(
        "Incident",
        back_populates="creator",
        foreign_keys="Incident.created_by",
    )


class Agent(Base, TimestampMixin):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    os: Mapped[str] = mapped_column(String(64))
    ip_address: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="offline")
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    version: Mapped[Optional[str]] = mapped_column(String(32))
    tags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    api_key: Mapped[str] = mapped_column(String(64), unique=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_ip: Mapped[Optional[str]] = mapped_column(String(64))


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(128))
    category: Mapped[str] = mapped_column(String(128))
    severity: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="open")
    url: Mapped[Optional[str]] = mapped_column(String(512))
    sender: Mapped[Optional[str]] = mapped_column(String(255))
    username: Mapped[Optional[str]] = mapped_column(String(255))
    hostname: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    assigned_to: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    conclusion: Mapped[Optional[str]] = mapped_column(Text)
    owner = relationship("User", back_populates="alerts", foreign_keys=[owner_id])
    assignee = relationship(
        "User",
        back_populates="assigned_alerts",
        foreign_keys=[assigned_to],
    )


class Workplan(Base):
    __tablename__ = "workplans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    owner_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(32), default="open")
    priority: Mapped[Optional[str]] = mapped_column(String(32))
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    context_type: Mapped[Optional[str]] = mapped_column(String(64))
    context_id: Mapped[Optional[int]] = mapped_column(Integer)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    items = relationship(
        "WorkplanItem",
        back_populates="workplan",
        cascade="all, delete-orphan",
    )
    flow = relationship(
        "WorkplanFlow",
        back_populates="workplan",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Handover(Base):
    __tablename__ = "handovers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shift_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    shift_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    analyst_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    alerts_summary: Mapped[str] = mapped_column(Text, default="")
    notes_to_next_shift: Mapped[str] = mapped_column(Text, default="")
    links: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSONB)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    analyst = relationship("User", foreign_keys=[analyst_user_id])
    creator = relationship("User", foreign_keys=[created_by])


class WorkplanItem(Base):
    __tablename__ = "workplan_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workplan_id: Mapped[int] = mapped_column(
        ForeignKey("workplans.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="open")
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    assignee_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    workplan = relationship("Workplan", back_populates="items")


class WorkplanFlow(Base):
    __tablename__ = "workplan_flow"

    workplan_id: Mapped[int] = mapped_column(
        ForeignKey("workplans.id", ondelete="CASCADE"),
        primary_key=True,
    )
    format: Mapped[str] = mapped_column(String(32), default="reactflow")
    nodes: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    edges: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    viewport: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    workplan = relationship("Workplan", back_populates="flow")


class NotificationEvent(Base):
    __tablename__ = "notification_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64))
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[int] = mapped_column(Integer)
    recipient_email: Mapped[str] = mapped_column(String(255))
    recipients: Mapped[List[str]] = mapped_column(JSONB, default=list)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    error: Mapped[Optional[str]] = mapped_column(Text)
    bucket_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class AnalyticRule(Base):
    __tablename__ = "analytic_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[str] = mapped_column(String(32), default="medium")
    category: Mapped[Optional[str]] = mapped_column(String(128))
    data_sources: Mapped[List[str]] = mapped_column(JSONB, default=list)
    query: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    tags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CorrelationRule(Base):
    __tablename__ = "correlation_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[str] = mapped_column(String(32), default="medium")
    window_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    logic: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    tags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WarRoomNote(Base):
    __tablename__ = "warroom_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_id: Mapped[Optional[int]] = mapped_column(ForeignKey("alerts.id"))
    content: Mapped[str] = mapped_column(Text)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    attachments: Mapped[List[str]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


class WorkGroup(Base):
    __tablename__ = "workgroups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[Optional[str]] = mapped_column(Text)
    members: Mapped[List[int]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


class AlertEscalation(Base):
    __tablename__ = "alert_escalations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"))
    escalated_to: Mapped[int] = mapped_column(ForeignKey("users.id"))
    escalated_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


class ActionLog(Base):
    __tablename__ = "action_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action_type: Mapped[str] = mapped_column(String(128))
    target_type: Mapped[str] = mapped_column(String(128))
    target_id: Mapped[int] = mapped_column(Integer)
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )


class SandboxResult(Base):
    __tablename__ = "sandbox_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String(32))
    value: Mapped[str] = mapped_column(String(512))
    filename: Mapped[Optional[str]] = mapped_column(String(255))
    verdict: Mapped[str] = mapped_column(String(64))
    threat_type: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(64))
    progress: Mapped[int] = mapped_column(Integer, default=0)
    file_hash: Mapped[Optional[str]] = mapped_column(String(255))
    iocs: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    endpoints: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    vt_results: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    osint_results: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    yara_matches: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )


class Indicator(Base):
    __tablename__ = "indicators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String(32))
    value: Mapped[str] = mapped_column(String(512))
    description: Mapped[Optional[str]] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(32))
    source: Mapped[str] = mapped_column(String(128))
    tags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class BiocRule(Base):
    __tablename__ = "bioc_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    platform: Mapped[str] = mapped_column(String(64))
    tactic: Mapped[str] = mapped_column(String(64))
    technique: Mapped[Optional[str]] = mapped_column(String(64))
    detection_logic: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(32))
    tags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(32), default="enabled")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class AnalyticsRule(Base):
    __tablename__ = "analytics_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    datasource: Mapped[str] = mapped_column(String(128))
    severity: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="enabled")
    query: Mapped[str] = mapped_column(Text)
    owner: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Endpoint(Base):
    __tablename__ = "endpoints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hostname: Mapped[str] = mapped_column(String(128))
    display_name: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32))
    agent_status: Mapped[str] = mapped_column(String(32))
    agent_version: Mapped[str] = mapped_column(String(32))
    ip_address: Mapped[str] = mapped_column(String(64))
    owner: Mapped[str] = mapped_column(String(128))
    os: Mapped[str] = mapped_column(String(64))
    os_version: Mapped[str] = mapped_column(String(64))
    cpu_model: Mapped[str] = mapped_column(String(128))
    ram_gb: Mapped[int] = mapped_column(Integer)
    disk_gb: Mapped[int] = mapped_column(Integer)
    resource_usage: Mapped[Dict[str, float]] = mapped_column(JSONB, default=dict)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    location: Mapped[str] = mapped_column(String(128))
    processes: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    alerts_open: Mapped[int] = mapped_column(Integer, default=0)
    tags: Mapped[List[str]] = mapped_column(JSONB, default=list)


class EndpointAction(Base):
    __tablename__ = "endpoint_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    endpoint_id: Mapped[Optional[int]] = mapped_column(ForeignKey("endpoints.id"))
    action_type: Mapped[str] = mapped_column(String(32))
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    requested_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    output: Mapped[Optional[str]] = mapped_column(Text)


class NetworkSensor(Base, TimestampMixin):
    __tablename__ = "network_sensors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    kind: Mapped[str] = mapped_column(String(32))
    location: Mapped[Optional[str]] = mapped_column(String(255))
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class NetworkEvent(Base, TimestampMixin):
    __tablename__ = "network_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(64))
    source: Mapped[str] = mapped_column(String(32))
    event_type: Mapped[str] = mapped_column(String(64))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    src_ip: Mapped[Optional[str]] = mapped_column(String(64))
    src_port: Mapped[Optional[int]] = mapped_column(Integer)
    dst_ip: Mapped[Optional[str]] = mapped_column(String(64))
    dst_port: Mapped[Optional[int]] = mapped_column(Integer)
    proto: Mapped[Optional[str]] = mapped_column(String(32))
    direction: Mapped[Optional[str]] = mapped_column(String(32))
    sensor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("network_sensors.id"))
    signature: Mapped[Optional[str]] = mapped_column(String(255))
    category: Mapped[Optional[str]] = mapped_column(String(128))
    severity: Mapped[Optional[int]] = mapped_column(Integer)
    flow_id: Mapped[Optional[str]] = mapped_column(String(128))
    uid: Mapped[Optional[str]] = mapped_column(String(128))
    community_id: Mapped[Optional[str]] = mapped_column(String(128))
    http_host: Mapped[Optional[str]] = mapped_column(String(255))
    http_url: Mapped[Optional[str]] = mapped_column(String(512))
    http_method: Mapped[Optional[str]] = mapped_column(String(32))
    http_status: Mapped[Optional[int]] = mapped_column(Integer)
    dns_query: Mapped[Optional[str]] = mapped_column(String(255))
    dns_type: Mapped[Optional[str]] = mapped_column(String(64))
    dns_rcode: Mapped[Optional[str]] = mapped_column(String(64))
    tls_sni: Mapped[Optional[str]] = mapped_column(String(255))
    tls_ja3: Mapped[Optional[str]] = mapped_column(String(128))
    tls_version: Mapped[Optional[str]] = mapped_column(String(64))
    tags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    raw: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)


class NetworkIngestError(Base, TimestampMixin):
    __tablename__ = "network_ingest_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(64))
    source: Mapped[str] = mapped_column(String(32))
    sensor_name: Mapped[Optional[str]] = mapped_column(String(128))
    ts: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str] = mapped_column(String(255))
    raw_snippet: Mapped[Optional[str]] = mapped_column(Text)


class PasswordGuardEvent(Base, TimestampMixin):
    __tablename__ = "password_guard_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    host_id: Mapped[str] = mapped_column(String(128), index=True)
    user: Mapped[str] = mapped_column(String(255), index=True)
    entry_id: Mapped[str] = mapped_column(String(128), index=True)
    entry_label: Mapped[str] = mapped_column(String(255))
    exposure_count: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(64), index=True)
    event_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    client_version: Mapped[str] = mapped_column(String(64))
    alert_id: Mapped[Optional[int]] = mapped_column(ForeignKey("alerts.id"))

    alert = relationship("Alert")


class PasswordGuardIngestAudit(Base):
    __tablename__ = "password_guard_ingest_audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("password_guard_events.id", ondelete="CASCADE")
    )
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    ingested_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    agent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("agents.id"))
    token_id: Mapped[str] = mapped_column(String(128))
    ip_address: Mapped[Optional[str]] = mapped_column(String(64))
    user_agent: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    event = relationship("PasswordGuardEvent")
    ingested_by_user = relationship("User")
    agent = relationship("Agent")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("agents.id"))
    event_type: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(32))
    category: Mapped[Optional[str]] = mapped_column(String(128))
    details: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


class ResponseAction(Base, TimestampMixin):
    __tablename__ = "response_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(64))
    action_type: Mapped[str] = mapped_column(String(64))
    target: Mapped[str] = mapped_column(String(255))
    ttl_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="requested")
    requested_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    details: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)


class Incident(Base, TimestampMixin):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="new")
    assigned_to: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    tags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    assignee = relationship(
        "User",
        back_populates="incidents_assigned",
        foreign_keys=[assigned_to],
    )
    creator = relationship(
        "User",
        back_populates="incidents_created",
        foreign_keys=[created_by],
    )


class IncidentItem(Base):
    __tablename__ = "incident_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[int] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE")
    )
    kind: Mapped[str] = mapped_column(String(32))
    ref_id: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


class DetectionRule(Base, TimestampMixin):
    __tablename__ = "detection_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(32))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    conditions: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    create_incident: Mapped[bool] = mapped_column(Boolean, default=False)


class TenantStoragePolicy(Base, TimestampMixin):
    __tablename__ = "tenant_storage_policy"

    tenant_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    data_lake_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    hot_days: Mapped[int] = mapped_column(Integer, default=30)
    cold_days: Mapped[int] = mapped_column(Integer, default=365)
    sampling_policy: Mapped[str] = mapped_column(String(64), default="none")
    dedup_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    legal_hold: Mapped[bool] = mapped_column(Boolean, default=False)


class TenantUsageDaily(Base, TimestampMixin):
    __tablename__ = "tenant_usage_daily"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    bytes_ingested: Mapped[int] = mapped_column(BigInteger, default=0)
    docs_ingested: Mapped[int] = mapped_column(BigInteger, default=0)
    query_count: Mapped[int] = mapped_column(Integer, default=0)
    hot_est: Mapped[int] = mapped_column(BigInteger, default=0)
    cold_est: Mapped[int] = mapped_column(BigInteger, default=0)


class RehydrationJob(Base):
    __tablename__ = "rehydration_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    dataset: Mapped[str] = mapped_column(String(128))
    time_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    time_to: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str] = mapped_column(String(255))
    case_id: Mapped[Optional[str]] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="requested")
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    ttl_hours: Mapped[int] = mapped_column(Integer, default=24)


class ColdObject(Base):
    __tablename__ = "cold_objects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    dataset: Mapped[str] = mapped_column(String(128))
    day: Mapped[date] = mapped_column(Date, index=True)
    object_key: Mapped[str] = mapped_column(String(512))
    bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


class InventorySnapshot(Base):
    __tablename__ = "inventory_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"))
    category: Mapped[str] = mapped_column(String(32))
    data: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


class VulnerabilityDefinition(Base, TimestampMixin):
    __tablename__ = "vulnerability_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cve_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(32))
    affected_products: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)


class AgentVulnerability(Base):
    __tablename__ = "agent_vulnerabilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"))
    definition_id: Mapped[int] = mapped_column(
        ForeignKey("vulnerability_definitions.id", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(String(32), default="open")
    evidence: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class SCAResult(Base):
    __tablename__ = "sca_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"))
    policy_id: Mapped[str] = mapped_column(String(128))
    policy_name: Mapped[str] = mapped_column(String(255))
    score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="unknown")
    passed_checks: Mapped[int] = mapped_column(Integer, default=0)
    failed_checks: Mapped[int] = mapped_column(Integer, default=0)
    details: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
