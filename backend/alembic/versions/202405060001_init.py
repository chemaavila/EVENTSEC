"""initial database schema

Revision ID: 202405060001
Revises:
Create Date: 2024-05-06 00:01:00.000000
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from passlib.context import CryptContext


revision = "202405060001"
down_revision = None
branch_labels = None
depends_on = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def jsonb():
    return postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("avatar_url", sa.String(length=512)),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Europe/Madrid"),
        sa.Column("team", sa.String(length=128)),
        sa.Column("manager", sa.String(length=128)),
        sa.Column("computer", sa.String(length=128)),
        sa.Column("mobile_phone", sa.String(length=64)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "agents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False, unique=True),
        sa.Column("os", sa.String(length=64), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="offline"),
        sa.Column("last_heartbeat", sa.DateTime(timezone=True)),
        sa.Column("version", sa.String(length=32)),
        sa.Column("tags", jsonb(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=128), nullable=False),
        sa.Column("category", sa.String(length=128), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("url", sa.String(length=512)),
        sa.Column("sender", sa.String(length=255)),
        sa.Column("username", sa.String(length=255)),
        sa.Column("hostname", sa.String(length=255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id")),
    )

    op.create_table(
        "workplans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("alert_id", sa.Integer(), sa.ForeignKey("alerts.id")),
        sa.Column("assigned_to", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "workgroups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("members", jsonb(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "warroom_notes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("alert_id", sa.Integer(), sa.ForeignKey("alerts.id", ondelete="CASCADE")),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("attachments", jsonb(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "alert_escalations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("alert_id", sa.Integer(), sa.ForeignKey("alerts.id", ondelete="CASCADE")),
        sa.Column("escalated_to", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("escalated_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("reason", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "action_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("action_type", sa.String(length=128), nullable=False),
        sa.Column("target_type", sa.String(length=128), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("parameters", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "sandbox_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("value", sa.String(length=512), nullable=False),
        sa.Column("filename", sa.String(length=255)),
        sa.Column("verdict", sa.String(length=64), nullable=False),
        sa.Column("threat_type", sa.String(length=255)),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("file_hash", sa.String(length=255)),
        sa.Column("iocs", jsonb(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("endpoints", jsonb(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("vt_results", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("osint_results", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("yara_matches", jsonb(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "indicators",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("value", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=128), nullable=False),
        sa.Column("tags", jsonb(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "bioc_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("platform", sa.String(length=64), nullable=False),
        sa.Column("tactic", sa.String(length=64), nullable=False),
        sa.Column("technique", sa.String(length=64)),
        sa.Column("detection_logic", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("tags", jsonb(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="enabled"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "analytics_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("datasource", sa.String(length=128), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="enabled"),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("owner", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "endpoints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hostname", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("agent_status", sa.String(length=32), nullable=False),
        sa.Column("agent_version", sa.String(length=32), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=False),
        sa.Column("owner", sa.String(length=128), nullable=False),
        sa.Column("os", sa.String(length=64), nullable=False),
        sa.Column("os_version", sa.String(length=64), nullable=False),
        sa.Column("cpu_model", sa.String(length=128), nullable=False),
        sa.Column("ram_gb", sa.Integer(), nullable=False),
        sa.Column("disk_gb", sa.Integer(), nullable=False),
        sa.Column("resource_usage", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location", sa.String(length=128), nullable=False),
        sa.Column("processes", jsonb(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("alerts_open", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tags", jsonb(), nullable=False, server_default=sa.text("'[]'::jsonb")),
    )

    op.create_table(
        "endpoint_actions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("endpoint_id", sa.Integer(), sa.ForeignKey("endpoints.id")),
        sa.Column("action_type", sa.String(length=32), nullable=False),
        sa.Column("parameters", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("requested_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("output", sa.Text()),
    )

    op.create_table(
        "network_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hostname", sa.String(length=128), nullable=False),
        sa.Column("username", sa.String(length=128), nullable=False),
        sa.Column("url", sa.String(length=512), nullable=False),
        sa.Column("verdict", sa.String(length=32), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    seed_data()


def seed_data() -> None:
    connection = op.get_bind()
    now = datetime.now(timezone.utc)

    admin_hash = pwd_context.hash("Admin123!")
    analyst_hash = pwd_context.hash("Analyst123!")
    connection.execute(
        sa.text(
            """
            INSERT INTO users (id, full_name, role, email, hashed_password, timezone, team, manager, computer, mobile_phone, created_at, updated_at)
            VALUES
            (1, 'Admin User', 'admin', 'admin@example.com', :admin_pw, 'Europe/Madrid', 'Management', NULL, 'ADMIN-PC-01', '+1234567890', :now, :now),
            (2, 'SOC Analyst', 'analyst', 'analyst@example.com', :analyst_pw, 'Europe/Madrid', 'SOC Team 1', 'Admin User', 'ANALYST-PC-01', '+1234567891', :now, :now)
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {"admin_pw": admin_hash, "analyst_pw": analyst_hash, "now": now},
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
    op.bulk_insert(
        sa.table(
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
        ),
        alerts,
    )


def downgrade() -> None:
    op.drop_table("network_events")
    op.drop_table("endpoint_actions")
    op.drop_table("endpoints")
    op.drop_table("analytics_rules")
    op.drop_table("bioc_rules")
    op.drop_table("indicators")
    op.drop_table("sandbox_results")
    op.drop_table("action_logs")
    op.drop_table("alert_escalations")
    op.drop_table("warroom_notes")
    op.drop_table("workgroups")
    op.drop_table("workplans")
    op.drop_table("alerts")
    op.drop_table("agents")
    op.drop_table("users")

