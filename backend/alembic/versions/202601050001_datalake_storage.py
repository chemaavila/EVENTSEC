"""add datalake storage policy tables

Revision ID: 202601050001
Revises: 202503110002
Create Date: 2026-01-05 15:28:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "202601050001"
down_revision = "202503110002"
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

    op.create_table(
        "tenant_storage_policy",
        sa.Column("tenant_id", sa.String(length=64), primary_key=True),
        sa.Column("data_lake_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("hot_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("cold_days", sa.Integer(), nullable=False, server_default="365"),
        sa.Column("sampling_policy", sa.String(length=64), nullable=False, server_default="none"),
        sa.Column("dedup_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("legal_hold", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "tenant_usage_daily",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("bytes_ingested", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("docs_ingested", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("query_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hot_est", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("cold_est", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_tenant_usage_daily_tenant_id_day",
        "tenant_usage_daily",
        ["tenant_id", "day"],
    )

    op.create_table(
        "rehydration_jobs",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("dataset", sa.String(length=128), nullable=False),
        sa.Column("time_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("time_to", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("case_id", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="requested"),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ttl_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
    )
    op.create_index(
        "ix_rehydration_jobs_tenant_status",
        "rehydration_jobs",
        ["tenant_id", "status"],
    )

    op.create_table(
        "cold_objects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("dataset", sa.String(length=128), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("object_key", sa.String(length=512), nullable=False),
        sa.Column("bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_cold_objects_tenant_dataset_day",
        "cold_objects",
        ["tenant_id", "dataset", "day"],
    )


def downgrade() -> None:
    op.drop_index("ix_cold_objects_tenant_dataset_day", table_name="cold_objects")
    op.drop_table("cold_objects")

    op.drop_index("ix_rehydration_jobs_tenant_status", table_name="rehydration_jobs")
    op.drop_table("rehydration_jobs")

    op.drop_index("ix_tenant_usage_daily_tenant_id_day", table_name="tenant_usage_daily")
    op.drop_table("tenant_usage_daily")

    op.drop_table("tenant_storage_policy")

    op.drop_index("ix_users_tenant_id", table_name="users")
    op.drop_column("users", "tenant_id")
