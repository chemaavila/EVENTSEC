"""add tenant_id to users

Revision ID: 202603010001
Revises: 202601050001
Create Date: 2026-03-01 00:01:00.000000
"""

from __future__ import annotations

from alembic import context, op
import sqlalchemy as sa


revision = "202603010001"
down_revision = "202601050001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if context.is_offline_mode():
        op.execute(
            "ALTER TABLE IF EXISTS public.users "
            "ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(64) "
            "NOT NULL DEFAULT 'default'"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_users_tenant_id "
            "ON public.users (tenant_id)"
        )
        return

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "tenant_id" not in columns:
        op.add_column(
            "users",
            sa.Column(
                "tenant_id",
                sa.String(length=64),
                nullable=False,
                server_default="default",
            ),
        )

    index_names = {index["name"] for index in inspector.get_indexes("users")}
    if "ix_users_tenant_id" not in index_names:
        op.create_index("ix_users_tenant_id", "users", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_users_tenant_id", table_name="users")
    op.drop_column("users", "tenant_id")
