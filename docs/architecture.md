# Email Protection Architecture (EventSec)

## Logical flow (inbound/outbound)

```mermaid
flowchart LR
    subgraph Internet
        Sender[External Sender]
        Recipient[External Recipient]
    end

    subgraph EventSec Cloud
        Gateway[Cloud Email Security Gateway]
        Policy[Policy Engine]
        UrlDefense[URL Defense/Rewriter]
        Malware[Malware & Attachment Scan]
        Quarantine[Quarantine Store (S3/KMS)]
        Admin[Admin Console]
        Identity[Identity/SSO (Entra ID)]
        EventBus[Event Bus / SIEM Export]
        Analyzer[Advanced Analyzer (Optional, mTLS)]
    end

    subgraph Customer
        M365[M365/Exchange]
        OnPrem[On-Prem Analyzer/Responder (Optional)]
    end

    Sender -->|MX -> Gateway| Gateway
    Gateway --> Policy
    Policy --> UrlDefense
    Policy --> Malware
    Malware -->|clean| Gateway
    Malware -->|quarantine| Quarantine
    UrlDefense --> Gateway
    Gateway -->|TLS Relay| M365
    M365 -->|Outbound Connector| Gateway
    Gateway -->|Outbound filtered| Recipient
    Gateway --> EventBus
    Admin --> Policy
    Admin --> Quarantine
    Identity --> Admin
    Analyzer --> EventBus
    Analyzer --> Policy
    OnPrem --> Analyzer
```

## Components

- **Cloud Email Security Gateway**: TLS-capable SMTP ingress/egress, rate-limits, greylisting (optional), SPF/DKIM/DMARC evaluation, queueing, and relay.
- **Policy Engine**: per-tenant rule evaluation (allow/quarantine/reject/tag/encrypt). Supports DLP rules and per-group policies.
- **URL Defense**: normalization, reputation checks, optional URL rewrite (safe links).
- **Malware Scan**: ClamAV, file-type detection, macro detection, sandbox hook.
- **Quarantine Store**: metadata in Postgres, content blobs in object storage with KMS per tenant.
- **Admin Console**: policy, connectors, quarantines, reports, health.
- **Identity/SSO**: Entra ID OIDC/SAML, RBAC, SCIM/Graph sync.
- **Advanced Analyzer (Optional)**: on-prem/VM container, mTLS to cloud, YARA/sandbox, retroactive remediation via Graph API.
- **Integrations**: M365/Exchange connectors, smart host, journaling optional.
- **Event Bus/SIEM Export**: structured JSON events to webhook/syslog/OTEL.

## Multi-tenant data model (key tables)

- `tenants` (tenant_id, name, feature_flags, status)
- `domains` (tenant_id, domain, verified, txt_token)
- `connectors` (tenant_id, type, config)
- `policies` (tenant_id, direction, conditions, actions)
- `messages` (tenant_id, message_id, direction, verdict, score)
- `quarantine` (tenant_id, message_id, storage_key, status)
- `analyzer_jobs` (tenant_id, message_id, verdict, iocs)
- `audit_log` (tenant_id, actor, action, target)
- `siem_events` (tenant_id, event_type, payload)

## Threats and mitigations (STRIDE)

| Threat | Example | Mitigation |
| --- | --- | --- |
| Spoofing | Forged sender domain | SPF/DKIM/DMARC enforcement, MTA-STS, TLS-RPT |
| Tampering | URL rewriting abuse | Canonicalization, safe-link signing, HMAC validation |
| Repudiation | Admin denies action | Immutable audit log, WORM option |
| Information Disclosure | Stored email content | Encrypt at rest (KMS per tenant), minimize PII |
| Denial of Service | SMTP floods | Rate limiting, backpressure, queueing |
| Elevation of Privilege | Over-privileged admin | RBAC, least privilege, MFA, break-glass account |
