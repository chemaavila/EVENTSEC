"""add password guard events and audit

Revision ID: 202603010003
Revises: 202601050001
Create Date: 2026-03-01 00:01:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "202603010003"
down_revision = "202601050001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "password_guard_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("host_id", sa.String(length=128), nullable=False),
        sa.Column("user", sa.String(length=255), nullable=False),
        sa.Column("entry_id", sa.String(length=128), nullable=False),
        sa.Column("entry_label", sa.String(length=255), nullable=False),
        sa.Column("exposure_count", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("event_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("client_version", sa.String(length=64), nullable=False),
        sa.Column("alert_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"]),
    )
    op.create_index(
        "ix_password_guard_events_action",
        "password_guard_events",
        ["action"],
    )
    op.create_index(
        "ix_password_guard_events_entry_id",
        "password_guard_events",
        ["entry_id"],
    )
    op.create_index(
        "ix_password_guard_events_host_id",
        "password_guard_events",
        ["host_id"],
    )
    op.create_index(
        "ix_password_guard_events_tenant_id",
        "password_guard_events",
        ["tenant_id"],
    )
    op.create_index(
        "ix_password_guard_events_user",
        "password_guard_events",
        ["user"],
    )

    op.create_table(
        "password_guard_ingest_audit",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("ingested_by_user_id", sa.Integer(), nullable=True),
        sa.Column("agent_id", sa.Integer(), nullable=True),
        sa.Column("token_id", sa.String(length=128), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["event_id"], ["password_guard_events.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["ingested_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
    )
    op.create_index(
        "ix_password_guard_ingest_audit_tenant_id",
        "password_guard_ingest_audit",
        ["tenant_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_password_guard_ingest_audit_tenant_id",
        table_name="password_guard_ingest_audit",
    )
    op.drop_table("password_guard_ingest_audit")
    op.drop_index(
        "ix_password_guard_events_user",
        table_name="password_guard_events",
    )
    op.drop_index(
        "ix_password_guard_events_tenant_id",
        table_name="password_guard_events",
    )
    op.drop_index(
        "ix_password_guard_events_host_id",
        table_name="password_guard_events",
    )
    op.drop_index(
        "ix_password_guard_events_entry_id",
        table_name="password_guard_events",
    )
    op.drop_index(
        "ix_password_guard_events_action",
        table_name="password_guard_events",
    )
    op.drop_table("password_guard_events")
