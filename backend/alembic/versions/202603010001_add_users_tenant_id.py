"""add tenant_id to users

Revision ID: 202603010001
Revises: 202601050001
Create Date: 2026-03-01 00:01:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "202603010001"
down_revision = "202601050001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "tenant_id",
            sa.String(length=64),
            nullable=False,
            server_default="default",
        ),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_users_tenant_id", table_name="users")
    op.drop_column("users", "tenant_id")
