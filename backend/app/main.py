from __future__ import annotations

import os
import secrets
import asyncio
import contextlib
import logging
import json
from pathlib import Path
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import random
from fastapi import Body, Depends, FastAPI, Header, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import exc as sqlalchemy_exc
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_current_admin_user,
    get_current_user,
    get_optional_user,
    get_password_hash,
    verify_password,
)
from .routers import (
    siem_router,
    edr_router,
    agents_router,
    events_router,
    rules_router,
    inventory_router,
    vulnerabilities_router,
    sca_router,
    kql_router,
    threatmap_router,
)
from . import search
from .metrics import (
    EVENT_INDEX_ERRORS,
    EVENT_QUEUE_SIZE,
    INGEST_TO_INDEX_SECONDS,
    RULE_ALERT_CREATED_TOTAL,
    RULE_MATCH_TOTAL,
    RULE_RUN_TOTAL,
    RULE_TO_ALERT_SECONDS,
)
from .config import settings
from fastapi import Response

from .schemas import (
    ActionLog,
    Alert,
    AlertCreate,
    AlertEscalation,
    AlertEscalationCreate,
    AlertUpdate,
    AnalyticsRule,
    AnalyticsRuleCreate,
    AnalyticsRuleUpdate,
    AnalyticRule,
    CorrelationRule,
    BiocRule,
    BiocRuleCreate,
    BiocRuleUpdate,
    Endpoint,
    EndpointAction,
    EndpointActionCreate,
    EndpointActionResult,
    Handover,
    HandoverCreate,
    HandoverUpdate,
    Indicator,
    IndicatorCreate,
    IndicatorUpdate,
    LoginRequest,
    LoginResponse,
    NetworkEvent,
    NetworkEventCreate,
    SandboxAnalysisRequest,
    SandboxAnalysisResult,
    UserCreate,
    UserProfile,
    UserUpdate,
    WarRoomNote,
    WarRoomNoteCreate,
    WorkGroup,
    WorkGroupCreate,
    Workplan,
    WorkplanCreate,
    WorkplanFlow,
    WorkplanFlowUpdate,
    WorkplanItem,
    WorkplanItemCreate,
    WorkplanItemUpdate,
    WorkplanUpdate,
    RuleImportPayload,
    RuleToggleUpdate,
    YaraMatch,
    YaraRule,
)
from .data.yara_rules import YARA_RULES
from .database import SessionLocal, get_db
from . import crud, models
from .notifications import (
    NotificationService,
    build_alert_url,
    resolve_level_recipients,
    resolve_manager_recipients,
    resolve_user_email,
)

app = FastAPI(title="EventSec Enterprise")
instrumentator = Instrumentator().instrument(app).expose(app, include_in_schema=False)
notification_service = NotificationService()

EVENT_QUEUE_MAXSIZE = int(os.getenv("EVENT_QUEUE_MAXSIZE", "2000"))

app.include_router(siem_router.router)
app.include_router(edr_router.router)
app.include_router(agents_router.router)
app.include_router(events_router.router)
app.include_router(rules_router.router)
app.include_router(inventory_router.router)
app.include_router(vulnerabilities_router.router)
app.include_router(sca_router.router)
app.include_router(kql_router.router)
app.include_router(threatmap_router.router)

logger = logging.getLogger("eventsec")
logger.setLevel(logging.INFO)

# CORS para permitir el frontend en localhost:5173/5174/5175, etc.
origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

yara_rules_cache: List[YaraRule] = [YaraRule(**rule) for rule in YARA_RULES]
_AGENT_SHARED_TOKEN = secrets.token_urlsafe(32)


def get_agent_shared_token() -> str:
    """
    Shared token for agent-to-backend calls (legacy/bootstrap).

    NOTE: Read dynamically (not at import time) so test monkeypatching and
    runtime env injection behave as expected.
    """
    return os.getenv("EVENTSEC_AGENT_TOKEN") or _AGENT_SHARED_TOKEN


def is_agent_request(agent_token: Optional[str]) -> bool:
    if settings.environment.lower() == "production":
        return False
    shared = get_agent_shared_token()
    return bool(agent_token and secrets.compare_digest(agent_token, shared))


def ensure_user_or_agent(
    current_user: Optional[UserProfile],
    agent_token: Optional[str],
) -> Optional[UserProfile]:
    if current_user:
        return current_user
    if agent_token and settings.environment.lower() == "production":
        raise HTTPException(
            status_code=401,
            detail="Shared agent token authentication is disabled in production.",
        )
    if is_agent_request(agent_token):
        return None
    raise HTTPException(
        status_code=401,
        detail="Invalid authentication credentials",
    )


async def require_agent_auth(
    request: Request,
    current_user: Optional[UserProfile] = Depends(get_optional_user),
    agent_token: Optional[str] = Header(None, alias="X-Agent-Token"),
    agent_key: Optional[str] = Header(None, alias="X-Agent-Key"),
    db: Session = Depends(get_db),
) -> Optional[models.Agent]:
    """
    FastAPI dependency for agent endpoints.

    Accepts authentication via:
    1. User JWT (for UI access) - returns None if authenticated as user
    2. X-Agent-Token header (shared token) - returns None if valid
    3. X-Agent-Key header (per-agent API key) - returns Agent model if valid

    Raises 401 if none of the above are valid.
    """
    # Option 1: User JWT authentication (UI access)
    if current_user:
        return None  # User authenticated, allow access

    # Option 2: Shared agent token (X-Agent-Token)
    if agent_token and settings.environment.lower() == "production":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Shared agent token authentication is disabled in production.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if agent_token and is_agent_request(agent_token):
        return None  # Shared token valid, allow access

    # Option 3: Per-agent API key (X-Agent-Key)
    if agent_key:
        agent = crud.get_agent_by_api_key(db, agent_key)
        if agent:
            return agent  # Per-agent key valid, return agent for context

    # No valid authentication found
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials. Provide either user JWT, X-Agent-Token, or X-Agent-Key header.",
        headers={"WWW-Authenticate": "Bearer"},
    )



async def process_event_queue(queue: asyncio.Queue) -> None:
    while True:
        event_id = await queue.get()
        EVENT_QUEUE_SIZE.set(queue.qsize())
        try:
            with SessionLocal() as db:
                event = db.get(models.Event, event_id)
                if not event:
                    continue
                rules = crud.list_detection_rules(db)
                logger.info(
                    "Evaluating event %s against %d detection rules",
                    event.id,
                    len(rules),
                )
                details = event.details or {}
                if not isinstance(details, dict):
                    details = {"raw": details}
                correlation_id = details.get("correlation_id")
                source_label = details.get("source") or event.category or event.event_type
                doc = {
                    "event_id": event.id,
                    "agent_id": event.agent_id,
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "category": event.category,
                    "source": source_label,
                    "details": details,
                    "message": details.get("message"),
                    "correlation_id": correlation_id,
                    "raw_ref": details.get("raw_ref"),
                    "timestamp": event.created_at.isoformat(),
                    "received_time": details.get("received_time"),
                }
                try:
                    search.index_event(doc)
                    if event.created_at:
                        delta = datetime.now(timezone.utc) - event.created_at
                        INGEST_TO_INDEX_SECONDS.observe(delta.total_seconds())
                except Exception as exc:  # noqa: BLE001
                    EVENT_INDEX_ERRORS.labels(source=source_label).inc()
                    logger.error("Failed to index event %s: %s", event.id, exc)
                for rule in rules:
                    RULE_RUN_TOTAL.labels(rule_id=str(rule.id)).inc()
                    if _rule_matches_event(rule.conditions or {}, event, details):
                        RULE_MATCH_TOTAL.labels(rule_id=str(rule.id)).inc()
                        rule_match_time = datetime.now(timezone.utc)
                        alert = models.Alert(
                            title=rule.name,
                            description=rule.description or "Detection rule match",
                            source="DetectionRule",
                            category=event.category or "event",
                            severity=rule.severity,
                            status="open",
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc),
                            username=details.get("username"),
                            hostname=details.get("hostname"),
                        )
                        alert = crud.create_alert(db, alert)
                        RULE_ALERT_CREATED_TOTAL.labels(rule_id=str(rule.id)).inc()
                        RULE_TO_ALERT_SECONDS.observe(
                            (datetime.now(timezone.utc) - rule_match_time).total_seconds()
                        )
                        try:
                            search.index_alert(
                                {
                                    "alert_id": alert.id,
                                    "title": alert.title,
                                    "severity": alert.severity,
                                    "status": alert.status,
                                    "category": alert.category,
                                    "timestamp": alert.created_at.isoformat(),
                                    "correlation_id": correlation_id,
                                    "details": alert.model_dump(),
                                }
                            )
                        except Exception as exc:  # noqa: BLE001
                            logger.error(
                                "Failed to index alert %s: %s", alert.id, exc
                            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error processing event %s: %s", event_id, exc)
        finally:
            queue.task_done()
            EVENT_QUEUE_SIZE.set(queue.qsize())


def _value_matches(expected: object, actual: object) -> bool:
    if isinstance(expected, list):
        return actual in expected
    return actual == expected


def _rule_matches_event(
    conditions: dict, event: models.Event, details: dict
) -> bool:
    for key, expected in conditions.items():
        if key.startswith("details."):
            detail_key = key.split(".", 1)[1]
            actual = details.get(detail_key)
        elif hasattr(event, key):
            actual = getattr(event, key)
        else:
            actual = details.get(key)
        if not _value_matches(expected, actual):
            return False
    return True


def _seed_detection_rules() -> None:
    seed_path = Path(__file__).parent / "data" / "detection_rules.json"
    if not seed_path.exists():
        logger.info("No detection rule seed file found at %s", seed_path)
        return
    with SessionLocal() as db:
        try:
            existing = crud.list_detection_rules(db)
        except (sqlalchemy_exc.ProgrammingError, sqlalchemy_exc.OperationalError) as exc:
            logger.warning(
                "Detection rules table not ready yet; skipping seed: %s", exc
            )
            return
        if existing:
            return
        try:
            payload = json.loads(seed_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            logger.warning("Failed to load detection rule seed file: %s", exc)
            return
        for rule_data in payload:
            rule = models.DetectionRule(
                name=rule_data["name"],
                description=rule_data.get("description"),
                severity=rule_data.get("severity", "medium"),
                enabled=rule_data.get("enabled", True),
                conditions=rule_data.get("conditions", {}),
            )
            crud.create_detection_rule(db, rule)


@app.on_event("startup")
async def startup_event() -> None:
    try:
        search.ensure_indices()
        logger.info("OpenSearch indices ready")
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to prepare OpenSearch indices: %s", exc)
    _seed_detection_rules()
    queue: asyncio.Queue = asyncio.Queue(maxsize=EVENT_QUEUE_MAXSIZE)
    app.state.event_queue = queue
    EVENT_QUEUE_SIZE.set(queue.qsize())
    app.state.event_worker = asyncio.create_task(process_event_queue(queue))


@app.on_event("shutdown")
async def shutdown_event() -> None:
    worker: asyncio.Task | None = getattr(app.state, "event_worker", None)
    if worker:
        worker.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await worker


@app.get("/", tags=["health"])
def health() -> dict:
    return {"status": "ok", "service": "eventsec-backend"}


@app.get("/metrics", tags=["metrics"])
def metrics() -> Response:
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


# --- Authentication ---


@app.post("/auth/login", response_model=LoginResponse, tags=["auth"])
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """Login endpoint."""
    # Find user by email
    user = crud.get_user_by_email(db, payload.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    hashed_password = user.hashed_password
    if not hashed_password or not verify_password(payload.password, hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(data={"sub": user.id})
    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        samesite="lax",
        secure=settings.server_https_enabled,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return LoginResponse(access_token=access_token, user=user)


@app.post("/auth/logout", tags=["auth"])
def logout(response: Response) -> dict:
    response.delete_cookie("access_token")
    return {"detail": "Logged out"}


# --- User Management ---


@app.get("/me", response_model=UserProfile, tags=["profile"])
def get_profile(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
    return current_user


@app.get("/users", response_model=List[UserProfile], tags=["users"])
def list_users(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[UserProfile]:
    """List all users for collaboration workflows."""
    return crud.list_users(db)


@app.post("/users", response_model=UserProfile, tags=["users"])
def create_user(
    payload: UserCreate,
    current_user: UserProfile = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> UserProfile:
    """Create a new user. Admin only."""
    
    # Check if email already exists
    if crud.get_user_by_email(db, payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = models.User(
        full_name=payload.full_name,
        role=payload.role,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        avatar_url=None,
        timezone=payload.timezone,
        team=payload.team,
        manager=payload.manager,
        computer=payload.computer,
        mobile_phone=payload.mobile_phone,
    )
    user = crud.create_user(db, user)
    if user.email:
        notification_service.emit(
            db,
            event_type="USER_CREATED_ASSIGNED",
            entity_type="user",
            entity_id=user.id,
            recipients=[user.email],
            payload={
                "subject": "Welcome to EventSec",
                "body": f"Your account has been created with role {user.role}.",
                "full_name": user.full_name,
                "role": user.role,
                "team": user.team,
            },
        )
    return user


@app.patch("/users/{user_id}", response_model=UserProfile, tags=["users"])
def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: UserProfile = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> UserProfile:
    """Update a user. Admin only."""
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(user, key, value)
    return crud.update_user(db, user)


# --- Alertas ---


@app.get("/alerts", response_model=List[Alert], tags=["alerts"])
def list_alerts(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Alert]:
    return crud.list_alerts(db)


@app.get("/alerts/{alert_id}", response_model=Alert, tags=["alerts"])
def get_alert(
    alert_id: int,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Alert:
    alert = crud.get_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


def resolve_alert_level(alert: models.Alert) -> int:
    if alert.severity in {"high", "critical"}:
        return 2
    return 1


@app.post("/alerts", response_model=Alert, tags=["alerts"])
def create_alert(
    payload: AlertCreate,
    current_user: Optional[UserProfile] = Depends(get_optional_user),
    agent_token: Optional[str] = Header(None, alias="X-Agent-Token"),
    db: Session = Depends(get_db),
) -> Alert:
    """Create a new alert."""
    ensure_user_or_agent(current_user, agent_token)
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")
    if not payload.source or not payload.source.strip():
        raise HTTPException(status_code=400, detail="Source is required")
    now = datetime.now(timezone.utc)
    alert = models.Alert(
        status="open",
        created_at=now,
        updated_at=now,
        **payload.model_dump(),
    )
    alert = crud.create_alert(db, alert)
    try:
        search.index_alert(
            {
                "alert_id": alert.id,
                "title": alert.title,
                "severity": alert.severity,
                "status": alert.status,
                "category": alert.category,
                "timestamp": alert.created_at.isoformat(),
                "details": alert.model_dump(),
            }
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to index alert %s: %s", alert.id, exc)
    level = resolve_alert_level(alert)
    recipients = resolve_manager_recipients(db) + resolve_level_recipients(db, level)
    notification_service.emit(
        db,
        event_type="ALERT_CREATED",
        entity_type="alert",
        entity_id=alert.id,
        recipients=recipients,
        payload={
            "subject": f"New alert #{alert.id}: {alert.title}",
            "body": f"Alert created with severity {alert.severity}.",
            "title": alert.title,
            "severity": alert.severity,
            "status": alert.status,
            "level": level,
            "owner_id": alert.owner_id,
            "alert_url": build_alert_url(alert.id),
        },
    )
    return alert


@app.patch("/alerts/{alert_id}", response_model=Alert, tags=["alerts"])
def update_alert(
    alert_id: int,
    payload: AlertUpdate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Alert:
    """Update alert (status, assignment, conclusion)."""
    alert = crud.get_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    previous_status = alert.status
    previous_assigned = alert.assigned_to
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(alert, key, value)
    alert.updated_at = datetime.now(timezone.utc)
    updated_alert = crud.update_alert(db, alert)

    # Auto-create a workplan linked to this alert when assigned and none exists
    if updates.get("assigned_to") and not crud.get_workplan_by_alert_id(db, alert_id):
        now = datetime.now(timezone.utc)
        workplan = models.Workplan(
            title=f"Workplan for alert #{alert_id}",
            description=f"Auto-created when assigning alert {alert_id}",
            context_type="alert",
            context_id=alert_id,
            owner_user_id=updates["assigned_to"],
            created_by=current_user.id,
            status="active",
            created_at=now,
            updated_at=now,
        )
        crud.create_workplan(db, workplan)

    if updates:
        managers = resolve_manager_recipients(db)
        owner_email = resolve_user_email(db, updated_alert.assigned_to or updated_alert.owner_id)
        recipients = [email for email in [owner_email, *managers] if email]
        if updates.get("status") == "closed" and previous_status != "closed":
            notification_service.emit(
                db,
                event_type="ALERT_CLOSED",
                entity_type="alert",
                entity_id=updated_alert.id,
                recipients=recipients,
                payload={
                    "subject": f"Alert closed #{updated_alert.id}",
                    "body": "Alert has been closed.",
                    "status": updated_alert.status,
                    "title": updated_alert.title,
                    "owner_id": updated_alert.assigned_to or updated_alert.owner_id,
                    "alert_url": build_alert_url(updated_alert.id),
                },
            )
        else:
            notification_service.emit(
                db,
                event_type="ALERT_UPDATED",
                entity_type="alert",
                entity_id=updated_alert.id,
                recipients=recipients,
                payload={
                    "subject": f"Alert updated #{updated_alert.id}",
                    "body": "Alert fields updated.",
                    "status": updated_alert.status,
                    "title": updated_alert.title,
                    "updated_fields": list(updates.keys()),
                    "owner_id": updated_alert.assigned_to or updated_alert.owner_id,
                    "alert_url": build_alert_url(updated_alert.id),
                },
            )

        if "assigned_to" in updates and updates.get("assigned_to"):
            if updates["assigned_to"] != previous_assigned:
                recipients = [
                    email
                    for email in [
                        resolve_user_email(db, updates["assigned_to"]),
                        resolve_user_email(db, current_user.id),
                        *managers,
                    ]
                    if email
                ]
            notification_service.emit(
                db,
                event_type="ALERT_ESCALATED",
                entity_type="alert",
                entity_id=updated_alert.id,
                recipients=recipients,
                payload={
                    "subject": f"Alert escalated #{updated_alert.id}",
                    "body": "Alert reassigned/escalated.",
                    "escalated_to": updates["assigned_to"],
                    "escalated_by": current_user.id,
                    "alert_url": build_alert_url(updated_alert.id),
                },
            )
        if "assigned_to" in updates and updates.get("assigned_to") is None and previous_assigned:
            actor_email = resolve_user_email(db, current_user.id)
            recipients = [
                email
                for email in [
                    resolve_user_email(db, previous_assigned),
                    actor_email,
                    *managers,
                ]
                if email
            ]
            notification_service.emit(
                db,
                event_type="ALERT_DEESCALATED",
                entity_type="alert",
                entity_id=updated_alert.id,
                recipients=recipients,
                payload={
                    "subject": f"Alert de-escalated #{updated_alert.id}",
                    "body": "Alert assignment removed.",
                    "from_user_id": previous_assigned,
                    "actor_id": current_user.id,
                    "alert_url": build_alert_url(updated_alert.id),
                },
            )

    return updated_alert


def log_action(
    db: Session,
    user_id: int,
    action_type: str,
    target_type: str,
    target_id: int,
    parameters: Dict[str, Any] = None,
) -> models.ActionLog:
    """Helper function to log actions."""
    if parameters is None:
        parameters = {}
    log = models.ActionLog(
        user_id=user_id,
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        parameters=parameters,
        created_at=datetime.now(timezone.utc),
    )
    return crud.create_action_log(db, log)


def update_endpoint_state(db: Session, endpoint_id: int, **changes: Any) -> models.Endpoint:
    endpoint = crud.get_endpoint(db, endpoint_id)
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    for key, value in changes.items():
        setattr(endpoint, key, value)
    return crud.update_endpoint(db, endpoint)


def find_endpoint_by_hostname(db: Session, hostname: str) -> Optional[models.Endpoint]:
    normalized = hostname.lower()
    return crud.get_endpoint_by_hostname(db, normalized)


def ensure_endpoint_registered(
    db: Session,
    hostname: str,
    agent: Optional[models.Agent] = None,
) -> models.Endpoint:
    """
    Ensure an Endpoint record exists for this hostname.

    This is required because action routing uses EndpointAction.endpoint_id
    and the agent polls by hostname. If the hostname is unknown, we register a minimal
    Endpoint using any available Agent metadata.
    """
    normalized_hostname = hostname.lower()
    existing = find_endpoint_by_hostname(db, normalized_hostname)
    if existing:
        return existing

    now = datetime.now(timezone.utc)
    endpoint = models.Endpoint(
        hostname=normalized_hostname,
        display_name=hostname,
        status="monitoring",
        agent_status="connected",
        agent_version=(getattr(agent, "version", None) or "unknown"),
        ip_address=(getattr(agent, "ip_address", None) or "0.0.0.0"),
        owner="Unknown",
        os=(getattr(agent, "os", None) or "Unknown"),
        os_version="Unknown",
        cpu_model="Unknown",
        ram_gb=0,
        disk_gb=0,
        resource_usage={"cpu": 0.0, "memory": 0.0, "disk": 0.0},
        last_seen=now,
        location="Unknown",
        processes=[],
        alerts_open=0,
        tags=[],
    )
    return crud.create_endpoint(db, endpoint)


def create_alert_from_network_event(db: Session, event: models.NetworkEvent) -> models.Alert:
    """Automatically registers an alert for high risk network events."""
    now = datetime.now(timezone.utc)
    alert = models.Alert(
        title=f"Phishing click detected on {event.hostname}",
        description=f"User {event.username} attempted to open {event.url}. Categorised as {event.category}.",
        source="Secure Web Gateway",
        category="Network",
        severity=event.severity,
        status="open",
        url=event.url,
        sender=None,
        username=event.username,
        hostname=event.hostname,
        created_at=now,
        updated_at=now,
    )
    alert = crud.create_alert(db, alert)
    try:
        search.index_alert(
            {
                "alert_id": alert.id,
                "title": alert.title,
                "severity": alert.severity,
                "status": alert.status,
                "category": alert.category,
                "timestamp": alert.created_at.isoformat(),
                "details": alert.model_dump(),
            }
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to index alert %s: %s", alert.id, exc)
    return alert


def pick_yara_matches(limit: int = 3) -> List[YaraMatch]:
    if not yara_rules_cache:
        return []
    sample = random.sample(
        yara_rules_cache,
        k=min(limit, len(yara_rules_cache)),
    )
    return [
        YaraMatch(
            rule_id=rule.id,
            rule_name=rule.name,
            source=rule.source,
            description=rule.description,
            tags=rule.tags,
        )
        for rule in sample
    ]


@app.post("/alerts/{alert_id}/block-url", tags=["alerts", "actions"])
def block_url(
    alert_id: int,
    url: str = Query(..., description="URL to block"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if not crud.get_alert(db, alert_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    if not url or not url.strip():
        raise HTTPException(status_code=400, detail="URL parameter is required")
    log_action(db, current_user.id, "block_url", "alert", alert_id, {"url": url})
    return {"detail": f"URL {url} blocked for alert {alert_id}"}


@app.post("/alerts/{alert_id}/unblock-url", tags=["alerts", "actions"])
def unblock_url(
    alert_id: int,
    url: str = Query(..., description="URL to unblock"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if not crud.get_alert(db, alert_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    if not url or not url.strip():
        raise HTTPException(status_code=400, detail="URL parameter is required")
    log_action(db, current_user.id, "unblock_url", "alert", alert_id, {"url": url})
    return {"detail": f"URL {url} unblocked for alert {alert_id}"}


@app.post("/alerts/{alert_id}/block-sender", tags=["alerts", "actions"])
def block_sender(
    alert_id: int,
    sender: str = Query(..., description="Email sender to block"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if not crud.get_alert(db, alert_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    if not sender or not sender.strip():
        raise HTTPException(status_code=400, detail="Sender parameter is required")
    log_action(db, current_user.id, "block_sender", "alert", alert_id, {"sender": sender})
    return {"detail": f"Sender {sender} blocked for alert {alert_id}"}


@app.post("/alerts/{alert_id}/unblock-sender", tags=["alerts", "actions"])
def unblock_sender(
    alert_id: int,
    sender: str = Query(..., description="Email sender to unblock"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if not crud.get_alert(db, alert_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    if not sender or not sender.strip():
        raise HTTPException(status_code=400, detail="Sender parameter is required")
    log_action(db, current_user.id, "unblock_sender", "alert", alert_id, {"sender": sender})
    return {"detail": f"Sender {sender} unblocked for alert {alert_id}"}


@app.post("/alerts/{alert_id}/revoke-session", tags=["alerts", "actions"])
def revoke_user_session(
    alert_id: int,
    username: str = Query(..., description="Username to revoke session for"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if not crud.get_alert(db, alert_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    if not username or not username.strip():
        raise HTTPException(status_code=400, detail="Username parameter is required")
    log_action(db, current_user.id, "revoke_session", "alert", alert_id, {"username": username})
    return {"detail": f"User session revoked for {username} in alert {alert_id}"}


@app.post("/alerts/{alert_id}/isolate-device", tags=["alerts", "actions"])
def isolate_device(
    alert_id: int,
    hostname: str = Query(..., description="Hostname to isolate"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if not crud.get_alert(db, alert_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    if not hostname or not hostname.strip():
        raise HTTPException(status_code=400, detail="Hostname parameter is required")
    log_action(db, current_user.id, "isolate_device", "alert", alert_id, {"hostname": hostname})
    return {"detail": f"Device {hostname} isolated for alert {alert_id}"}


@app.delete("/alerts/{alert_id}", tags=["alerts"])
def delete_alert(
    alert_id: int,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Delete an alert."""
    alert = crud.get_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    log_action(db, current_user.id, "delete_alert", "alert", alert_id)
    crud.delete_alert(db, alert)
    return {"detail": f"Alert {alert_id} deleted successfully"}


@app.post(
    "/alerts/{alert_id}/escalate", response_model=AlertEscalation, tags=["alerts"]
)
def escalate_alert(
    alert_id: int,
    payload: AlertEscalationCreate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AlertEscalation:
    """Escalate an alert to another user."""
    if not crud.get_alert(db, alert_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    if not crud.get_user_by_id(db, payload.escalated_to):
        raise HTTPException(status_code=404, detail="Target user not found")
    
    escalation = models.AlertEscalation(
        alert_id=alert_id,
        escalated_to=payload.escalated_to,
        escalated_by=current_user.id,
        reason=payload.reason,
        created_at=datetime.now(timezone.utc),
    )
    escalation = crud.create_alert_escalation(db, escalation)
    log_action(db, current_user.id, "escalate_alert", "alert", alert_id, {"escalated_to": payload.escalated_to})
    recipients = [
        email
        for email in [
            resolve_user_email(db, payload.escalated_to),
            resolve_user_email(db, current_user.id),
            *resolve_manager_recipients(db),
        ]
        if email
    ]
    notification_service.emit(
        db,
        event_type="ALERT_ESCALATED",
        entity_type="alert",
        entity_id=alert_id,
        recipients=recipients,
        payload={
            "subject": f"Alert escalated #{alert_id}",
            "body": "Alert escalated to a new assignee.",
            "escalated_to": payload.escalated_to,
            "escalated_by": current_user.id,
            "reason": payload.reason,
            "alert_url": build_alert_url(alert_id),
        },
    )
    return escalation


# --- Handovers ---


@app.get("/handover", response_model=List[Handover], tags=["handover"])
def list_handovers(
    analyst_user_id: Optional[int] = Query(None),
    created_by: Optional[int] = Query(None),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Handover]:
    return crud.list_handovers(db, analyst_user_id=analyst_user_id, created_by=created_by)


@app.post("/handover", response_model=Handover, tags=["handover"])
def create_handover(
    payload: HandoverCreate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Handover:
    """Create a new handover."""
    if payload.shift_start >= payload.shift_end:
        raise HTTPException(
            status_code=400, detail="Shift end must be after shift start"
        )
    now = datetime.now(timezone.utc)
    analyst_user_id = payload.analyst_user_id or current_user.id
    handover = models.Handover(
        shift_start=payload.shift_start,
        shift_end=payload.shift_end,
        analyst_user_id=analyst_user_id,
        alerts_summary=payload.alerts_summary,
        notes_to_next_shift=payload.notes_to_next_shift,
        links=payload.links,
        created_by=current_user.id,
        created_at=now,
        updated_at=now,
    )
    return crud.create_handover(db, handover)


@app.get("/api/handovers", response_model=List[Handover], tags=["handovers"])
def list_handovers_api(
    analyst_user_id: Optional[int] = Query(None),
    created_by: Optional[int] = Query(None),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Handover]:
    return crud.list_handovers(db, analyst_user_id=analyst_user_id, created_by=created_by)


@app.post("/api/handovers", response_model=Handover, tags=["handovers"])
def create_handover_api(
    payload: HandoverCreate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Handover:
    if payload.shift_start >= payload.shift_end:
        raise HTTPException(
            status_code=400, detail="Shift end must be after shift start"
        )
    now = datetime.now(timezone.utc)
    analyst_user_id = payload.analyst_user_id or current_user.id
    handover = models.Handover(
        shift_start=payload.shift_start,
        shift_end=payload.shift_end,
        analyst_user_id=analyst_user_id,
        alerts_summary=payload.alerts_summary,
        notes_to_next_shift=payload.notes_to_next_shift,
        links=payload.links,
        created_by=current_user.id,
        created_at=now,
        updated_at=now,
    )
    return crud.create_handover(db, handover)


@app.get("/api/handovers/{handover_id}", response_model=Handover, tags=["handovers"])
def get_handover(
    handover_id: int,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Handover:
    handover = crud.get_handover(db, handover_id)
    if not handover:
        raise HTTPException(status_code=404, detail="Handover not found")
    return handover


@app.patch("/api/handovers/{handover_id}", response_model=Handover, tags=["handovers"])
def update_handover(
    handover_id: int,
    payload: HandoverUpdate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Handover:
    handover = crud.get_handover(db, handover_id)
    if not handover:
        raise HTTPException(status_code=404, detail="Handover not found")
    updates = payload.model_dump(exclude_unset=True)
    if "shift_start" in updates and "shift_end" in updates:
        if updates["shift_start"] >= updates["shift_end"]:
            raise HTTPException(
                status_code=400, detail="Shift end must be after shift start"
            )
    for key, value in updates.items():
        setattr(handover, key, value)
    handover.updated_at = datetime.now(timezone.utc)
    return crud.update_handover(db, handover)


# --- Work Groups ---


@app.get("/workgroups", response_model=List[WorkGroup], tags=["workgroups"])
def list_workgroups(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[WorkGroup]:
    return crud.list_workgroups(db)


@app.post("/workgroups", response_model=WorkGroup, tags=["workgroups"])
def create_workgroup(
    payload: WorkGroupCreate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkGroup:
    """Create a work group. Admin or team lead only."""
    if current_user.role not in ["admin", "team_lead"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    workgroup = models.WorkGroup(
        name=payload.name,
        description=payload.description,
        members=payload.members,
        created_at=datetime.now(timezone.utc),
    )
    return crud.create_workgroup(db, workgroup)


# --- Workplans ---


@app.get("/workplans", response_model=List[Workplan], tags=["workplans"])
def list_workplans(
    context_type: Optional[str] = Query(None),
    context_id: Optional[int] = Query(None),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Workplan]:
    return crud.list_workplans(db, context_type=context_type, context_id=context_id)


@app.post("/workplans", response_model=Workplan, tags=["workplans"])
def create_workplan(
    payload: WorkplanCreate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Workplan:
    now = datetime.now(timezone.utc)
    owner_user_id = payload.owner_user_id or current_user.id
    workplan = models.Workplan(
        title=payload.title,
        description=payload.description,
        owner_user_id=owner_user_id,
        priority=payload.priority,
        due_at=payload.due_at,
        context_type=payload.context_type,
        context_id=payload.context_id,
        created_by=current_user.id,
        status="draft",
        created_at=now,
        updated_at=now,
    )
    return crud.create_workplan(db, workplan)


@app.patch("/workplans/{workplan_id}", response_model=Workplan, tags=["workplans"])
def update_workplan_entry(
    workplan_id: int,
    payload: WorkplanUpdate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Workplan:
    workplan = db.get(models.Workplan, workplan_id)
    if not workplan:
        raise HTTPException(status_code=404, detail="Workplan not found")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(workplan, key, value)
    workplan.updated_at = datetime.now(timezone.utc)
    updated = crud.update_workplan(db, workplan)
    log_action(db, current_user.id, "update_workplan", "workplan", workplan_id, updates)
    return updated


@app.get("/api/workplans", response_model=List[Workplan], tags=["workplans"])
def list_workplans_api(
    context_type: Optional[str] = Query(None),
    context_id: Optional[int] = Query(None),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Workplan]:
    return crud.list_workplans(db, context_type=context_type, context_id=context_id)


@app.get("/api/workplans/{workplan_id}", response_model=Workplan, tags=["workplans"])
def get_workplan_api(
    workplan_id: int,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Workplan:
    workplan = db.get(models.Workplan, workplan_id)
    if not workplan:
        raise HTTPException(status_code=404, detail="Workplan not found")
    return workplan


@app.post("/api/workplans", response_model=Workplan, tags=["workplans"])
def create_workplan_api(
    payload: WorkplanCreate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Workplan:
    now = datetime.now(timezone.utc)
    owner_user_id = payload.owner_user_id or current_user.id
    workplan = models.Workplan(
        title=payload.title,
        description=payload.description,
        owner_user_id=owner_user_id,
        priority=payload.priority,
        due_at=payload.due_at,
        context_type=payload.context_type,
        context_id=payload.context_id,
        created_by=current_user.id,
        status="draft",
        created_at=now,
        updated_at=now,
    )
    return crud.create_workplan(db, workplan)


@app.patch("/api/workplans/{workplan_id}", response_model=Workplan, tags=["workplans"])
def update_workplan_api(
    workplan_id: int,
    payload: WorkplanUpdate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Workplan:
    workplan = db.get(models.Workplan, workplan_id)
    if not workplan:
        raise HTTPException(status_code=404, detail="Workplan not found")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(workplan, key, value)
    workplan.updated_at = datetime.now(timezone.utc)
    updated = crud.update_workplan(db, workplan)
    log_action(db, current_user.id, "update_workplan", "workplan", workplan_id, updates)
    return updated


@app.get("/api/workplans/{workplan_id}/items", response_model=List[WorkplanItem], tags=["workplans"])
def list_workplan_items(
    workplan_id: int,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[WorkplanItem]:
    if not db.get(models.Workplan, workplan_id):
        raise HTTPException(status_code=404, detail="Workplan not found")
    return crud.list_workplan_items(db, workplan_id)


@app.post("/api/workplans/{workplan_id}/items", response_model=WorkplanItem, tags=["workplans"])
def create_workplan_item(
    workplan_id: int,
    payload: WorkplanItemCreate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkplanItem:
    if not db.get(models.Workplan, workplan_id):
        raise HTTPException(status_code=404, detail="Workplan not found")
    now = datetime.now(timezone.utc)
    item = models.WorkplanItem(
        workplan_id=workplan_id,
        title=payload.title,
        status=payload.status or "open",
        order_index=payload.order_index or 0,
        assignee_user_id=payload.assignee_user_id,
        due_at=payload.due_at,
        notes=payload.notes,
        created_at=now,
        updated_at=now,
    )
    return crud.create_workplan_item(db, item)


@app.patch("/api/workplans/{workplan_id}/items/{item_id}", response_model=WorkplanItem, tags=["workplans"])
def update_workplan_item(
    workplan_id: int,
    item_id: int,
    payload: WorkplanItemUpdate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkplanItem:
    item = db.get(models.WorkplanItem, item_id)
    if not item or item.workplan_id != workplan_id:
        raise HTTPException(status_code=404, detail="Workplan item not found")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(item, key, value)
    item.updated_at = datetime.now(timezone.utc)
    return crud.update_workplan_item(db, item)


@app.patch("/api/workplans/{workplan_id}/items", response_model=WorkplanItem, tags=["workplans"])
def update_workplan_item_legacy(
    workplan_id: int,
    item_id: int = Query(...),
    payload: WorkplanItemUpdate = Body(...),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkplanItem:
    return update_workplan_item(workplan_id, item_id, payload, current_user, db)


@app.delete("/api/workplans/{workplan_id}/items/{item_id}", tags=["workplans"])
def delete_workplan_item(
    workplan_id: int,
    item_id: int,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    item = db.get(models.WorkplanItem, item_id)
    if not item or item.workplan_id != workplan_id:
        raise HTTPException(status_code=404, detail="Workplan item not found")
    crud.delete_workplan_item(db, item)
    return {"detail": "Deleted"}


@app.delete("/api/workplans/{workplan_id}/items", tags=["workplans"])
def delete_workplan_item_legacy(
    workplan_id: int,
    item_id: int = Query(...),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return delete_workplan_item(workplan_id, item_id, current_user, db)


@app.get("/api/workplans/{workplan_id}/flow", response_model=WorkplanFlow, tags=["workplans"])
def get_workplan_flow(
    workplan_id: int,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkplanFlow:
    flow = crud.get_workplan_flow(db, workplan_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    return flow


@app.put("/api/workplans/{workplan_id}/flow", response_model=WorkplanFlow, tags=["workplans"])
def update_workplan_flow(
    workplan_id: int,
    payload: WorkplanFlowUpdate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkplanFlow:
    if not db.get(models.Workplan, workplan_id):
        raise HTTPException(status_code=404, detail="Workplan not found")
    if not isinstance(payload.nodes, list) or not isinstance(payload.edges, list):
        raise HTTPException(status_code=400, detail="Nodes and edges must be arrays")
    if len(payload.nodes) > 200 or len(payload.edges) > 400:
        raise HTTPException(status_code=400, detail="Flow size exceeds limits")
    now = datetime.now(timezone.utc)
    existing = crud.get_workplan_flow(db, workplan_id)
    if existing:
        existing.format = payload.format
        existing.nodes = payload.nodes
        existing.edges = payload.edges
        existing.viewport = payload.viewport
        existing.updated_at = now
        return crud.upsert_workplan_flow(db, existing)
    flow = models.WorkplanFlow(
        workplan_id=workplan_id,
        format=payload.format,
        nodes=payload.nodes,
        edges=payload.edges,
        viewport=payload.viewport,
        updated_at=now,
    )
    return crud.upsert_workplan_flow(db, flow)


# --- Threat Intel (IOC/BIOC/YARA) ---


@app.get("/indicators", response_model=List[Indicator], tags=["intel"])
def list_indicators(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Indicator]:
    return crud.list_indicators(db)


@app.post("/indicators", response_model=Indicator, tags=["intel"])
def create_indicator_entry(
    payload: IndicatorCreate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Indicator:
    now = datetime.now(timezone.utc)
    indicator = models.Indicator(
        created_at=now,
        updated_at=now,
        **payload.model_dump(),
    )
    indicator = crud.create_indicator(db, indicator)
    log_action(db, current_user.id, "create_indicator", "indicator", indicator.id, payload.model_dump())
    return indicator


@app.patch("/indicators/{indicator_id}", response_model=Indicator, tags=["intel"])
def update_indicator_entry(
    indicator_id: int,
    payload: IndicatorUpdate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Indicator:
    indicator = db.get(models.Indicator, indicator_id)
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if value is not None:
            setattr(indicator, key, value)
    indicator.updated_at = datetime.now(timezone.utc)
    updated = crud.update_indicator(db, indicator)
    log_action(db, current_user.id, "update_indicator", "indicator", indicator_id, updates)
    return updated


@app.get("/biocs", response_model=List[BiocRule], tags=["intel"])
def list_bioc_rules(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[BiocRule]:
    return crud.list_bioc_rules(db)


@app.post("/biocs", response_model=BiocRule, tags=["intel"])
def create_bioc_rule(
    payload: BiocRuleCreate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BiocRule:
    now = datetime.now(timezone.utc)
    rule = models.BiocRule(
        created_at=now,
        updated_at=now,
        **payload.model_dump(),
    )
    rule = crud.create_bioc_rule(db, rule)
    log_action(db, current_user.id, "create_bioc", "bioc_rule", rule.id, payload.model_dump())
    return rule


@app.patch("/biocs/{rule_id}", response_model=BiocRule, tags=["intel"])
def update_bioc_rule(
    rule_id: int,
    payload: BiocRuleUpdate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BiocRule:
    rule = db.get(models.BiocRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="BIOC rule not found")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if value is not None:
            setattr(rule, key, value)
    rule.updated_at = datetime.now(timezone.utc)
    updated = crud.update_bioc_rule(db, rule)
    log_action(db, current_user.id, "update_bioc", "bioc_rule", rule_id, updates)
    return updated


@app.get("/analytics/rules", response_model=List[AnalyticsRule], tags=["analytics"])
def list_analytics_rules(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[AnalyticsRule]:
    return crud.list_analytics_rules(db)


@app.get("/analytics/rules/{rule_id}", response_model=AnalyticsRule, tags=["analytics"])
def get_analytics_rule(
    rule_id: int,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalyticsRule:
    rule = db.get(models.AnalyticsRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Analytics rule not found")
    return rule


@app.post("/analytics/rules", response_model=AnalyticsRule, tags=["analytics"])
def create_analytics_rule(
    payload: AnalyticsRuleCreate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalyticsRule:
    now = datetime.now(timezone.utc)
    rule = models.AnalyticsRule(
        created_at=now,
        updated_at=now,
        status="enabled",
        **payload.model_dump(),
    )
    rule = crud.create_analytics_rule(db, rule)
    log_action(db, current_user.id, "create_analytics_rule", "analytics_rule", rule.id, payload.model_dump())
    return rule


@app.patch(
    "/analytics/rules/{rule_id}", response_model=AnalyticsRule, tags=["analytics"]
)
def update_analytics_rule(
    rule_id: int,
    payload: AnalyticsRuleUpdate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalyticsRule:
    rule = db.get(models.AnalyticsRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Analytics rule not found")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if value is not None:
            setattr(rule, key, value)
    rule.updated_at = datetime.now(timezone.utc)
    updated = crud.update_analytics_rule(db, rule)
    log_action(db, current_user.id, "update_analytics_rule", "analytics_rule", rule_id, updates)
    return updated


# --- Rule Library ---


@app.get("/api/rules", response_model=List[AnalyticRule] | List[CorrelationRule], tags=["rules"])
def list_rule_library(
    type: str = Query("analytic", pattern="^(analytic|correlation)$"),
    search: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    enabled: Optional[bool] = Query(None),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[AnalyticRule] | List[CorrelationRule]:
    if type == "correlation":
        return crud.list_correlation_rules(db, search=search, severity=severity, enabled=enabled)
    return crud.list_analytic_rules(db, search=search, severity=severity, enabled=enabled)


@app.get("/api/rules/{rule_id}", response_model=AnalyticRule | CorrelationRule, tags=["rules"])
def get_rule_library_entry(
    rule_id: int,
    type: str = Query("analytic", pattern="^(analytic|correlation)$"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalyticRule | CorrelationRule:
    if type == "correlation":
        rule = crud.get_correlation_rule(db, rule_id)
    else:
        rule = crud.get_analytic_rule(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@app.patch("/api/rules/{rule_id}", response_model=AnalyticRule | CorrelationRule, tags=["rules"])
def toggle_rule_library_entry(
    rule_id: int,
    payload: RuleToggleUpdate,
    type: str = Query("analytic", pattern="^(analytic|correlation)$"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalyticRule | CorrelationRule:
    if type == "correlation":
        rule = crud.get_correlation_rule(db, rule_id)
    else:
        rule = crud.get_analytic_rule(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(rule, key, value)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@app.post("/api/rules/import", tags=["rules"])
def import_rules(
    payload: RuleImportPayload,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    analytics = payload.analytic_rules or []
    correlations = payload.correlation_rules or []
    created = 0
    now = datetime.now(timezone.utc)
    for entry in analytics:
        rule_id = entry.get("id")
        rule = crud.get_analytic_rule(db, rule_id) if rule_id else None
        rule = rule or models.AnalyticRule(created_at=now)
        rule.title = entry.get("title") or entry.get("name") or rule.title or "Untitled"
        rule.description = entry.get("description", "")
        rule.severity = entry.get("severity", "medium")
        rule.category = entry.get("category")
        rule.data_sources = entry.get("data_sources", entry.get("dataSources", []))
        rule.query = entry.get("query", {})
        rule.tags = entry.get("tags", [])
        rule.enabled = bool(entry.get("enabled", True))
        if rule_id:
            rule.id = rule_id
        crud.upsert_analytic_rule(db, rule)
        created += 1
    for entry in correlations:
        rule_id = entry.get("id")
        rule = crud.get_correlation_rule(db, rule_id) if rule_id else None
        rule = rule or models.CorrelationRule(created_at=now)
        rule.title = entry.get("title") or entry.get("name") or rule.title or "Untitled"
        rule.description = entry.get("description", "")
        rule.severity = entry.get("severity", "medium")
        rule.window_minutes = entry.get("window_minutes", entry.get("windowMinutes"))
        rule.logic = entry.get("logic", {})
        rule.tags = entry.get("tags", [])
        rule.enabled = bool(entry.get("enabled", True))
        if rule_id:
            rule.id = rule_id
        crud.upsert_correlation_rule(db, rule)
        created += 1
    return {"detail": "Imported rules", "count": created}


@app.get("/yara/rules", response_model=List[YaraRule], tags=["intel"])
def list_yara_rules(
    current_user: UserProfile = Depends(get_current_user),
) -> List[YaraRule]:
    return yara_rules_cache


# --- Action Logs ---


@app.get("/action-logs", response_model=List[ActionLog], tags=["logs"])
def list_action_logs(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ActionLog]:
    """List action logs. Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return crud.list_action_logs(db)


# --- War Room ---


@app.get("/warroom/notes", response_model=List[WarRoomNote], tags=["warroom"])
def list_warroom_notes(
    alert_id: Optional[int] = None,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[WarRoomNote]:
    return crud.list_warroom_notes(db, alert_id)


@app.post("/warroom/notes", response_model=WarRoomNote, tags=["warroom"])
def create_warroom_note(
    payload: WarRoomNoteCreate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WarRoomNote:
    note = models.WarRoomNote(
        alert_id=payload.alert_id,
        content=payload.content,
        created_by=current_user.id,
        attachments=payload.attachments,
        created_at=datetime.now(timezone.utc),
    )
    return crud.create_warroom_note(db, note)


# --- Sandbox ---


@app.post("/sandbox/analyze", response_model=SandboxAnalysisResult, tags=["sandbox"])
def analyze_sandbox(
    payload: SandboxAnalysisRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SandboxAnalysisResult:
    """
    Lightweight, deterministic sandbox response to avoid false positives.
    - Treat common document types as clean.
    - Flag obviously executable/script formats as malicious.
    - URLs are only flagged if they look phishy (simple keyword heuristics).
    """
    now = datetime.now(timezone.utc)
    hash_value = payload.metadata.get("hash") if payload.metadata else None
    filename = (
        payload.filename or payload.metadata.get("filename")
        if payload.metadata
        else None
    )
    lower_name = (filename or "").lower()

    doc_whitelist_ext = {
        ".pdf",
        ".doc",
        ".docx",
        ".ppt",
        ".pptx",
        ".xls",
        ".xlsx",
        ".txt",
        ".rtf",
        ".odt",
        ".csv",
        ".eml",
    }
    exec_like_ext = {
        ".exe",
        ".dll",
        ".ps1",
        ".vbs",
        ".js",
        ".bat",
        ".scr",
        ".jar",
        ".apk",
        ".iso",
        ".img",
        ".lnk",
        ".cmd",
    }

    # Phishing keywords: action words and urgency triggers
    phishy_action_keywords = {
        "login",
        "verify",
        "update",
        "reset",
        "secure",
        "account",
        "confirm",
        "suspend",
        "locked",
        "expire",
        "urgent",
        "immediately",
        "validate",
        "authenticate",
        "reactivate",
        "restore",
        "unlock",
        "recover",
    }

    # Brand impersonation: legitimate brands commonly spoofed in phishing
    phishy_brand_keywords = {
        # Cloud / Email
        "icloud",
        "apple",
        "appleid",
        "itunes",
        "google",
        "gmail",
        "gdrive",
        "googledrive",
        "microsoft",
        "outlook",
        "office365",
        "microsoft365",
        "onedrive",
        "sharepoint",
        "azure",
        "dropbox",
        "box",
        # Banking / Payment
        "paypal",
        "stripe",
        "venmo",
        "zelle",
        "cashapp",
        "chase",
        "wellsfargo",
        "bankofamerica",
        "citibank",
        "hsbc",
        "barclays",
        "americanexpress",
        "amex",
        "visa",
        "mastercard",
        # Social / Retail
        "facebook",
        "instagram",
        "whatsapp",
        "twitter",
        "linkedin",
        "tiktok",
        "amazon",
        "ebay",
        "netflix",
        "spotify",
        "walmart",
        "target",
        # Crypto
        "coinbase",
        "binance",
        "metamask",
        "blockchain",
        "crypto",
        "wallet",
        # Shipping / Delivery
        "fedex",
        "ups",
        "usps",
        "dhl",
        # Other
        "docusign",
        "adobe",
        "zoom",
        "slack",
        "telegram",
    }

    # Suspicious TLDs often used in phishing
    suspicious_tlds = {
        ".tk",
        ".ml",
        ".ga",
        ".cf",
        ".gq",
        ".xyz",
        ".top",
        ".buzz",
        ".icu",
        ".club",
        ".work",
        ".site",
    }

    def looks_malicious_file() -> bool:
        from pathlib import Path as _Path

        if not lower_name:
            return False
        ext = _Path(lower_name).suffix
        if ext in exec_like_ext:
            return True
        if ext in doc_whitelist_ext:
            return False
        size = payload.metadata.get("size") if payload.metadata else None
        return bool(size is not None and size < 32 * 1024)

    def looks_malicious_url() -> bool:
        import re

        url_value = (payload.value or "").lower().strip()

        # Check for phishy action keywords
        if any(keyword in url_value for keyword in phishy_action_keywords):
            return True

        # Check for brand impersonation (brand name in non-official domain)
        for brand in phishy_brand_keywords:
            if brand in url_value:
                # Check if it's NOT the official domain (e.g., "icloud" but not "icloud.com" or "apple.com")
                official_patterns = [
                    f"{brand}.com",
                    f"{brand}.net",
                    f"{brand}.org",
                    f"www.{brand}.com",
                    f"www.{brand}.net",
                ]
                is_official = any(pattern in url_value for pattern in official_patterns)
                if not is_official:
                    return True

        # Check for suspicious TLDs
        if any(
            url_value.endswith(tld) or f"{tld}/" in url_value for tld in suspicious_tlds
        ):
            return True

        # Check for IP address in URL (often phishing)
        if re.search(r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", url_value):
            return True

        # Check for excessive subdomains (e.g., login.secure.apple.fake-domain.com)
        if url_value.count(".") >= 4:
            return True

        # Check for lookalike patterns with hyphens before/after brand names
        lookalike_pattern = r"(^|[.-])(apple|google|microsoft|paypal|amazon|facebook|icloud|netflix)([.-])"
        if re.search(lookalike_pattern, url_value):
            return True

        return False

    def get_url_threat_type() -> str | None:
        """Return a specific threat type based on what triggered detection."""
        url_value = (payload.value or "").lower().strip()

        for brand in phishy_brand_keywords:
            if brand in url_value:
                return f"Brand impersonation phishing ({brand.upper()})"

        if any(keyword in url_value for keyword in phishy_action_keywords):
            return "Credential harvesting phishing"

        if any(
            url_value.endswith(tld) or f"{tld}/" in url_value for tld in suspicious_tlds
        ):
            return "Suspicious TLD commonly used in phishing"

        return "Suspicious URL"

    if payload.type == "file":
        is_malicious = looks_malicious_file()
        threat_type = "Executable / script file" if is_malicious else None
    else:
        is_malicious = looks_malicious_url()
        threat_type = get_url_threat_type() if is_malicious else None

    if is_malicious:
        vt_results = {
            "malicious": 7,
            "suspicious": 1,
            "clean": 40,
            "undetected": 4,
            "last_analysis_date": now.isoformat(),
        }
        osint_results = {
            "reputation": "High risk",
            "threat_intel": [
                "Associated with ransomware campaigns",
                "Observed in phishing kits",
            ],
            "yara_rules": ["WannaCry_Generic", "Suspicious_Macro_Execution"],
        }
        iocs = [
            {
                "type": "IP Address",
                "value": "142.250.184.238",
                "description": "C2 infrastructure",
            },
            {
                "type": "Domain",
                "value": "iqwerfsdopgjifaposrdfjhosguriJfaewrwer.gwea.com",
                "description": "Kill-switch domain",
            },
            {
                "type": "File Path",
                "value": r"C:\Users\Admin\Desktop\PLEASE_READ_ME.txt",
                "description": "Ransom note dropped",
            },
            {
                "type": "Registry Key",
                "value": r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run\mssecsvc.exe",
                "description": "Persistence mechanism",
            },
        ]
        matched_endpoints = [
            {
                "id": endpoint.id,
                "hostname": endpoint.hostname,
                "status": endpoint.status,
                "ip_address": endpoint.ip_address,
                "last_seen": endpoint.last_seen.isoformat(),
                "location": endpoint.location,
            }
            for endpoint in crud.list_endpoints(db)[:2]
        ]
        yara_matches = pick_yara_matches(2 if payload.type == "file" else 1)
        verdict = "malicious"
    else:
        vt_results = {
            "malicious": 0,
            "suspicious": 0,
            "clean": 50,
            "undetected": 0,
            "last_analysis_date": now.isoformat(),
        }
        osint_results = {
            "reputation": "Clean",
            "threat_intel": [],
            "yara_rules": [],
        }
        iocs = []
        matched_endpoints = []
        yara_matches = []
        verdict = "clean"

    result = models.SandboxResult(
        type=payload.type,
        value=payload.value,
        filename=filename,
        verdict=verdict,
        threat_type=threat_type,
        status="completed",
        progress=100,
        file_hash=hash_value or payload.value,
        iocs=iocs,
        endpoints=matched_endpoints,
        vt_results=vt_results,
        osint_results=osint_results,
        yara_matches=yara_matches,
        created_at=now,
    )
    return crud.create_sandbox_result(db, result)


@app.get("/sandbox/analyses", response_model=List[SandboxAnalysisResult], tags=["sandbox"])
def list_sandbox_analyses(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[SandboxAnalysisResult]:
    return crud.list_sandbox_results(db)


# --- Network telemetry ---


@app.get("/network/events", response_model=List[NetworkEvent], tags=["network"])
def list_network_events_api(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[NetworkEvent]:
    return crud.list_network_events(db)


@app.post("/network/events", response_model=NetworkEvent, tags=["network"])
def create_network_event_api(
    payload: NetworkEventCreate,
    current_user: Optional[UserProfile] = Depends(get_optional_user),
    agent_token: Optional[str] = Header(None, alias="X-Agent-Token"),
    db: Session = Depends(get_db),
) -> NetworkEvent:
    ensure_user_or_agent(current_user, agent_token)
    now = datetime.now(timezone.utc)
    description = payload.description or f"{payload.url} categorised as {payload.category}"
    event = models.NetworkEvent(
        hostname=payload.hostname,
        username=payload.username,
        url=payload.url,
        verdict=payload.verdict,
        category=payload.category,
        description=description,
        severity=payload.severity,
        created_at=now,
    )
    event = crud.create_network_event(db, event)

    if payload.verdict == "malicious":
        new_alert = create_alert_from_network_event(db, event)
        if current_user:
            log_action(db, current_user.id, "network_event_alert", "alert", new_alert.id, {"url": payload.url})
    return event


@app.get("/endpoints", response_model=List[Endpoint], tags=["endpoints"])
def list_endpoints(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Endpoint]:
    return crud.list_endpoints(db)


@app.get("/endpoints/{endpoint_id}", response_model=Endpoint, tags=["endpoints"])
def get_endpoint(
    endpoint_id: int,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Endpoint:
    endpoint = crud.get_endpoint(db, endpoint_id)
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    return endpoint


@app.get(
    "/endpoints/{endpoint_id}/actions",
    response_model=List[EndpointAction],
    tags=["endpoints"],
)
def list_endpoint_actions_api(
    endpoint_id: int,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[EndpointAction]:
    if not crud.get_endpoint(db, endpoint_id):
        raise HTTPException(status_code=404, detail="Endpoint not found")
    return crud.list_endpoint_actions(db, endpoint_id)


@app.post(
    "/endpoints/{endpoint_id}/actions",
    response_model=EndpointAction,
    tags=["endpoints"],
)
def create_endpoint_action(
    endpoint_id: int,
    payload: EndpointActionCreate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EndpointAction:
    endpoint = crud.get_endpoint(db, endpoint_id)
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    correlation_id = str(uuid.uuid4())
    before_state = {
        "status": endpoint.status,
        "agent_status": endpoint.agent_status,
        "last_seen": endpoint.last_seen.isoformat() if endpoint.last_seen else None,
    }
    action = models.EndpointAction(
        endpoint_id=endpoint_id,
        action_type=payload.action_type,
        parameters=payload.parameters,
        status="pending",
        requested_by=current_user.id,
        requested_at=datetime.now(timezone.utc),
    )
    action = crud.create_endpoint_action(db, action)
    log_action(
        db,
        current_user.id,
        f"endpoint_{payload.action_type}",
        "endpoint",
        endpoint_id,
        {
            "parameters": payload.parameters,
            "correlation_id": correlation_id,
            "before_state": before_state,
            "outcome": "requested",
        },
    )
    return action


@app.get("/agent/actions", response_model=List[EndpointAction], tags=["agent"])
def pull_agent_actions(
    hostname: str,
    agent_auth: Optional[models.Agent] = Depends(require_agent_auth),
    db: Session = Depends(get_db),
) -> List[EndpointAction]:
    """
    Get pending actions for an endpoint.

    Authentication: Accepts user JWT, X-Agent-Token (shared), or X-Agent-Key (per-agent).
    """
    endpoint = ensure_endpoint_registered(db, hostname, agent_auth)
    actions = crud.list_endpoint_actions(db, endpoint.id)
    return [action for action in actions if action.status == "pending"]


@app.post(
    "/agent/actions/{action_id}/complete", response_model=EndpointAction, tags=["agent"]
)
def complete_agent_action(
    action_id: int,
    payload: EndpointActionResult,
    agent_auth: Optional[models.Agent] = Depends(require_agent_auth),
    db: Session = Depends(get_db),
) -> EndpointAction:
    """
    Mark an action as completed.

    Authentication: Accepts user JWT, X-Agent-Token (shared), or X-Agent-Key (per-agent).
    """
    action = crud.get_endpoint_action(db, action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    if action.status != "pending":
        return action
    status_value = "completed" if payload.success else "failed"
    action.status = status_value
    action.completed_at = datetime.now(timezone.utc)
    action.output = payload.output
    updated_action = crud.update_endpoint_action(db, action)

    if payload.success:
        if action.action_type == "isolate":
            update_endpoint_state(db, action.endpoint_id, status="isolated", agent_status="isolated")
        elif action.action_type == "release":
            update_endpoint_state(db, action.endpoint_id, status="protected", agent_status="connected")
        elif action.action_type == "reboot":
            update_endpoint_state(
                db,
                action.endpoint_id,
                last_seen=datetime.now(timezone.utc),
                agent_status="rebooting",
            )
        elif action.action_type == "command":
            update_endpoint_state(db, action.endpoint_id, last_seen=datetime.now(timezone.utc))
    endpoint = crud.get_endpoint(db, action.endpoint_id)
    after_state = None
    if endpoint:
        after_state = {
            "status": endpoint.status,
            "agent_status": endpoint.agent_status,
            "last_seen": endpoint.last_seen.isoformat() if endpoint.last_seen else None,
        }
    actor_id = agent_auth.id if agent_auth else None
    log_action(
        db,
        actor_id or 0,
        f"endpoint_{action.action_type}_complete",
        "endpoint",
        action.endpoint_id,
        {
            "correlation_id": str(uuid.uuid4()),
            "outcome": "success" if payload.success else "failed",
            "before_state": None,
            "after_state": after_state,
            "error_code": None if payload.success else "action_failed",
        },
    )
    return updated_action
