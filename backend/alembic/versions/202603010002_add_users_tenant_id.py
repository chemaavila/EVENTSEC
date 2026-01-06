"""add tenant_id to users

Revision ID: 202603010002
Revises: 202603010001
Create Date: 2026-03-01 00:02:00.000000
"""

from __future__ import annotations

from alembic import op


revision = "202603010002"
down_revision = "202603010001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Idempotent migration for persisted volumes and concurrent runs."""
    # Use raw SQL for Postgres-safe IF NOT EXISTS / IF EXISTS support.
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(64)")
    op.execute("ALTER TABLE users ALTER COLUMN tenant_id SET DEFAULT 'default'")
    op.execute("UPDATE users SET tenant_id='default' WHERE tenant_id IS NULL")
    op.execute("ALTER TABLE users ALTER COLUMN tenant_id SET NOT NULL")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_tenant_id ON users (tenant_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_users_tenant_id")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS tenant_id")
