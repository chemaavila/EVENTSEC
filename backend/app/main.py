from __future__ import annotations

import os
import secrets
import asyncio
import contextlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import random
from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

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
)
from . import search
from fastapi import Response

from .schemas import (
    ActionLog,
    ActionLogCreate,
    Alert,
    AlertCreate,
    AlertEscalation,
    AlertEscalationCreate,
    AlertUpdate,
    AnalyticsRule,
    AnalyticsRuleCreate,
    AnalyticsRuleUpdate,
    BiocRule,
    BiocRuleCreate,
    BiocRuleUpdate,
    Endpoint,
    EndpointAction,
    EndpointActionCreate,
    EndpointActionResult,
    EndpointProcess,
    Handover,
    HandoverCreate,
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
    WorkplanUpdate,
    YaraMatch,
    YaraRule,
)
from .data.yara_rules import YARA_RULES
from .database import SessionLocal
from . import crud, models

app = FastAPI(title="EventSec Enterprise")
instrumentator = Instrumentator().instrument(app).expose(app, include_in_schema=False)

app.include_router(siem_router.router)
app.include_router(edr_router.router)
app.include_router(agents_router.router)
app.include_router(events_router.router)
app.include_router(rules_router.router)
app.include_router(inventory_router.router)
app.include_router(vulnerabilities_router.router)
app.include_router(sca_router.router)

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

# "Base de datos" en memoria (suficiente para demo)
alerts_db: Dict[int, Alert] = {}
handovers_db: Dict[int, Handover] = {}
users_db: Dict[int, UserProfile] = {}
user_passwords: Dict[int, str] = {}  # user_id -> hashed_password
workgroups_db: Dict[int, WorkGroup] = {}
escalations_db: Dict[int, AlertEscalation] = {}
workplans_db: Dict[int, Workplan] = {}
action_logs_db: Dict[int, ActionLog] = {}
warroom_notes_db: Dict[int, WarRoomNote] = {}
sandbox_results_db: Dict[int, SandboxAnalysisResult] = {}
endpoints_db: Dict[int, Endpoint] = {}
indicators_db: Dict[int, Indicator] = {}
bioc_rules_db: Dict[int, BiocRule] = {}
analytics_rules_db: Dict[int, AnalyticsRule] = {}
network_events_db: Dict[int, NetworkEvent] = {}
endpoint_actions_db: Dict[int, EndpointAction] = {}

next_alert_id = 1
next_handover_id = 1
next_user_id = 1
next_workgroup_id = 1
next_escalation_id = 1
next_workplan_id = 1
next_action_log_id = 1
next_warroom_note_id = 1
next_sandbox_result_id = 1
next_endpoint_id = 1
next_indicator_id = 1
next_bioc_rule_id = 1
next_analytics_rule_id = 1
next_network_event_id = 1
next_endpoint_action_id = 1
yara_rules_cache: List[YaraRule] = [YaraRule(**rule) for rule in YARA_RULES]
AGENT_SHARED_TOKEN = os.getenv("EVENTSEC_AGENT_TOKEN", "eventsec-agent-token")


def is_agent_request(agent_token: Optional[str]) -> bool:
    return bool(agent_token and secrets.compare_digest(agent_token, AGENT_SHARED_TOKEN))


def ensure_user_or_agent(
    current_user: Optional[UserProfile],
    agent_token: Optional[str],
) -> Optional[UserProfile]:
    if current_user:
        return current_user
    if is_agent_request(agent_token):
        return None
    raise HTTPException(
        status_code=401,
        detail="Invalid authentication credentials",
    )


def seed_data() -> None:
    """Crear algunos datos de ejemplo en memoria."""
    global next_alert_id, next_handover_id, next_user_id

    if alerts_db:
        return

    now = datetime.now(timezone.utc)
    
    # Create admin user
    admin_user = UserProfile(
        id=1,
        full_name="Admin User",
        role="admin",
        email="admin@example.com",
        avatar_url=None,
        timezone="Europe/Madrid",
        team="Management",
        manager=None,
        computer="ADMIN-PC-01",
        mobile_phone="+1234567890",
    )
    users_db[1] = admin_user
    user_passwords[1] = get_password_hash("Admin123!")  # Default admin password
    
    # Create analyst user
    analyst_user = UserProfile(
        id=2,
        full_name="SOC Analyst",
        role="analyst",
        email="analyst@example.com",
        avatar_url=None,
        timezone="Europe/Madrid",
        team="SOC Team 1",
        manager="Admin User",
        computer="ANALYST-PC-01",
        mobile_phone="+1234567891",
    )
    users_db[2] = analyst_user
    user_passwords[2] = get_password_hash("Analyst123!")
    
    next_user_id = 3
    
    # Seed endpoints
    global next_endpoint_id
    endpoint_samples = [
        Endpoint(
            id=1,
            hostname="WIN-SEC-SRV01",
            display_name="WIN-SEC-SRV01",
            status="protected",
            agent_status="connected",
            agent_version="v2.5.1",
            ip_address="192.168.1.102",
            owner="Alex Jensen",
            os="Windows Server",
            os_version="2022 21H2",
            cpu_model="Intel Xeon E-2388G @ 3.20GHz",
            ram_gb=32,
            disk_gb=512,
            resource_usage={"cpu": 34.0, "memory": 58.0, "disk": 82.0},
            last_seen=now,
            location="Data Center 01",
            processes=[
                EndpointProcess(name="svchost.exe", pid=1124, user="SYSTEM", cpu=5.21, ram=2.34),
                EndpointProcess(name="chrome.exe", pid=8744, user="Administrator", cpu=3.88, ram=8.12),
                EndpointProcess(name="powershell.exe", pid=9120, user="Administrator", cpu=1.92, ram=1.05),
                EndpointProcess(name="sqlservr.exe", pid=4532, user="NT SERVICE\\MSSQLSERVER", cpu=0.87, ram=15.6),
            ],
            alerts_open=1,
            tags=["Critical", "Production"],
        ),
        Endpoint(
            id=2,
            hostname="LAPTOP-T1-DEV",
            display_name="Analyst Laptop",
            status="monitoring",
            agent_status="connected",
            agent_version="v2.4.0",
            ip_address="10.0.5.23",
            owner="Sara Patel",
            os="Windows 11 Pro",
            os_version="22H2",
            cpu_model="Intel i7-1185G7",
            ram_gb=16,
            disk_gb=256,
            resource_usage={"cpu": 41.0, "memory": 64.0, "disk": 55.0},
            last_seen=now - timedelta(minutes=3),
            location="HQ SOC Floor",
            processes=[
                EndpointProcess(name="Teams.exe", pid=4112, user="Sara", cpu=4.2, ram=5.8),
                EndpointProcess(name="Excel.exe", pid=5503, user="Sara", cpu=2.1, ram=3.4),
            ],
            alerts_open=2,
            tags=["Tier1"],
        ),
        Endpoint(
            id=3,
            hostname="LINUX-WEB-01",
            display_name="WEB-01",
            status="isolated",
            agent_status="disconnected",
            agent_version="v2.3.5",
            ip_address="172.16.20.14",
            owner="WebOps",
            os="Ubuntu Server",
            os_version="22.04",
            cpu_model="AMD EPYC 7502P",
            ram_gb=64,
            disk_gb=1024,
            resource_usage={"cpu": 12.0, "memory": 44.0, "disk": 67.0},
            last_seen=now - timedelta(minutes=45),
            location="DMZ Rack 3",
            processes=[
                EndpointProcess(name="nginx", pid=1241, user="www-data", cpu=2.2, ram=1.1),
                EndpointProcess(name="php-fpm", pid=2200, user="www-data", cpu=1.8, ram=2.2),
            ],
            alerts_open=3,
            tags=["DMZ", "HighTraffic"],
        ),
    ]
    for endpoint in endpoint_samples:
        endpoints_db[endpoint.id] = endpoint
    next_endpoint_id = len(endpoint_samples) + 1

    # Seed alerts
    examples = [
        Alert(
            id=1,
            title="Suspicious sign-in from new location",
            description="Multiple failed sign-ins followed by a successful login from an unknown IP.",
            source="Azure AD",
            category="Authentication",
            severity="high",
            status="open",
            url="https://portal.azure.com",
            sender=None,
            username="jdoe",
            hostname=None,
            created_at=now - timedelta(hours=2),
            updated_at=now - timedelta(hours=1, minutes=30),
        ),
        Alert(
            id=2,
            title="Malware detection on endpoint",
            description="EDR detected a suspicious PowerShell process spawning from Outlook.",
            source="Endpoint EDR",
            category="Malware",
            severity="critical",
            status="in_progress",
            url=None,
            sender="alerts@edr.local",
            username="asmith",
            hostname="LAPTOP-01",
            created_at=now - timedelta(hours=4),
            updated_at=now - timedelta(hours=3, minutes=10),
        ),
        Alert(
            id=3,
            title="Multiple 403 responses from single IP",
            description="High number of forbidden responses detected from a single external IP.",
            source="WAF",
            category="Web",
            severity="medium",
            status="open",
            url="https://portal.waf.local",
            sender=None,
            username=None,
            hostname=None,
            created_at=now - timedelta(days=1),
            updated_at=now - timedelta(days=1, hours=-1),
        ),
    ]

    for alert in examples:
        alerts_db[alert.id] = alert

    next_alert_id = max(alerts_db.keys()) + 1 if alerts_db else 1
    next_handover_id = 1

    # Seed indicators and BIOCs
    global next_indicator_id, next_bioc_rule_id, next_analytics_rule_id
    indicator_samples = [
        Indicator(
            id=1,
            type="url",
            value="http://accounts-login[.]secure-sync.app",
            description="Credential harvesting kit targeting O365 tenants",
            severity="high",
            source="Phishing feed",
            tags=["o365", "phishing"],
            status="active",
            created_at=now - timedelta(hours=6),
            updated_at=now - timedelta(hours=1),
        ),
        Indicator(
            id=2,
            type="hash",
            value="b6f0baba3bd4f09bc5f9479fa3c4e321c9f7aa20cc3d5ffb97734ffb2df4be2c",
            description="SHA-256 hash for WannaCry dropper",
            severity="critical",
            source="Yara-Rules",
            tags=["ransomware", "wannacry"],
            status="active",
            created_at=now - timedelta(days=1),
            updated_at=now - timedelta(hours=20),
        ),
    ]
    for indicator in indicator_samples:
        indicators_db[indicator.id] = indicator
    next_indicator_id = len(indicators_db) + 1

    bioc_samples = [
        BiocRule(
            id=1,
            name="Office spawning PowerShell with encoded command",
            description="Detects Office processes launching PowerShell with base64 payloads",
            platform="Windows",
            tactic="Execution",
            technique="T1059.001",
            detection_logic="DeviceProcessEvents | where InitiatingProcessFileName in ('winword.exe','excel.exe') ..."
            " | where FileName == 'powershell.exe' and ProcessCommandLine contains '-enc'",
            severity="high",
            tags=["process-tree", "macro"],
            created_at=now - timedelta(days=2),
            updated_at=now - timedelta(hours=5),
        ),
        BiocRule(
            id=2,
            name="Multiple failed logons followed by success",
            description="Detects brute force attempts that eventually succeed",
            platform="Azure AD",
            tactic="Credential Access",
            technique="T1110",
            detection_logic="SigninLogs | summarize count() by UserPrincipalName, ResultType ...",
            severity="medium",
            tags=["cloud", "authentication"],
            created_at=now - timedelta(days=3),
            updated_at=now - timedelta(days=1),
        ),
    ]
    for rule in bioc_samples:
        bioc_rules_db[rule.id] = rule
    next_bioc_rule_id = len(bioc_rules_db) + 1

    analytics_samples = [
        AnalyticsRule(
            id=1,
            name="Impossible travel followed by privileged action",
            description="Detects logons from distant geographies followed by role assignment",
            datasource="Azure AD",
            severity="high",
            status="enabled",
            query="let threshold = 5000; SigninLogs | ...",
            owner="Admin User",
            created_at=now - timedelta(days=5),
            updated_at=now - timedelta(days=1),
        ),
        AnalyticsRule(
            id=2,
            name="EDR alert with outbound C2",
            description="Combines high severity EDR alert with suspicious egress traffic",
            datasource="EDR + Firewall",
            severity="critical",
            status="enabled",
            query="EdrEvents | where Severity == 'High' ...",
            owner="SOC Analyst",
            created_at=now - timedelta(days=4),
            updated_at=now - timedelta(hours=10),
        ),
    ]
    for rule in analytics_samples:
        analytics_rules_db[rule.id] = rule
    next_analytics_rule_id = len(analytics_rules_db) + 1

    # Seed a workplan
    global next_workplan_id
    initial_workplan = Workplan(
        id=1,
        title="Contain WannaCry outbreak",
        description="Validate isolation of impacted endpoints, block C2, coordinate comms",
        alert_id=2,
        assigned_to=2,
        created_by=1,
        status="in_progress",
        created_at=now - timedelta(hours=3),
        updated_at=now - timedelta(hours=1),
    )
    workplans_db[1] = initial_workplan
    next_workplan_id = 2

    # Seed a network event
    global next_network_event_id
    network_event = NetworkEvent(
        id=1,
        hostname="LAPTOP-T1-DEV",
        username="sara.patel",
        url="http://accounts-login.secure-sync.app",
        verdict="malicious",
        category="phishing",
        description="User clicked credential harvesting URL blocked by SWG",
        severity="high",
        created_at=now - timedelta(minutes=40),
    )
    network_events_db[network_event.id] = network_event
    next_network_event_id = 2


async def process_event_queue(queue: asyncio.Queue) -> None:
    while True:
        event_id = await queue.get()
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
                doc = {
                    "event_id": event.id,
                    "agent_id": event.agent_id,
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "category": event.category,
                    "details": details,
                    "message": details.get("message"),
                    "timestamp": event.created_at.isoformat(),
                }
                try:
                    search.index_event(doc)
                except Exception as exc:  # noqa: BLE001
                    logger.error("Failed to index event %s: %s", event.id, exc)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error processing event %s: %s", event_id, exc)
        finally:
            queue.task_done()


@app.on_event("startup")
async def startup_event() -> None:
    seed_data()
    try:
        search.ensure_indices()
        logger.info("OpenSearch indices ready")
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to prepare OpenSearch indices: %s", exc)
    queue: asyncio.Queue = asyncio.Queue()
    app.state.event_queue = queue
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


# --- Authentication ---


@app.post("/auth/login", response_model=LoginResponse, tags=["auth"])
def login(payload: LoginRequest, response: Response) -> LoginResponse:
    """Login endpoint."""
    # Find user by email
    user = None
    for u in users_db.values():
        if u.email == payload.email:
            user = u
            break
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    hashed_password = user_passwords.get(user.id)
    if not hashed_password or not verify_password(payload.password, hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(data={"sub": user.id})
    response.set_cookie(
        "access_token",
        access_token,
        httponly=False,
        samesite="lax",
        secure=False,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return LoginResponse(access_token=access_token, user=user)


# --- User Management ---


@app.get("/me", response_model=UserProfile, tags=["profile"])
def get_profile(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
    return current_user


@app.get("/users", response_model=List[UserProfile], tags=["users"])
def list_users(current_user: UserProfile = Depends(get_current_user)) -> List[UserProfile]:
    """List all users for collaboration workflows."""
    return list(users_db.values())


@app.post("/users", response_model=UserProfile, tags=["users"])
def create_user(
    payload: UserCreate,
    current_user: UserProfile = Depends(get_current_admin_user)
) -> UserProfile:
    """Create a new user. Admin only."""
    global next_user_id
    
    # Check if email already exists
    for u in users_db.values():
        if u.email == payload.email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    now = datetime.now(timezone.utc)
    user = UserProfile(
        id=next_user_id,
        full_name=payload.full_name,
        role=payload.role,
        email=payload.email,
        avatar_url=None,
        timezone=payload.timezone,
        team=payload.team,
        manager=payload.manager,
        computer=payload.computer,
        mobile_phone=payload.mobile_phone,
    )
    users_db[next_user_id] = user
    user_passwords[next_user_id] = get_password_hash(payload.password)
    next_user_id += 1
    return user


@app.patch("/users/{user_id}", response_model=UserProfile, tags=["users"])
def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: UserProfile = Depends(get_current_admin_user)
) -> UserProfile:
    """Update a user. Admin only."""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users_db[user_id]
    user_dict = user.model_dump()
    
    # Update only provided fields
    update_dict = payload.model_dump(exclude_unset=True)
    user_dict.update(update_dict)
    
    updated_user = UserProfile(**user_dict)
    users_db[user_id] = updated_user
    return updated_user


# --- Alertas ---


@app.get("/alerts", response_model=List[Alert], tags=["alerts"])
def list_alerts(current_user: UserProfile = Depends(get_current_user)) -> List[Alert]:
    return sorted(alerts_db.values(), key=lambda a: a.created_at, reverse=True)


@app.get("/alerts/{alert_id}", response_model=Alert, tags=["alerts"])
def get_alert(alert_id: int, current_user: UserProfile = Depends(get_current_user)) -> Alert:
    alert = alerts_db.get(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@app.post("/alerts", response_model=Alert, tags=["alerts"])
def create_alert(
    payload: AlertCreate,
    current_user: Optional[UserProfile] = Depends(get_optional_user),
    agent_token: Optional[str] = Header(None, alias="X-Agent-Token"),
) -> Alert:
    """Create a new alert."""
    global next_alert_id
    ensure_user_or_agent(current_user, agent_token)
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")
    if not payload.source or not payload.source.strip():
        raise HTTPException(status_code=400, detail="Source is required")
    now = datetime.now(timezone.utc)
    alert = Alert(
        id=next_alert_id,
        status="open",
        created_at=now,
        updated_at=now,
        **payload.model_dump(),
    )
    alerts_db[next_alert_id] = alert
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
    next_alert_id += 1
    return alert


@app.patch("/alerts/{alert_id}", response_model=Alert, tags=["alerts"])
def update_alert(
    alert_id: int,
    payload: AlertUpdate,
    current_user: UserProfile = Depends(get_current_user)
) -> Alert:
    """Update alert status."""
    if alert_id not in alerts_db:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert = alerts_db[alert_id]
    alert_dict = alert.model_dump()
    alert_dict["status"] = payload.status
    alert_dict["updated_at"] = datetime.now(timezone.utc)
    updated_alert = Alert(**alert_dict)
    alerts_db[alert_id] = updated_alert
    return updated_alert


def log_action(
    user_id: int,
    action_type: str,
    target_type: str,
    target_id: int,
    parameters: Dict[str, Any] = None
) -> None:
    """Helper function to log actions."""
    global next_action_log_id
    if parameters is None:
        parameters = {}
    log = ActionLog(
        id=next_action_log_id,
        user_id=user_id,
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        parameters=parameters,
        created_at=datetime.now(timezone.utc),
    )
    action_logs_db[next_action_log_id] = log
    next_action_log_id += 1


def update_endpoint_state(endpoint_id: int, **changes: Any) -> Endpoint:
    endpoint = endpoints_db.get(endpoint_id)
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    data = endpoint.model_dump()
    data.update(changes)
    updated = Endpoint(**data)
    endpoints_db[endpoint_id] = updated
    return updated


def find_endpoint_by_hostname(hostname: str) -> Optional[Endpoint]:
    normalized = hostname.lower()
    for endpoint in endpoints_db.values():
        if endpoint.hostname.lower() == normalized or endpoint.display_name.lower() == normalized:
            return endpoint
    return None


def create_alert_from_network_event(event: NetworkEvent) -> Alert:
    """Automatically registers an alert for high risk network events."""
    global next_alert_id
    now = datetime.now(timezone.utc)
    alert = Alert(
        id=next_alert_id,
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
    alerts_db[next_alert_id] = alert
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
    next_alert_id += 1
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
    current_user: UserProfile = Depends(get_current_user)
) -> dict:
    if alert_id not in alerts_db:
        raise HTTPException(status_code=404, detail="Alert not found")
    if not url or not url.strip():
        raise HTTPException(status_code=400, detail="URL parameter is required")
    log_action(current_user.id, "block_url", "alert", alert_id, {"url": url})
    return {"detail": f"URL {url} blocked for alert {alert_id}"}


@app.post("/alerts/{alert_id}/unblock-url", tags=["alerts", "actions"])
def unblock_url(
    alert_id: int,
    url: str = Query(..., description="URL to unblock"),
    current_user: UserProfile = Depends(get_current_user)
) -> dict:
    if alert_id not in alerts_db:
        raise HTTPException(status_code=404, detail="Alert not found")
    if not url or not url.strip():
        raise HTTPException(status_code=400, detail="URL parameter is required")
    log_action(current_user.id, "unblock_url", "alert", alert_id, {"url": url})
    return {"detail": f"URL {url} unblocked for alert {alert_id}"}


@app.post("/alerts/{alert_id}/block-sender", tags=["alerts", "actions"])
def block_sender(
    alert_id: int,
    sender: str = Query(..., description="Email sender to block"),
    current_user: UserProfile = Depends(get_current_user)
) -> dict:
    if alert_id not in alerts_db:
        raise HTTPException(status_code=404, detail="Alert not found")
    if not sender or not sender.strip():
        raise HTTPException(status_code=400, detail="Sender parameter is required")
    log_action(current_user.id, "block_sender", "alert", alert_id, {"sender": sender})
    return {"detail": f"Sender {sender} blocked for alert {alert_id}"}


@app.post("/alerts/{alert_id}/unblock-sender", tags=["alerts", "actions"])
def unblock_sender(
    alert_id: int,
    sender: str = Query(..., description="Email sender to unblock"),
    current_user: UserProfile = Depends(get_current_user)
) -> dict:
    if alert_id not in alerts_db:
        raise HTTPException(status_code=404, detail="Alert not found")
    if not sender or not sender.strip():
        raise HTTPException(status_code=400, detail="Sender parameter is required")
    log_action(current_user.id, "unblock_sender", "alert", alert_id, {"sender": sender})
    return {"detail": f"Sender {sender} unblocked for alert {alert_id}"}


@app.post("/alerts/{alert_id}/revoke-session", tags=["alerts", "actions"])
def revoke_user_session(
    alert_id: int,
    username: str = Query(..., description="Username to revoke session for"),
    current_user: UserProfile = Depends(get_current_user)
) -> dict:
    if alert_id not in alerts_db:
        raise HTTPException(status_code=404, detail="Alert not found")
    if not username or not username.strip():
        raise HTTPException(status_code=400, detail="Username parameter is required")
    log_action(current_user.id, "revoke_session", "alert", alert_id, {"username": username})
    return {"detail": f"User session revoked for {username} in alert {alert_id}"}


@app.post("/alerts/{alert_id}/isolate-device", tags=["alerts", "actions"])
def isolate_device(
    alert_id: int,
    hostname: str = Query(..., description="Hostname to isolate"),
    current_user: UserProfile = Depends(get_current_user)
) -> dict:
    if alert_id not in alerts_db:
        raise HTTPException(status_code=404, detail="Alert not found")
    if not hostname or not hostname.strip():
        raise HTTPException(status_code=400, detail="Hostname parameter is required")
    log_action(current_user.id, "isolate_device", "alert", alert_id, {"hostname": hostname})
    return {"detail": f"Device {hostname} isolated for alert {alert_id}"}


@app.delete("/alerts/{alert_id}", tags=["alerts"])
def delete_alert(
    alert_id: int,
    current_user: UserProfile = Depends(get_current_user)
) -> dict:
    """Delete an alert."""
    if alert_id not in alerts_db:
        raise HTTPException(status_code=404, detail="Alert not found")
    log_action(current_user.id, "delete_alert", "alert", alert_id)
    del alerts_db[alert_id]
    return {"detail": f"Alert {alert_id} deleted successfully"}


@app.post("/alerts/{alert_id}/escalate", response_model=AlertEscalation, tags=["alerts"])
def escalate_alert(
    alert_id: int,
    payload: AlertEscalationCreate,
    current_user: UserProfile = Depends(get_current_user)
) -> AlertEscalation:
    """Escalate an alert to another user."""
    global next_escalation_id
    if alert_id not in alerts_db:
        raise HTTPException(status_code=404, detail="Alert not found")
    if payload.escalated_to not in users_db:
        raise HTTPException(status_code=404, detail="Target user not found")
    
    escalation = AlertEscalation(
        id=next_escalation_id,
        alert_id=alert_id,
        escalated_to=payload.escalated_to,
        escalated_by=current_user.id,
        reason=payload.reason,
        created_at=datetime.now(timezone.utc),
    )
    escalations_db[next_escalation_id] = escalation
    next_escalation_id += 1
    log_action(current_user.id, "escalate_alert", "alert", alert_id, {"escalated_to": payload.escalated_to})
    return escalation


# --- Handovers ---


@app.get("/handover", response_model=List[Handover], tags=["handover"])
def list_handovers(current_user: UserProfile = Depends(get_current_user)) -> List[Handover]:
    return sorted(handovers_db.values(), key=lambda h: h.created_at, reverse=True)


@app.post("/handover", response_model=Handover, tags=["handover"])
def create_handover(
    payload: HandoverCreate,
    current_user: UserProfile = Depends(get_current_user)
) -> Handover:
    """Create a new handover."""
    global next_handover_id
    if not payload.analyst or not payload.analyst.strip():
        raise HTTPException(status_code=400, detail="Analyst name is required")
    if payload.shift_start >= payload.shift_end:
        raise HTTPException(
            status_code=400, detail="Shift end must be after shift start"
        )
    now = datetime.now(timezone.utc)
    handover = Handover(
        id=next_handover_id,
        created_at=now,
        **payload.model_dump(),
    )
    handovers_db[next_handover_id] = handover
    next_handover_id += 1
    
    # Email sending (simulated - in production use actual email service)
    if payload.send_email and payload.recipient_emails:
        # In production, integrate with email service like SendGrid, AWS SES, etc.
        print(f"[EMAIL] Sending handover to: {', '.join(payload.recipient_emails)}")
        print(f"[EMAIL] Subject: Handover from {payload.analyst}")
        print(f"[EMAIL] Body: {payload.notes}")
    
    return handover


# --- Work Groups ---


@app.get("/workgroups", response_model=List[WorkGroup], tags=["workgroups"])
def list_workgroups(current_user: UserProfile = Depends(get_current_user)) -> List[WorkGroup]:
    return list(workgroups_db.values())


@app.post("/workgroups", response_model=WorkGroup, tags=["workgroups"])
def create_workgroup(
    payload: WorkGroupCreate,
    current_user: UserProfile = Depends(get_current_user)
) -> WorkGroup:
    """Create a work group. Admin or team lead only."""
    if current_user.role not in ["admin", "team_lead"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    global next_workgroup_id
    workgroup = WorkGroup(
        id=next_workgroup_id,
        name=payload.name,
        description=payload.description,
        members=payload.members,
        created_at=datetime.now(timezone.utc),
    )
    workgroups_db[next_workgroup_id] = workgroup
    next_workgroup_id += 1
    return workgroup


# --- Workplans ---


@app.get("/workplans", response_model=List[Workplan], tags=["workplans"])
def list_workplans(current_user: UserProfile = Depends(get_current_user)) -> List[Workplan]:
    return list(workplans_db.values())


@app.post("/workplans", response_model=Workplan, tags=["workplans"])
def create_workplan(
    payload: WorkplanCreate,
    current_user: UserProfile = Depends(get_current_user)
) -> Workplan:
    global next_workplan_id
    now = datetime.now(timezone.utc)
    workplan = Workplan(
        id=next_workplan_id,
        title=payload.title,
        description=payload.description,
        alert_id=payload.alert_id,
        assigned_to=payload.assigned_to,
        created_by=current_user.id,
        status="open",
        created_at=now,
        updated_at=now,
    )
    workplans_db[next_workplan_id] = workplan
    next_workplan_id += 1
    return workplan


@app.patch("/workplans/{workplan_id}", response_model=Workplan, tags=["workplans"])
def update_workplan_entry(
    workplan_id: int,
    payload: WorkplanUpdate,
    current_user: UserProfile = Depends(get_current_user)
) -> Workplan:
    if workplan_id not in workplans_db:
        raise HTTPException(status_code=404, detail="Workplan not found")
    workplan = workplans_db[workplan_id]
    updates = payload.model_dump(exclude_unset=True)
    data = workplan.model_dump()
    data.update(updates)
    data["updated_at"] = datetime.now(timezone.utc)
    updated = Workplan(**data)
    workplans_db[workplan_id] = updated
    log_action(current_user.id, "update_workplan", "workplan", workplan_id, updates)
    return updated


# --- Threat Intel (IOC/BIOC/YARA) ---


@app.get("/indicators", response_model=List[Indicator], tags=["intel"])
def list_indicators(current_user: UserProfile = Depends(get_current_user)) -> List[Indicator]:
    return sorted(indicators_db.values(), key=lambda ind: ind.updated_at, reverse=True)


@app.post("/indicators", response_model=Indicator, tags=["intel"])
def create_indicator_entry(
    payload: IndicatorCreate,
    current_user: UserProfile = Depends(get_current_user)
) -> Indicator:
    global next_indicator_id
    now = datetime.now(timezone.utc)
    indicator = Indicator(
        id=next_indicator_id,
        created_at=now,
        updated_at=now,
        **payload.model_dump(),
    )
    indicators_db[next_indicator_id] = indicator
    log_action(current_user.id, "create_indicator", "indicator", indicator.id, indicator.model_dump())
    next_indicator_id += 1
    return indicator


@app.patch("/indicators/{indicator_id}", response_model=Indicator, tags=["intel"])
def update_indicator_entry(
    indicator_id: int,
    payload: IndicatorUpdate,
    current_user: UserProfile = Depends(get_current_user)
) -> Indicator:
    indicator = indicators_db.get(indicator_id)
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    updates = payload.model_dump(exclude_unset=True)
    data = indicator.model_dump()
    for key, value in updates.items():
        if value is not None:
            data[key] = value
    data["updated_at"] = datetime.now(timezone.utc)
    updated = Indicator(**data)
    indicators_db[indicator_id] = updated
    log_action(current_user.id, "update_indicator", "indicator", indicator_id, updates)
    return updated


@app.get("/biocs", response_model=List[BiocRule], tags=["intel"])
def list_bioc_rules(current_user: UserProfile = Depends(get_current_user)) -> List[BiocRule]:
    return sorted(bioc_rules_db.values(), key=lambda rule: rule.updated_at, reverse=True)


@app.post("/biocs", response_model=BiocRule, tags=["intel"])
def create_bioc_rule(
    payload: BiocRuleCreate,
    current_user: UserProfile = Depends(get_current_user)
) -> BiocRule:
    global next_bioc_rule_id
    now = datetime.now(timezone.utc)
    rule = BiocRule(
        id=next_bioc_rule_id,
        created_at=now,
        updated_at=now,
        **payload.model_dump(),
    )
    bioc_rules_db[next_bioc_rule_id] = rule
    log_action(current_user.id, "create_bioc", "bioc_rule", rule.id, rule.model_dump())
    next_bioc_rule_id += 1
    return rule


@app.patch("/biocs/{rule_id}", response_model=BiocRule, tags=["intel"])
def update_bioc_rule(
    rule_id: int,
    payload: BiocRuleUpdate,
    current_user: UserProfile = Depends(get_current_user)
) -> BiocRule:
    rule = bioc_rules_db.get(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="BIOC rule not found")
    updates = payload.model_dump(exclude_unset=True)
    data = rule.model_dump()
    for key, value in updates.items():
        if value is not None:
            data[key] = value
    data["updated_at"] = datetime.now(timezone.utc)
    updated = BiocRule(**data)
    bioc_rules_db[rule_id] = updated
    log_action(current_user.id, "update_bioc", "bioc_rule", rule_id, updates)
    return updated


@app.get("/analytics/rules", response_model=List[AnalyticsRule], tags=["analytics"])
def list_analytics_rules(
    current_user: UserProfile = Depends(get_current_user),
) -> List[AnalyticsRule]:
    return sorted(analytics_rules_db.values(), key=lambda rule: rule.updated_at, reverse=True)


@app.get("/analytics/rules/{rule_id}", response_model=AnalyticsRule, tags=["analytics"])
def get_analytics_rule(
    rule_id: int,
    current_user: UserProfile = Depends(get_current_user),
) -> AnalyticsRule:
    rule = analytics_rules_db.get(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Analytics rule not found")
    return rule


@app.post("/analytics/rules", response_model=AnalyticsRule, tags=["analytics"])
def create_analytics_rule(
    payload: AnalyticsRuleCreate,
    current_user: UserProfile = Depends(get_current_user),
) -> AnalyticsRule:
    global next_analytics_rule_id
    now = datetime.now(timezone.utc)
    rule = AnalyticsRule(
        id=next_analytics_rule_id,
        created_at=now,
        updated_at=now,
        status="enabled",
        **payload.model_dump(),
    )
    analytics_rules_db[next_analytics_rule_id] = rule
    log_action(current_user.id, "create_analytics_rule", "analytics_rule", rule.id, rule.model_dump())
    next_analytics_rule_id += 1
    return rule


@app.patch("/analytics/rules/{rule_id}", response_model=AnalyticsRule, tags=["analytics"])
def update_analytics_rule(
    rule_id: int,
    payload: AnalyticsRuleUpdate,
    current_user: UserProfile = Depends(get_current_user),
) -> AnalyticsRule:
    rule = analytics_rules_db.get(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Analytics rule not found")
    updates = payload.model_dump(exclude_unset=True)
    data = rule.model_dump()
    for key, value in updates.items():
        if value is not None:
            data[key] = value
    data["updated_at"] = datetime.now(timezone.utc)
    updated = AnalyticsRule(**data)
    analytics_rules_db[rule_id] = updated
    log_action(current_user.id, "update_analytics_rule", "analytics_rule", rule_id, updates)
    return updated


@app.get("/yara/rules", response_model=List[YaraRule], tags=["intel"])
def list_yara_rules(current_user: UserProfile = Depends(get_current_user)) -> List[YaraRule]:
    return yara_rules_cache


# --- Action Logs ---


@app.get("/action-logs", response_model=List[ActionLog], tags=["logs"])
def list_action_logs(current_user: UserProfile = Depends(get_current_user)) -> List[ActionLog]:
    """List action logs. Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return sorted(action_logs_db.values(), key=lambda l: l.created_at, reverse=True)


# --- War Room ---


@app.get("/warroom/notes", response_model=List[WarRoomNote], tags=["warroom"])
def list_warroom_notes(
    alert_id: Optional[int] = None,
    current_user: UserProfile = Depends(get_current_user)
) -> List[WarRoomNote]:
    notes = list(warroom_notes_db.values())
    if alert_id:
        notes = [n for n in notes if n.alert_id == alert_id]
    return sorted(notes, key=lambda n: n.created_at, reverse=True)


@app.post("/warroom/notes", response_model=WarRoomNote, tags=["warroom"])
def create_warroom_note(
    payload: WarRoomNoteCreate,
    current_user: UserProfile = Depends(get_current_user)
) -> WarRoomNote:
    global next_warroom_note_id
    note = WarRoomNote(
        id=next_warroom_note_id,
        alert_id=payload.alert_id,
        content=payload.content,
        created_by=current_user.id,
        attachments=payload.attachments,
        created_at=datetime.now(timezone.utc),
    )
    warroom_notes_db[next_warroom_note_id] = note
    next_warroom_note_id += 1
    return note


# --- Sandbox ---


@app.post("/sandbox/analyze", response_model=SandboxAnalysisResult, tags=["sandbox"])
def analyze_sandbox(
    payload: SandboxAnalysisRequest,
    current_user: UserProfile = Depends(get_current_user)
) -> SandboxAnalysisResult:
    """Analyze file, IP, URL, domain, or hash using VT and OSINT sources."""
    global next_sandbox_result_id

    now = datetime.now(timezone.utc)
    hash_value = payload.metadata.get("hash") if payload.metadata else None
    filename = payload.filename or payload.metadata.get("filename") if payload.metadata else None

    vt_results = {
        "malicious": 7,
        "suspicious": 1,
        "clean": 40,
        "undetected": 4,
        "last_analysis_date": now.isoformat(),
    }

    osint_results = {
        "reputation": "High risk",
        "threat_intel": ["Associated with ransomware campaigns", "Observed in phishing kits"],
        "yara_rules": ["WannaCry_Generic", "Suspicious_Macro_Execution"],
    }

    iocs = [
        {"type": "IP Address", "value": "142.250.184.238", "description": "C2 infrastructure"},
        {"type": "Domain", "value": "iqwerfsdopgjifaposrdfjhosguriJfaewrwer.gwea.com", "description": "Kill-switch domain"},
        {"type": "File Path", "value": r"C:\Users\Admin\Desktop\PLEASE_READ_ME.txt", "description": "Ransom note dropped"},
        {"type": "Registry Key", "value": r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run\mssecsvc.exe", "description": "Persistence mechanism"},
    ]

    # Associate with endpoints (simple heuristic: match first 2 endpoints)
    matched_endpoints = []
    for endpoint in list(endpoints_db.values())[:2]:
        matched_endpoints.append(
            {
                "id": endpoint.id,
                "hostname": endpoint.hostname,
                "status": endpoint.status,
                "ip_address": endpoint.ip_address,
                "last_seen": endpoint.last_seen.isoformat(),
                "location": endpoint.location,
            }
        )

    yara_matches = pick_yara_matches(2 if payload.type == "file" else 1)

    result = SandboxAnalysisResult(
        id=next_sandbox_result_id,
        type=payload.type,
        value=payload.value,
        filename=filename,
        verdict="malicious",
        threat_type="Ransomware (WannaCry)" if payload.type == "file" else "Suspicious URL",
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
    sandbox_results_db[next_sandbox_result_id] = result
    next_sandbox_result_id += 1
    return result


@app.get("/sandbox/analyses", response_model=List[SandboxAnalysisResult], tags=["sandbox"])
def list_sandbox_analyses(current_user: UserProfile = Depends(get_current_user)) -> List[SandboxAnalysisResult]:
    return sorted(sandbox_results_db.values(), key=lambda r: r.created_at, reverse=True)


# --- Network telemetry ---


@app.get("/network/events", response_model=List[NetworkEvent], tags=["network"])
def list_network_events_api(
    current_user: UserProfile = Depends(get_current_user),
) -> List[NetworkEvent]:
    return sorted(network_events_db.values(), key=lambda evt: evt.created_at, reverse=True)


@app.post("/network/events", response_model=NetworkEvent, tags=["network"])
def create_network_event_api(
    payload: NetworkEventCreate,
    current_user: Optional[UserProfile] = Depends(get_optional_user),
    agent_token: Optional[str] = Header(None, alias="X-Agent-Token"),
) -> NetworkEvent:
    global next_network_event_id
    ensure_user_or_agent(current_user, agent_token)
    now = datetime.now(timezone.utc)
    description = payload.description or f"{payload.url} categorised as {payload.category}"
    event = NetworkEvent(
        id=next_network_event_id,
        hostname=payload.hostname,
        username=payload.username,
        url=payload.url,
        verdict=payload.verdict,
        category=payload.category,
        description=description,
        severity=payload.severity,
        created_at=now,
    )
    network_events_db[next_network_event_id] = event
    next_network_event_id += 1

    if payload.verdict == "malicious":
        new_alert = create_alert_from_network_event(event)
        if current_user:
            log_action(current_user.id, "network_event_alert", "alert", new_alert.id, {"url": payload.url})
    return event


@app.get("/endpoints", response_model=List[Endpoint], tags=["endpoints"])
def list_endpoints(current_user: UserProfile = Depends(get_current_user)) -> List[Endpoint]:
    return list(endpoints_db.values())


@app.get("/endpoints/{endpoint_id}", response_model=Endpoint, tags=["endpoints"])
def get_endpoint(endpoint_id: int, current_user: UserProfile = Depends(get_current_user)) -> Endpoint:
    endpoint = endpoints_db.get(endpoint_id)
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    return endpoint


@app.get("/endpoints/{endpoint_id}/actions", response_model=List[EndpointAction], tags=["endpoints"])
def list_endpoint_actions_api(
    endpoint_id: int,
    current_user: UserProfile = Depends(get_current_user),
) -> List[EndpointAction]:
    if endpoint_id not in endpoints_db:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    return sorted(
        [action for action in endpoint_actions_db.values() if action.endpoint_id == endpoint_id],
        key=lambda action: action.requested_at,
        reverse=True,
    )


@app.post("/endpoints/{endpoint_id}/actions", response_model=EndpointAction, tags=["endpoints"])
def create_endpoint_action(
    endpoint_id: int,
    payload: EndpointActionCreate,
    current_user: UserProfile = Depends(get_current_user),
) -> EndpointAction:
    global next_endpoint_action_id
    if endpoint_id not in endpoints_db:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    action = EndpointAction(
        id=next_endpoint_action_id,
        endpoint_id=endpoint_id,
        action_type=payload.action_type,
        parameters=payload.parameters,
        status="pending",
        requested_by=current_user.id,
        requested_at=datetime.now(timezone.utc),
    )
    endpoint_actions_db[next_endpoint_action_id] = action
    next_endpoint_action_id += 1
    log_action(current_user.id, f"endpoint_{payload.action_type}", "endpoint", endpoint_id, payload.parameters)
    return action


@app.get("/agent/actions", response_model=List[EndpointAction], tags=["agent"])
def pull_agent_actions(
    hostname: str,
    current_user: Optional[UserProfile] = Depends(get_optional_user),
    agent_token: Optional[str] = Header(None, alias="X-Agent-Token"),
) -> List[EndpointAction]:
    ensure_user_or_agent(current_user, agent_token)
    endpoint = find_endpoint_by_hostname(hostname)
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not registered")
    return [
        action
        for action in endpoint_actions_db.values()
        if action.endpoint_id == endpoint.id and action.status == "pending"
    ]


@app.post("/agent/actions/{action_id}/complete", response_model=EndpointAction, tags=["agent"])
def complete_agent_action(
    action_id: int,
    payload: EndpointActionResult,
    current_user: Optional[UserProfile] = Depends(get_optional_user),
    agent_token: Optional[str] = Header(None, alias="X-Agent-Token"),
) -> EndpointAction:
    ensure_user_or_agent(current_user, agent_token)
    action = endpoint_actions_db.get(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    if action.status != "pending":
        return action
    status_value = "completed" if payload.success else "failed"
    action_data = action.model_dump()
    action_data["status"] = status_value
    action_data["completed_at"] = datetime.now(timezone.utc)
    action_data["output"] = payload.output
    updated_action = EndpointAction(**action_data)
    endpoint_actions_db[action_id] = updated_action

    if payload.success:
        if action.action_type == "isolate":
            update_endpoint_state(action.endpoint_id, status="isolated", agent_status="isolated")
        elif action.action_type == "release":
            update_endpoint_state(action.endpoint_id, status="protected", agent_status="connected")
        elif action.action_type == "reboot":
            update_endpoint_state(action.endpoint_id, last_seen=datetime.now(timezone.utc), agent_status="rebooting")
        elif action.action_type == "command":
            update_endpoint_state(action.endpoint_id, last_seen=datetime.now(timezone.utc))

    return updated_action
