"""inventory snapshots, vulnerability, sca results

Revision ID: 202405060003
Revises: 202405060002
Create Date: 2024-05-06 01:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "202405060003"
down_revision = "202405060002"
branch_labels = None
depends_on = None


def jsonb():
    return postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "inventory_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "agent_id",
            sa.Integer(),
            sa.ForeignKey("agents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column(
            "data", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "vulnerability_definitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cve_id", sa.String(length=32), nullable=False, unique=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column(
            "affected_products",
            jsonb(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "sca_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "agent_id",
            sa.Integer(),
            sa.ForeignKey("agents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("policy_id", sa.String(length=128), nullable=False),
        sa.Column("policy_name", sa.String(length=255), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'unknown'"),
        ),
        sa.Column(
            "passed_checks", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "failed_checks", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "details", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "agent_vulnerabilities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "agent_id",
            sa.Integer(),
            sa.ForeignKey("agents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "definition_id",
            sa.Integer(),
            sa.ForeignKey("vulnerability_definitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'open'"),
        ),
        sa.Column(
            "evidence", jsonb(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
    )
    op.create_unique_constraint(
        "uq_agent_definition",
        "agent_vulnerabilities",
        ["agent_id", "definition_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_agent_definition", "agent_vulnerabilities", type_="unique")
    op.drop_table("agent_vulnerabilities")
    op.drop_table("sca_results")
    op.drop_table("vulnerability_definitions")
    op.drop_table("inventory_snapshots")
