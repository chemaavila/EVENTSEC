"""add owner scoping for intel and sandbox results

Revision ID: 202603150001
Revises: 202603120002
Create Date: 2026-03-15 00:01:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "202603150001"
down_revision = "202603120002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sandbox_results",
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.add_column(
        "indicators",
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.add_column(
        "bioc_rules",
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("bioc_rules", "owner_id")
    op.drop_column("indicators", "owner_id")
    op.drop_column("sandbox_results", "owner_id")
