from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel


AlertStatus = Literal["open", "in_progress", "closed"]
AlertSeverity = Literal["low", "medium", "high", "critical"]


class AlertBase(BaseModel):
    title: str
    description: str
    source: str
    category: str
    severity: AlertSeverity = "medium"
    url: Optional[str] = None
    sender: Optional[str] = None
    username: Optional[str] = None
    hostname: Optional[str] = None


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    status: Optional[AlertStatus] = None
    assigned_to: Optional[int] = None
    conclusion: Optional[str] = None


class Alert(AlertBase):
    id: int
    status: AlertStatus = "open"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    assigned_to: Optional[int] = None
    conclusion: Optional[str] = None

    class Config:
        from_attributes = True


class HandoverBase(BaseModel):
    shift_start: datetime
    shift_end: datetime
    alerts_summary: str = ""
    notes_to_next_shift: str = ""
    links: Optional[List[Dict[str, Any]]] = None


class HandoverCreate(HandoverBase):
    analyst_user_id: Optional[int] = None


class HandoverUpdate(BaseModel):
    shift_start: Optional[datetime] = None
    shift_end: Optional[datetime] = None
    analyst_user_id: Optional[int] = None
    alerts_summary: Optional[str] = None
    notes_to_next_shift: Optional[str] = None
    links: Optional[List[Dict[str, Any]]] = None


class Handover(HandoverBase):
    id: int
    analyst_user_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    id: int
    full_name: str
    role: str
    email: str
    avatar_url: Optional[str] = None
    timezone: str = "Europe/Madrid"
    team: Optional[str] = None
    manager: Optional[str] = None
    computer: Optional[str] = None
    mobile_phone: Optional[str] = None

    class Config:
        from_attributes = True


class UserRole(str, Enum):
    ADMIN = "admin"
    TEAM_LEAD = "team_lead"
    ANALYST = "analyst"
    SENIOR_ANALYST = "senior_analyst"


class UserCreate(BaseModel):
    full_name: str
    role: str
    email: str
    password: str
    team: Optional[str] = None
    manager: Optional[str] = None
    computer: Optional[str] = None
    mobile_phone: Optional[str] = None
    timezone: str = "Europe/Madrid"


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    team: Optional[str] = None
    manager: Optional[str] = None
    computer: Optional[str] = None
    mobile_phone: Optional[str] = None
    timezone: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


class AgentBase(BaseModel):
    name: str
    os: str
    ip_address: str
    version: Optional[str] = None
    tags: List[str] = []


class Agent(AgentBase):
    id: int
    status: str
    last_heartbeat: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    last_ip: Optional[str] = None

    class Config:
        from_attributes = True


class AgentEnrollRequest(BaseModel):
    name: str
    os: str
    ip_address: str
    version: Optional[str] = None
    enrollment_key: str


class AgentEnrollResponse(BaseModel):
    agent_id: int
    api_key: str


class AgentHeartbeat(BaseModel):
    version: Optional[str] = None
    ip_address: Optional[str] = None
    status: Optional[str] = None
    last_seen: datetime = datetime.utcnow()


class WorkGroup(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    members: List[int] = []
    created_at: datetime

    class Config:
        from_attributes = True


class WorkGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    members: List[int] = []


class AlertEscalation(BaseModel):
    id: int
    alert_id: int
    escalated_to: int
    escalated_by: int
    reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertEscalationCreate(BaseModel):
    alert_id: int
    escalated_to: int
    reason: Optional[str] = None


class Workplan(BaseModel):
    id: int
    title: str
    description: str
    owner_user_id: Optional[int] = None
    status: str = "open"
    priority: Optional[str] = None
    due_at: Optional[datetime] = None
    context_type: Optional[str] = None
    context_id: Optional[int] = None
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkplanCreate(BaseModel):
    title: str
    description: str
    owner_user_id: Optional[int] = None
    priority: Optional[str] = None
    due_at: Optional[datetime] = None
    context_type: Optional[str] = None
    context_id: Optional[int] = None


class WorkplanUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    owner_user_id: Optional[int] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_at: Optional[datetime] = None
    context_type: Optional[str] = None
    context_id: Optional[int] = None


class WorkplanItem(BaseModel):
    id: int
    workplan_id: int
    title: str
    status: str
    order_index: int
    assignee_user_id: Optional[int] = None
    due_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkplanItemCreate(BaseModel):
    title: str
    status: Optional[str] = None
    order_index: Optional[int] = None
    assignee_user_id: Optional[int] = None
    due_at: Optional[datetime] = None
    notes: Optional[str] = None


class WorkplanItemUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    order_index: Optional[int] = None
    assignee_user_id: Optional[int] = None
    due_at: Optional[datetime] = None
    notes: Optional[str] = None


class WorkplanFlow(BaseModel):
    workplan_id: int
    format: str = "reactflow"
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    viewport: Optional[Dict[str, Any]] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkplanFlowUpdate(BaseModel):
    format: str = "reactflow"
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    viewport: Optional[Dict[str, Any]] = None


class AnalyticRule(BaseModel):
    id: int
    title: str
    description: str
    severity: AlertSeverity = "medium"
    category: Optional[str] = None
    data_sources: List[str] = []
    query: Dict[str, Any] = {}
    tags: List[str] = []
    enabled: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class CorrelationRule(BaseModel):
    id: int
    title: str
    description: str
    severity: AlertSeverity = "medium"
    window_minutes: Optional[int] = None
    logic: Dict[str, Any] = {}
    tags: List[str] = []
    enabled: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class RuleToggleUpdate(BaseModel):
    enabled: Optional[bool] = None


class RuleImportPayload(BaseModel):
    analytic_rules: Optional[List[Dict[str, Any]]] = None
    correlation_rules: Optional[List[Dict[str, Any]]] = None


class ActionLog(BaseModel):
    id: int
    user_id: int
    action_type: str
    target_type: str
    target_id: int
    parameters: Dict[str, Any] = {}
    created_at: datetime


class ActionLogCreate(BaseModel):
    action_type: str
    target_type: str
    target_id: int
    parameters: Dict[str, Any] = {}


class WarRoomNote(BaseModel):
    id: int
    alert_id: Optional[int] = None
    content: str
    created_by: int
    attachments: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True


class WarRoomNoteCreate(BaseModel):
    alert_id: Optional[int] = None
    content: str
    attachments: List[str] = []


class SandboxAnalysisRequest(BaseModel):
    type: str  # "file", "ip", "url", "domain", "hash"
    value: str
    filename: Optional[str] = None
    metadata: Dict[str, Any] = {}


class YaraMatch(BaseModel):
    rule_id: str
    rule_name: str
    source: str
    description: Optional[str] = None
    tags: List[str] = []


class YaraRule(BaseModel):
    id: str
    name: str
    source: str
    description: Optional[str] = None
    author: Optional[str] = None
    reference: Optional[str] = None
    tags: List[str] = []
    rule: str


class SandboxAnalysisResult(BaseModel):
    id: int
    type: str
    value: str
    filename: Optional[str] = None
    verdict: str
    threat_type: Optional[str] = None
    status: str
    progress: int
    file_hash: Optional[str] = None
    iocs: List[Dict[str, str]]
    endpoints: List[Dict[str, Any]]
    vt_results: Optional[Dict[str, Any]] = None
    osint_results: Optional[Dict[str, Any]] = None
    yara_matches: List[YaraMatch] = []
    created_at: datetime

    class Config:
        from_attributes = True


class EndpointProcess(BaseModel):
    name: str
    pid: int
    user: str
    cpu: float
    ram: float


class Endpoint(BaseModel):
    id: int
    hostname: str
    display_name: str
    status: str
    agent_status: str
    agent_version: str
    ip_address: str
    owner: str
    os: str
    os_version: str
    cpu_model: str
    ram_gb: int
    disk_gb: int
    resource_usage: Dict[str, float]
    last_seen: datetime
    location: str
    processes: List[EndpointProcess]
    alerts_open: int
    tags: List[str] = []

    class Config:
        from_attributes = True


class IndicatorType(str, Enum):
    IP = "ip"
    URL = "url"
    DOMAIN = "domain"
    HASH = "hash"
    EMAIL = "email"
    FILE_PATH = "file_path"


class Indicator(BaseModel):
    id: int
    type: IndicatorType
    value: str
    description: Optional[str] = None
    severity: AlertSeverity = "medium"
    source: str = "manual"
    tags: List[str] = []
    status: Literal["active", "retired"] = "active"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IndicatorCreate(BaseModel):
    type: IndicatorType
    value: str
    description: Optional[str] = None
    severity: AlertSeverity = "medium"
    source: str = "manual"
    tags: List[str] = []


class IndicatorUpdate(BaseModel):
    description: Optional[str] = None
    severity: Optional[AlertSeverity] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[Literal["active", "retired"]] = None


class BiocRule(BaseModel):
    id: int
    name: str
    description: str
    platform: str
    tactic: str
    technique: Optional[str] = None
    detection_logic: str
    severity: AlertSeverity = "medium"
    status: Literal["enabled", "disabled"] = "enabled"
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BiocRuleCreate(BaseModel):
    name: str
    description: str
    platform: str
    tactic: str
    technique: Optional[str] = None
    detection_logic: str
    severity: AlertSeverity = "medium"
    tags: List[str] = []


class BiocRuleUpdate(BaseModel):
    description: Optional[str] = None
    platform: Optional[str] = None
    tactic: Optional[str] = None
    technique: Optional[str] = None
    detection_logic: Optional[str] = None
    severity: Optional[AlertSeverity] = None
    status: Optional[Literal["enabled", "disabled"]] = None
    tags: Optional[List[str]] = None


class AnalyticsRule(BaseModel):
    id: int
    name: str
    description: str
    datasource: str
    severity: AlertSeverity = "medium"
    status: Literal["enabled", "disabled"] = "enabled"
    query: str
    owner: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnalyticsRuleCreate(BaseModel):
    name: str
    description: str
    datasource: str
    severity: AlertSeverity = "medium"
    query: str
    owner: str


class AnalyticsRuleUpdate(BaseModel):
    description: Optional[str] = None
    datasource: Optional[str] = None
    severity: Optional[AlertSeverity] = None
    status: Optional[Literal["enabled", "disabled"]] = None
    query: Optional[str] = None
    owner: Optional[str] = None


class NetworkSensorPayload(BaseModel):
    name: str
    kind: Literal["suricata", "zeek"]
    location: Optional[str] = None


class NetworkIngestMeta(BaseModel):
    collector_version: Optional[str] = None
    host: Optional[str] = None
    file: Optional[str] = None
    offset: Optional[int] = None


class NetworkBulkIngestRequest(BaseModel):
    source: Literal["suricata", "zeek"]
    sensor: NetworkSensorPayload
    events: List[Dict[str, Any]]
    meta: Optional[NetworkIngestMeta] = None


class NetworkIngestErrorDetail(BaseModel):
    index: int
    reason: str
    hint: Optional[str] = None


class NetworkBulkIngestResponse(BaseModel):
    accepted: int
    rejected: int
    errors: List[NetworkIngestErrorDetail] = []
    created_sensor_id: Optional[int] = None


class NetworkEvent(BaseModel):
    id: str
    tenant_id: Optional[str] = None
    source: str
    event_type: str
    ts: datetime
    src_ip: Optional[str] = None
    src_port: Optional[int] = None
    dst_ip: Optional[str] = None
    dst_port: Optional[int] = None
    proto: Optional[str] = None
    direction: Optional[str] = None
    sensor_id: Optional[int] = None
    sensor_name: Optional[str] = None
    signature: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[int] = None
    flow_id: Optional[str] = None
    uid: Optional[str] = None
    community_id: Optional[str] = None
    http_host: Optional[str] = None
    http_url: Optional[str] = None
    http_method: Optional[str] = None
    http_status: Optional[int] = None
    dns_query: Optional[str] = None
    dns_type: Optional[str] = None
    dns_rcode: Optional[str] = None
    tls_sni: Optional[str] = None
    tls_ja3: Optional[str] = None
    tls_version: Optional[str] = None
    tags: List[str] = []
    raw: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NetworkSensor(BaseModel):
    id: int
    tenant_id: Optional[str] = None
    name: str
    kind: str
    location: Optional[str] = None
    last_seen_at: Optional[datetime] = None
    status: str
    error_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NetworkStats(BaseModel):
    total_events: int
    events_last_24h: int
    top_signatures: List[Dict[str, Any]]
    top_destinations: List[Dict[str, Any]]
    top_severities: List[Dict[str, Any]]


class SecurityEventCreate(BaseModel):
    event_type: str
    severity: AlertSeverity
    category: Optional[str] = None
    details: Dict[str, Any] = {}


class SecurityEvent(BaseModel):
    id: int
    agent_id: Optional[int]
    event_type: str
    severity: AlertSeverity
    category: Optional[str]
    details: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class IndexedEvent(BaseModel):
    event_id: Optional[int] = None
    agent_id: Optional[int] = None
    event_type: Optional[str] = None
    severity: Optional[str] = None
    category: Optional[str] = None
    timestamp: Optional[datetime] = None
    message: Optional[str] = None
    details: Dict[str, Any] = {}


class DetectionRule(BaseModel):
    id: int
    name: str
    description: Optional[str]
    severity: AlertSeverity
    enabled: bool
    conditions: Dict[str, Any]
    create_incident: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DetectionRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    severity: AlertSeverity = "medium"
    enabled: bool = True
    conditions: Dict[str, Any] = {}
    create_incident: bool = False


class ResponseActionBase(BaseModel):
    action_type: str
    target: str
    ttl_minutes: Optional[int] = None
    status: Optional[str] = None
    details: Dict[str, Any] = {}


class ResponseActionCreate(ResponseActionBase):
    pass


class ResponseActionUpdate(BaseModel):
    status: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ResponseAction(ResponseActionBase):
    id: int
    tenant_id: Optional[str] = None
    status: str
    requested_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


IncidentStatus = Literal[
    "new",
    "triage",
    "in_progress",
    "contained",
    "resolved",
    "closed",
]
IncidentSeverity = Literal["low", "medium", "high", "critical"]


class IncidentItem(BaseModel):
    id: int
    incident_id: int
    kind: str
    ref_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class IncidentItemCreate(BaseModel):
    kind: str
    ref_id: str


class IncidentBase(BaseModel):
    title: str
    description: Optional[str] = None
    severity: IncidentSeverity = "medium"
    status: IncidentStatus = "new"
    assigned_to: Optional[int] = None
    tags: List[str] = []


class IncidentCreate(IncidentBase):
    items: Optional[List[IncidentItemCreate]] = None


class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    assigned_to: Optional[int] = None
    tags: Optional[List[str]] = None


class Incident(IncidentBase):
    id: int
    tenant_id: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    items: List[IncidentItem] = []

    class Config:
        from_attributes = True


class InventorySnapshotCreate(BaseModel):
    category: str
    data: Dict[str, Any]


class InventorySnapshot(BaseModel):
    id: int
    agent_id: int
    category: str
    data: Dict[str, Any]
    collected_at: datetime

    class Config:
        from_attributes = True


class InventoryIngestRequest(BaseModel):
    snapshots: List[InventorySnapshotCreate]


class InventoryOverview(BaseModel):
    agent_id: int
    categories: Dict[str, List[InventorySnapshot]]


class VulnerabilityDefinitionCreate(BaseModel):
    cve_id: str
    title: str
    severity: AlertSeverity = "medium"
    description: Optional[str] = None
    affected_products: List[Dict[str, Any]] = []


class VulnerabilityDefinition(BaseModel):
    id: int
    cve_id: str
    title: str
    severity: AlertSeverity
    description: Optional[str] = None
    affected_products: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentVulnerability(BaseModel):
    id: int
    agent_id: int
    definition_id: int
    status: str
    evidence: Dict[str, Any]
    detected_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SCAResultCreate(BaseModel):
    policy_id: str
    policy_name: str
    score: float = 0
    status: str = "unknown"
    passed_checks: int = 0
    failed_checks: int = 0
    details: Dict[str, Any] = {}


class SCAResult(BaseModel):
    id: int
    agent_id: int
    policy_id: str
    policy_name: str
    score: float
    status: str
    passed_checks: int
    failed_checks: int
    details: Dict[str, Any]
    collected_at: datetime

    class Config:
        from_attributes = True


class EndpointAction(BaseModel):
    id: int
    endpoint_id: int
    action_type: Literal["isolate", "release", "reboot", "command"]
    parameters: Dict[str, Any] = {}
    status: Literal["pending", "completed", "failed"] = "pending"
    requested_by: Optional[int] = None
    requested_at: datetime
    completed_at: Optional[datetime] = None
    output: Optional[str] = None

    class Config:
        from_attributes = True


class EndpointActionCreate(BaseModel):
    action_type: Literal["isolate", "release", "reboot", "command"]
    parameters: Dict[str, Any] = {}


class EndpointActionResult(BaseModel):
    success: bool = True
    output: Optional[str] = None
