"""add workplan items, flows, notifications, and handover fields

Revision ID: 202503110001
Revises: 202409150001
Create Date: 2025-03-11 00:01:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "202503110001"
down_revision = "202409150001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("handovers", sa.Column("analyst_user_id", sa.Integer(), nullable=True))
    op.add_column("handovers", sa.Column("notes_to_next_shift", sa.Text(), nullable=True))
    op.add_column("handovers", sa.Column("links", postgresql.JSONB(), nullable=True))
    op.add_column("handovers", sa.Column("created_by", sa.Integer(), nullable=True))
    op.add_column("handovers", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        "fk_handovers_analyst_user",
        "handovers",
        "users",
        ["analyst_user_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_handovers_created_by",
        "handovers",
        "users",
        ["created_by"],
        ["id"],
    )
    op.execute("UPDATE handovers SET notes_to_next_shift = notes WHERE notes_to_next_shift IS NULL")
    op.execute("UPDATE handovers SET updated_at = created_at WHERE updated_at IS NULL")

    op.add_column("workplans", sa.Column("owner_user_id", sa.Integer(), nullable=True))
    op.add_column("workplans", sa.Column("priority", sa.String(length=32), nullable=True))
    op.add_column("workplans", sa.Column("due_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("workplans", sa.Column("context_type", sa.String(length=64), nullable=True))
    op.add_column("workplans", sa.Column("context_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_workplans_owner_user",
        "workplans",
        "users",
        ["owner_user_id"],
        ["id"],
    )
    op.execute(
        "UPDATE workplans SET owner_user_id = assigned_to WHERE owner_user_id IS NULL AND assigned_to IS NOT NULL"
    )
    op.execute(
        "UPDATE workplans SET owner_user_id = created_by WHERE owner_user_id IS NULL"
    )
    op.execute(
        "UPDATE workplans SET context_type = 'alert', context_id = alert_id "
        "WHERE context_type IS NULL AND alert_id IS NOT NULL"
    )

    op.create_table(
        "workplan_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workplan_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("assignee_user_id", sa.Integer(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workplan_id"], ["workplans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assignee_user_id"], ["users.id"]),
    )

    op.create_table(
        "workplan_flow",
        sa.Column("workplan_id", sa.Integer(), primary_key=True),
        sa.Column("format", sa.String(length=32), nullable=False, server_default="reactflow"),
        sa.Column("nodes", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("edges", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("viewport", postgresql.JSONB(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workplan_id"], ["workplans.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "notification_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("recipient_email", sa.String(length=255), nullable=False),
        sa.Column("recipients", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("bucket_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "event_type",
            "entity_type",
            "entity_id",
            "recipient_email",
            "bucket_time",
            name="uq_notification_events_dedup",
        ),
    )

    op.create_table(
        "analytic_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default="medium"),
        sa.Column("category", sa.String(length=128), nullable=True),
        sa.Column("data_sources", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("query", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("tags", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "correlation_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default="medium"),
        sa.Column("window_minutes", sa.Integer(), nullable=True),
        sa.Column("logic", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("tags", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("correlation_rules")
    op.drop_table("analytic_rules")
    op.drop_table("notification_events")
    op.drop_table("workplan_flow")
    op.drop_table("workplan_items")

    op.drop_constraint("fk_workplans_owner_user", "workplans", type_="foreignkey")
    op.drop_column("workplans", "context_id")
    op.drop_column("workplans", "context_type")
    op.drop_column("workplans", "due_at")
    op.drop_column("workplans", "priority")
    op.drop_column("workplans", "owner_user_id")

    op.drop_constraint("fk_handovers_created_by", "handovers", type_="foreignkey")
    op.drop_constraint("fk_handovers_analyst_user", "handovers", type_="foreignkey")
    op.drop_column("handovers", "updated_at")
    op.drop_column("handovers", "created_by")
    op.drop_column("handovers", "links")
    op.drop_column("handovers", "notes_to_next_shift")
    op.drop_column("handovers", "analyst_user_id")
