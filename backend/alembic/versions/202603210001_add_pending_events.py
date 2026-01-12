"""add pending events table

Revision ID: 202603210001
Revises: 202603200001
Create Date: 2026-03-21 00:01:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "202603210001"
down_revision = "202603200001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pending_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "event_id",
            sa.Integer(),
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.create_index(
        "ix_pending_events_event_id",
        "pending_events",
        ["event_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_pending_events_event_id", table_name="pending_events")
    op.drop_table("pending_events")
