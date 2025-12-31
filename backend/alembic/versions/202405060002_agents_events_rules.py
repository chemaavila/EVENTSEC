"""agent registry, events, detection rules

Revision ID: 202405060002
Revises: 202405060001
Create Date: 2024-05-06 01:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "202405060002"
down_revision = "202405060001"
branch_labels = None
depends_on = None


def jsonb():
    return postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.add_column(
        "agents",
        sa.Column("api_key", sa.String(length=64), nullable=False, server_default=""),
    )
    op.add_column("agents", sa.Column("last_seen", sa.DateTime(timezone=True)))
    op.add_column("agents", sa.Column("last_ip", sa.String(length=64)))
    op.alter_column("agents", "api_key", server_default=None)
    op.create_unique_constraint("uq_agents_api_key", "agents", ["api_key"])

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "agent_id", sa.Integer(), sa.ForeignKey("agents.id", ondelete="SET NULL")
        ),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("category", sa.String(length=128)),
        sa.Column(
            "details", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "detection_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column(
            "enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "conditions", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("detection_rules")
    op.drop_table("events")
    op.drop_constraint("uq_agents_api_key", "agents", type_="unique")
    op.drop_column("agents", "last_ip")
    op.drop_column("agents", "last_seen")
    op.drop_column("agents", "api_key")
