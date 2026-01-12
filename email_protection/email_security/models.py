import base64
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

class TenantCreate(BaseModel):
    name: str
    feature_flags: Dict[str, bool] = Field(default_factory=dict)

class TenantRecord(TenantCreate):
    id: str
    status: str
    created_at: datetime

class DomainCreate(BaseModel):
    tenant_id: str
    domain: str

class DomainRecord(DomainCreate):
    id: str
    verified: bool
    verification_token: str
    created_at: datetime
    updated_at: datetime

class ConnectorCreate(BaseModel):
    tenant_id: str
    connector_type: str
    config: Dict[str, Any] = Field(default_factory=dict)

class ConnectorRecord(ConnectorCreate):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime

class PolicyCondition(BaseModel):
    type: str
    value: Optional[str] = None
    operator: Optional[str] = None

class PolicyAction(BaseModel):
    type: str
    value: Optional[str] = None

class PolicyCreate(BaseModel):
    tenant_id: str
    name: str
    direction: str
    enabled: bool = True
    conditions: List[PolicyCondition] = Field(default_factory=list)
    actions: List[PolicyAction] = Field(default_factory=list)

class PolicyRecord(PolicyCreate):
    id: str
    created_at: datetime
    updated_at: datetime

class AttachmentInput(BaseModel):
    filename: str
    content_base64: Optional[str] = None
    size: Optional[int] = None
    mime: Optional[str] = None

    def decoded_bytes(self) -> bytes:
        if not self.content_base64:
            return b""
        return base64.b64decode(self.content_base64)

class UrlInput(BaseModel):
    url: str

class AuthResults(BaseModel):
    spf: Optional[str] = None
    dkim: Optional[str] = None
    dmarc: Optional[str] = None

class IngestMessage(BaseModel):
    tenant_id: str
    direction: str
    sender: str
    recipients: List[str]
    subject: str
    body: Optional[str] = None
    attachments: List[AttachmentInput] = Field(default_factory=list)
    urls: List[UrlInput] = Field(default_factory=list)
    auth_results: Optional[AuthResults] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class IngestResponse(BaseModel):
    message_id: str
    verdict: str
    score: int
    actions: List[PolicyAction]
    quarantine_id: Optional[str] = None

class QuarantineRecord(BaseModel):
    id: str
    tenant_id: str
    message_id: str
    reason: str
    status: str
    stored_at: datetime
    released_at: Optional[datetime] = None

class AnalyzerSubmit(BaseModel):
    tenant_id: str
    message_id: str
    sample_type: str
    sample_ref: str

class AnalyzerVerdict(BaseModel):
    tenant_id: str
    job_id: str
    verdict: str
    iocs: List[str] = Field(default_factory=list)

class SiemEvent(BaseModel):
    id: str
    tenant_id: str
    event_type: str
    message_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class IdentityProviderConfig(BaseModel):
    tenant_id: str
    issuer: str
    client_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
