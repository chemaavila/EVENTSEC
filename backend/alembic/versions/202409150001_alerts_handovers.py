"""add alert assignment fields and handovers

Revision ID: 202409150001
Revises: 202405060003
Create Date: 2024-09-15 00:01:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "202409150001"
down_revision = "202405060003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("alerts", sa.Column("assigned_to", sa.Integer(), nullable=True))
    op.add_column("alerts", sa.Column("conclusion", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_alerts_assigned_to_users",
        "alerts",
        "users",
        ["assigned_to"],
        ["id"],
    )

    op.create_table(
        "handovers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("shift_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("shift_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("analyst", sa.String(length=128), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("alerts_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("handovers")
    op.drop_constraint("fk_alerts_assigned_to_users", "alerts", type_="foreignkey")
    op.drop_column("alerts", "conclusion")
    op.drop_column("alerts", "assigned_to")
