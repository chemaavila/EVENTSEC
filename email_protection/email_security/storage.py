import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from email_security.models import (
    AnalyzerSubmit,
    AnalyzerVerdict,
    ConnectorCreate,
    ConnectorRecord,
    DomainCreate,
    DomainRecord,
    IngestMessage,
    PolicyCreate,
    PolicyRecord,
    QuarantineRecord,
    SiemEvent,
    TenantCreate,
    TenantRecord,
)

DB_PATH = os.getenv("EMAIL_PROTECT_DB_PATH") or os.getenv("TOKEN_DB_PATH", "tokens.db")


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def init_email_security_db() -> None:
    conn = db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ep_tenants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            feature_flags_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ep_domains (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            domain TEXT NOT NULL,
            verified INTEGER NOT NULL,
            verification_token TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ep_connectors (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            connector_type TEXT NOT NULL,
            config_json TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ep_policies (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            direction TEXT NOT NULL,
            enabled INTEGER NOT NULL,
            conditions_json TEXT NOT NULL,
            actions_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ep_messages (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            direction TEXT NOT NULL,
            sender TEXT NOT NULL,
            recipients_json TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT,
            received_at TEXT NOT NULL,
            verdict TEXT NOT NULL,
            score INTEGER NOT NULL,
            actions_json TEXT NOT NULL,
            metadata_json TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ep_quarantine (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            message_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL,
            stored_at TEXT NOT NULL,
            released_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ep_siem_events (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            message_id TEXT,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ep_audit_log (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            target TEXT,
            metadata_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ep_analyzer_jobs (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            message_id TEXT NOT NULL,
            sample_type TEXT NOT NULL,
            sample_ref TEXT NOT NULL,
            status TEXT NOT NULL,
            verdict TEXT,
            iocs_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ep_queue (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            message_id TEXT NOT NULL,
            status TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ep_identity_provider (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            issuer TEXT NOT NULL,
            client_id TEXT NOT NULL,
            metadata_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def create_tenant(payload: TenantCreate) -> TenantRecord:
    tenant_id = str(uuid.uuid4())
    now = _utcnow()
    conn = db()
    conn.execute(
        "INSERT INTO ep_tenants(id, name, status, feature_flags_json, created_at) VALUES (?,?,?,?,?)",
        (tenant_id, payload.name, "active", json.dumps(payload.feature_flags), now.isoformat()),
    )
    conn.commit()
    conn.close()
    return TenantRecord(
        id=tenant_id,
        name=payload.name,
        status="active",
        feature_flags=payload.feature_flags,
        created_at=now,
    )


def list_tenants() -> List[TenantRecord]:
    conn = db()
    rows = conn.execute("SELECT * FROM ep_tenants ORDER BY created_at DESC").fetchall()
    conn.close()
    return [
        TenantRecord(
            id=row["id"],
            name=row["name"],
            status=row["status"],
            feature_flags=json.loads(row["feature_flags_json"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]


def get_tenant(tenant_id: str) -> Optional[TenantRecord]:
    conn = db()
    row = conn.execute("SELECT * FROM ep_tenants WHERE id = ?", (tenant_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return TenantRecord(
        id=row["id"],
        name=row["name"],
        status=row["status"],
        feature_flags=json.loads(row["feature_flags_json"]),
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def create_domain(payload: DomainCreate) -> DomainRecord:
    domain_id = str(uuid.uuid4())
    token = uuid.uuid4().hex
    now = _utcnow()
    conn = db()
    conn.execute(
        """
        INSERT INTO ep_domains(id, tenant_id, domain, verified, verification_token, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?)
        """,
        (domain_id, payload.tenant_id, payload.domain, 0, token, now.isoformat(), now.isoformat()),
    )
    conn.commit()
    conn.close()
    return DomainRecord(
        id=domain_id,
        tenant_id=payload.tenant_id,
        domain=payload.domain,
        verified=False,
        verification_token=token,
        created_at=now,
        updated_at=now,
    )


def verify_domain(domain_id: str, token: str) -> Optional[DomainRecord]:
    conn = db()
    row = conn.execute("SELECT * FROM ep_domains WHERE id = ?", (domain_id,)).fetchone()
    if not row:
        conn.close()
        return None
    if row["verification_token"] != token:
        conn.close()
        return None
    now = _utcnow().isoformat()
    conn.execute(
        "UPDATE ep_domains SET verified = 1, updated_at = ? WHERE id = ?",
        (now, domain_id),
    )
    conn.commit()
    conn.close()
    return DomainRecord(
        id=row["id"],
        tenant_id=row["tenant_id"],
        domain=row["domain"],
        verified=True,
        verification_token=row["verification_token"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(now),
    )


def list_domains(tenant_id: str) -> List[DomainRecord]:
    conn = db()
    rows = conn.execute(
        "SELECT * FROM ep_domains WHERE tenant_id = ? ORDER BY created_at DESC", (tenant_id,)
    ).fetchall()
    conn.close()
    return [
        DomainRecord(
            id=row["id"],
            tenant_id=row["tenant_id"],
            domain=row["domain"],
            verified=bool(row["verified"]),
            verification_token=row["verification_token"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
        for row in rows
    ]


def create_policy(payload: PolicyCreate) -> PolicyRecord:
    policy_id = str(uuid.uuid4())
    now = _utcnow()
    conn = db()
    conn.execute(
        """
        INSERT INTO ep_policies(
            id, tenant_id, name, direction, enabled, conditions_json, actions_json, created_at, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (
            policy_id,
            payload.tenant_id,
            payload.name,
            payload.direction,
            1 if payload.enabled else 0,
            json.dumps([c.model_dump() for c in payload.conditions]),
            json.dumps([a.model_dump() for a in payload.actions]),
            now.isoformat(),
            now.isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    return PolicyRecord(
        id=policy_id,
        tenant_id=payload.tenant_id,
        name=payload.name,
        direction=payload.direction,
        enabled=payload.enabled,
        conditions=payload.conditions,
        actions=payload.actions,
        created_at=now,
        updated_at=now,
    )


def list_policies(tenant_id: str, direction: Optional[str] = None) -> List[PolicyRecord]:
    conn = db()
    params: List[Any] = [tenant_id]
    where = "tenant_id = ?"
    if direction:
        where += " AND direction = ?"
        params.append(direction)
    rows = conn.execute(
        f"SELECT * FROM ep_policies WHERE {where} ORDER BY created_at DESC", params
    ).fetchall()
    conn.close()
    records: List[PolicyRecord] = []
    for row in rows:
        records.append(
            PolicyRecord(
                id=row["id"],
                tenant_id=row["tenant_id"],
                name=row["name"],
                direction=row["direction"],
                enabled=bool(row["enabled"]),
                conditions=[c for c in json.loads(row["conditions_json"])],
                actions=[a for a in json.loads(row["actions_json"])],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
        )
    return records


def create_connector(payload: ConnectorCreate) -> ConnectorRecord:
    connector_id = str(uuid.uuid4())
    now = _utcnow()
    conn = db()
    conn.execute(
        """
        INSERT INTO ep_connectors(
            id, tenant_id, connector_type, config_json, status, created_at, updated_at
        ) VALUES (?,?,?,?,?,?,?)
        """,
        (
            connector_id,
            payload.tenant_id,
            payload.connector_type,
            json.dumps(payload.config),
            "configured",
            now.isoformat(),
            now.isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    return ConnectorRecord(
        id=connector_id,
        tenant_id=payload.tenant_id,
        connector_type=payload.connector_type,
        config=payload.config,
        status="configured",
        created_at=now,
        updated_at=now,
    )


def list_connectors(tenant_id: str) -> List[ConnectorRecord]:
    conn = db()
    rows = conn.execute(
        "SELECT * FROM ep_connectors WHERE tenant_id = ? ORDER BY created_at DESC", (tenant_id,)
    ).fetchall()
    conn.close()
    return [
        ConnectorRecord(
            id=row["id"],
            tenant_id=row["tenant_id"],
            connector_type=row["connector_type"],
            config=json.loads(row["config_json"]),
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
        for row in rows
    ]


def record_message(message: IngestMessage, verdict: str, score: int, actions: Iterable[Dict[str, Any]]) -> str:
    message_id = str(uuid.uuid4())
    now = _utcnow().isoformat()
    conn = db()
    conn.execute(
        """
        INSERT INTO ep_messages(
            id, tenant_id, direction, sender, recipients_json, subject, body, received_at,
            verdict, score, actions_json, metadata_json
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            message_id,
            message.tenant_id,
            message.direction,
            message.sender,
            json.dumps(message.recipients),
            message.subject,
            message.body,
            now,
            verdict,
            score,
            json.dumps(list(actions)),
            json.dumps(message.metadata),
        ),
    )
    conn.commit()
    conn.close()
    return message_id


def create_quarantine(tenant_id: str, message_id: str, reason: str) -> QuarantineRecord:
    quarantine_id = str(uuid.uuid4())
    now = _utcnow()
    conn = db()
    conn.execute(
        """
        INSERT INTO ep_quarantine(id, tenant_id, message_id, reason, status, stored_at, released_at)
        VALUES (?,?,?,?,?,?,?)
        """,
        (quarantine_id, tenant_id, message_id, reason, "quarantined", now.isoformat(), None),
    )
    conn.commit()
    conn.close()
    return QuarantineRecord(
        id=quarantine_id,
        tenant_id=tenant_id,
        message_id=message_id,
        reason=reason,
        status="quarantined",
        stored_at=now,
        released_at=None,
    )


def list_quarantine(tenant_id: str) -> List[QuarantineRecord]:
    conn = db()
    rows = conn.execute(
        "SELECT * FROM ep_quarantine WHERE tenant_id = ? ORDER BY stored_at DESC", (tenant_id,)
    ).fetchall()
    conn.close()
    records: List[QuarantineRecord] = []
    for row in rows:
        records.append(
            QuarantineRecord(
                id=row["id"],
                tenant_id=row["tenant_id"],
                message_id=row["message_id"],
                reason=row["reason"],
                status=row["status"],
                stored_at=datetime.fromisoformat(row["stored_at"]),
                released_at=datetime.fromisoformat(row["released_at"]) if row["released_at"] else None,
            )
        )
    return records


def release_quarantine(quarantine_id: str) -> Optional[QuarantineRecord]:
    conn = db()
    row = conn.execute("SELECT * FROM ep_quarantine WHERE id = ?", (quarantine_id,)).fetchone()
    if not row:
        conn.close()
        return None
    now = _utcnow().isoformat()
    conn.execute(
        "UPDATE ep_quarantine SET status = ?, released_at = ? WHERE id = ?",
        ("released", now, quarantine_id),
    )
    conn.commit()
    conn.close()
    return QuarantineRecord(
        id=row["id"],
        tenant_id=row["tenant_id"],
        message_id=row["message_id"],
        reason=row["reason"],
        status="released",
        stored_at=datetime.fromisoformat(row["stored_at"]),
        released_at=datetime.fromisoformat(now),
    )


def record_siem_event(
    tenant_id: str, event_type: str, message_id: Optional[str], payload: Dict[str, Any]
) -> SiemEvent:
    event_id = str(uuid.uuid4())
    now = _utcnow()
    conn = db()
    conn.execute(
        """
        INSERT INTO ep_siem_events(id, tenant_id, event_type, message_id, payload_json, created_at)
        VALUES (?,?,?,?,?,?)
        """,
        (event_id, tenant_id, event_type, message_id, json.dumps(payload), now.isoformat()),
    )
    conn.commit()
    conn.close()
    return SiemEvent(
        id=event_id,
        tenant_id=tenant_id,
        event_type=event_type,
        message_id=message_id,
        payload=payload,
        created_at=now,
    )


def list_siem_events(tenant_id: str, limit: int = 100) -> List[SiemEvent]:
    conn = db()
    rows = conn.execute(
        """
        SELECT * FROM ep_siem_events
        WHERE tenant_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (tenant_id, limit),
    ).fetchall()
    conn.close()
    return [
        SiemEvent(
            id=row["id"],
            tenant_id=row["tenant_id"],
            event_type=row["event_type"],
            message_id=row["message_id"],
            payload=json.loads(row["payload_json"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]


def record_audit(tenant_id: str, actor: str, action: str, target: str, metadata: Dict[str, Any]) -> None:
    conn = db()
    conn.execute(
        "INSERT INTO ep_audit_log(id, tenant_id, actor, action, target, metadata_json, created_at)"
        " VALUES (?,?,?,?,?,?,?)",
        (
            str(uuid.uuid4()),
            tenant_id,
            actor,
            action,
            target,
            json.dumps(metadata),
            _utcnow().isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def report_summary(tenant_id: str) -> Dict[str, Any]:
    conn = db()
    total = conn.execute(
        "SELECT COUNT(1) AS total FROM ep_messages WHERE tenant_id = ?", (tenant_id,)
    ).fetchone()["total"]
    quarantined = conn.execute(
        "SELECT COUNT(1) AS total FROM ep_quarantine WHERE tenant_id = ? AND status = 'quarantined'",
        (tenant_id,),
    ).fetchone()["total"]
    blocked = conn.execute(
        "SELECT COUNT(1) AS total FROM ep_messages WHERE tenant_id = ? AND verdict = 'blocked'",
        (tenant_id,),
    ).fetchone()["total"]
    conn.close()
    return {
        "tenant_id": tenant_id,
        "total_messages": total,
        "quarantined": quarantined,
        "blocked": blocked,
    }


def create_analyzer_job(payload: AnalyzerSubmit) -> str:
    job_id = str(uuid.uuid4())
    now = _utcnow()
    conn = db()
    conn.execute(
        """
        INSERT INTO ep_analyzer_jobs(
            id, tenant_id, message_id, sample_type, sample_ref, status, verdict, iocs_json,
            created_at, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (
            job_id,
            payload.tenant_id,
            payload.message_id,
            payload.sample_type,
            payload.sample_ref,
            "submitted",
            None,
            json.dumps([]),
            now.isoformat(),
            now.isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    return job_id


def update_analyzer_job(payload: AnalyzerVerdict) -> Optional[str]:
    conn = db()
    row = conn.execute(
        "SELECT id FROM ep_analyzer_jobs WHERE id = ? AND tenant_id = ?",
        (payload.job_id, payload.tenant_id),
    ).fetchone()
    if not row:
        conn.close()
        return None
    now = _utcnow().isoformat()
    conn.execute(
        """
        UPDATE ep_analyzer_jobs
        SET status = ?, verdict = ?, iocs_json = ?, updated_at = ?
        WHERE id = ?
        """,
        ("completed", payload.verdict, json.dumps(payload.iocs), now, payload.job_id),
    )
    conn.commit()
    conn.close()
    return payload.job_id


def enqueue_message(tenant_id: str, message_id: str, payload: Dict[str, Any]) -> str:
    queue_id = str(uuid.uuid4())
    now = _utcnow().isoformat()
    conn = db()
    conn.execute(
        """
        INSERT INTO ep_queue(id, tenant_id, message_id, status, payload_json, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?)
        """,
        (queue_id, tenant_id, message_id, "pending", json.dumps(payload), now, now),
    )
    conn.commit()
    conn.close()
    return queue_id


def fetch_pending_queue(limit: int = 10) -> List[Dict[str, Any]]:
    conn = db()
    rows = conn.execute(
        "SELECT * FROM ep_queue WHERE status = 'pending' ORDER BY created_at ASC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_queue_status(queue_id: str, status: str) -> None:
    conn = db()
    conn.execute(
        "UPDATE ep_queue SET status = ?, updated_at = ? WHERE id = ?",
        (status, _utcnow().isoformat(), queue_id),
    )
    conn.commit()
    conn.close()


def upsert_identity_provider(tenant_id: str, issuer: str, client_id: str, metadata: Dict[str, Any]) -> None:
    provider_id = str(uuid.uuid4())
    now = _utcnow().isoformat()
    conn = db()
    existing = conn.execute(
        "SELECT id FROM ep_identity_provider WHERE tenant_id = ?", (tenant_id,)
    ).fetchone()
    if existing:
        conn.execute(
            """
            UPDATE ep_identity_provider
            SET issuer = ?, client_id = ?, metadata_json = ?, updated_at = ?
            WHERE tenant_id = ?
            """,
            (issuer, client_id, json.dumps(metadata), now, tenant_id),
        )
    else:
        conn.execute(
            """
            INSERT INTO ep_identity_provider(id, tenant_id, issuer, client_id, metadata_json, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?)
            """,
            (provider_id, tenant_id, issuer, client_id, json.dumps(metadata), now, now),
        )
    conn.commit()
    conn.close()


def get_identity_provider(tenant_id: str) -> Optional[Dict[str, Any]]:
    conn = db()
    row = conn.execute(
        "SELECT * FROM ep_identity_provider WHERE tenant_id = ?", (tenant_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "tenant_id": row["tenant_id"],
        "issuer": row["issuer"],
        "client_id": row["client_id"],
        "metadata": json.loads(row["metadata_json"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
