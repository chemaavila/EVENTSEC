from __future__ import annotations

from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from .auth import get_password_hash


def seed_core_data(connection: sa.Connection) -> None:
    now = datetime.now(timezone.utc)
    
    def insert_if_missing(
        table: sa.TableClause,
        rows: list[dict],
        conflict_columns: list[str],
    ) -> None:
        if not rows:
            return
        if connection.dialect.name == "postgresql":
            stmt = (
                pg_insert(table)
                .values(rows)
                .on_conflict_do_nothing(index_elements=conflict_columns)
            )
            connection.execute(stmt)
            return
        for row in rows:
            filters = [getattr(table.c, col) == row[col] for col in conflict_columns]
            exists = connection.execute(
                sa.select(sa.literal(1)).select_from(table).where(sa.and_(*filters))
            ).scalar()
            if not exists:
                connection.execute(table.insert().values(**row))

    users_table = sa.table(
        "users",
        sa.column("id", sa.Integer),
        sa.column("full_name", sa.String),
        sa.column("role", sa.String),
        sa.column("email", sa.String),
        sa.column("hashed_password", sa.String),
        sa.column("timezone", sa.String),
        sa.column("tenant_id", sa.String),
        sa.column("team", sa.String),
        sa.column("manager", sa.String),
        sa.column("computer", sa.String),
        sa.column("mobile_phone", sa.String),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    admin_hash = get_password_hash("Admin123!")
    analyst_hash = get_password_hash("Analyst123!")
    insert_if_missing(
        users_table,
        [
            {
                "id": 1,
                "full_name": "Admin User",
                "role": "admin",
                "email": "admin@example.com",
                "hashed_password": admin_hash,
                "timezone": "Europe/Madrid",
                "tenant_id": "default",
                "team": "Management",
                "manager": None,
                "computer": "ADMIN-PC-01",
                "mobile_phone": "+1234567890",
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": 2,
                "full_name": "SOC Analyst",
                "role": "analyst",
                "email": "analyst@example.com",
                "hashed_password": analyst_hash,
                "timezone": "Europe/Madrid",
                "tenant_id": "default",
                "team": "SOC Team 1",
                "manager": "Admin User",
                "computer": "ANALYST-PC-01",
                "mobile_phone": "+1234567891",
                "created_at": now,
                "updated_at": now,
            },
        ],
        ["id"],
    )

    alerts_table = sa.table(
        "alerts",
        sa.column("id", sa.Integer),
        sa.column("title", sa.String),
        sa.column("description", sa.Text),
        sa.column("source", sa.String),
        sa.column("category", sa.String),
        sa.column("severity", sa.String),
        sa.column("status", sa.String),
        sa.column("url", sa.String),
        sa.column("sender", sa.String),
        sa.column("username", sa.String),
        sa.column("hostname", sa.String),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    alerts = [
        {
            "id": 1,
            "title": "Suspicious sign-in from new location",
            "description": "Multiple failed sign-ins followed by a successful login from an unknown IP.",
            "source": "Azure AD",
            "category": "Authentication",
            "severity": "high",
            "status": "open",
            "url": "https://portal.azure.com",
            "sender": None,
            "username": "jdoe",
            "hostname": None,
            "created_at": now - timedelta(hours=2),
            "updated_at": now - timedelta(hours=1, minutes=30),
        },
        {
            "id": 2,
            "title": "Malware detection on endpoint",
            "description": "EDR detected a suspicious PowerShell process spawning from Outlook.",
            "source": "Endpoint EDR",
            "category": "Malware",
            "severity": "critical",
            "status": "in_progress",
            "url": None,
            "sender": "alerts@edr.local",
            "username": "asmith",
            "hostname": "LAPTOP-01",
            "created_at": now - timedelta(hours=4),
            "updated_at": now - timedelta(hours=3, minutes=10),
        },
        {
            "id": 3,
            "title": "Multiple 403 responses from single IP",
            "description": "High number of forbidden responses detected from a single external IP.",
            "source": "WAF",
            "category": "Web",
            "severity": "medium",
            "status": "open",
            "url": "https://portal.waf.local",
            "sender": None,
            "username": None,
            "hostname": None,
            "created_at": now - timedelta(days=1),
            "updated_at": now - timedelta(days=1, hours=-1),
        },
    ]
    insert_if_missing(alerts_table, alerts, ["id"])

    endpoints_table = sa.table(
        "endpoints",
        sa.column("id", sa.Integer),
        sa.column("hostname", sa.String),
        sa.column("display_name", sa.String),
        sa.column("status", sa.String),
        sa.column("agent_status", sa.String),
        sa.column("agent_version", sa.String),
        sa.column("ip_address", sa.String),
        sa.column("owner", sa.String),
        sa.column("os", sa.String),
        sa.column("os_version", sa.String),
        sa.column("cpu_model", sa.String),
        sa.column("ram_gb", sa.Integer),
        sa.column("disk_gb", sa.Integer),
        sa.column("resource_usage", sa.JSON),
        sa.column("last_seen", sa.DateTime(timezone=True)),
        sa.column("location", sa.String),
        sa.column("processes", sa.JSON),
        sa.column("alerts_open", sa.Integer),
        sa.column("tags", sa.JSON),
    )

    endpoints = [
        {
            "id": 1,
            "hostname": "WIN-SEC-SRV01",
            "display_name": "WIN-SEC-SRV01",
            "status": "protected",
            "agent_status": "connected",
            "agent_version": "v2.5.1",
            "ip_address": "192.168.1.102",
            "owner": "Alex Jensen",
            "os": "Windows Server",
            "os_version": "2022 21H2",
            "cpu_model": "Intel Xeon E-2388G @ 3.20GHz",
            "ram_gb": 32,
            "disk_gb": 512,
            "resource_usage": {"cpu": 34.0, "memory": 58.0, "disk": 82.0},
            "last_seen": now,
            "location": "Data Center 01",
            "processes": [
                {"name": "svchost.exe", "pid": 1124, "user": "SYSTEM", "cpu": 5.21, "ram": 2.34},
                {"name": "chrome.exe", "pid": 8744, "user": "Administrator", "cpu": 3.88, "ram": 8.12},
                {"name": "powershell.exe", "pid": 9120, "user": "Administrator", "cpu": 1.92, "ram": 1.05},
                {"name": "sqlservr.exe", "pid": 4532, "user": "NT SERVICE\\MSSQLSERVER", "cpu": 0.87, "ram": 15.6},
            ],
            "alerts_open": 1,
            "tags": ["Critical", "Production"],
        },
        {
            "id": 2,
            "hostname": "LAPTOP-T1-DEV",
            "display_name": "Analyst Laptop",
            "status": "monitoring",
            "agent_status": "connected",
            "agent_version": "v2.4.0",
            "ip_address": "10.0.5.23",
            "owner": "Sara Patel",
            "os": "Windows 11 Pro",
            "os_version": "22H2",
            "cpu_model": "Intel i7-1185G7",
            "ram_gb": 16,
            "disk_gb": 256,
            "resource_usage": {"cpu": 41.0, "memory": 64.0, "disk": 55.0},
            "last_seen": now - timedelta(minutes=3),
            "location": "HQ SOC Floor",
            "processes": [
                {"name": "Teams.exe", "pid": 4112, "user": "Sara", "cpu": 4.2, "ram": 5.8},
                {"name": "Excel.exe", "pid": 5503, "user": "Sara", "cpu": 2.1, "ram": 3.4},
            ],
            "alerts_open": 2,
            "tags": ["Tier1"],
        },
        {
            "id": 3,
            "hostname": "LINUX-WEB-01",
            "display_name": "WEB-01",
            "status": "isolated",
            "agent_status": "disconnected",
            "agent_version": "v2.3.5",
            "ip_address": "172.16.20.14",
            "owner": "WebOps",
            "os": "Ubuntu Server",
            "os_version": "22.04",
            "cpu_model": "AMD EPYC 7502P",
            "ram_gb": 64,
            "disk_gb": 1024,
            "resource_usage": {"cpu": 12.0, "memory": 44.0, "disk": 67.0},
            "last_seen": now - timedelta(minutes=45),
            "location": "DMZ Rack 3",
            "processes": [
                {"name": "nginx", "pid": 1241, "user": "www-data", "cpu": 2.2, "ram": 1.1},
                {"name": "php-fpm", "pid": 2200, "user": "www-data", "cpu": 1.8, "ram": 2.2},
            ],
            "alerts_open": 3,
            "tags": ["DMZ", "HighTraffic"],
        },
    ]
    insert_if_missing(endpoints_table, endpoints, ["id"])
