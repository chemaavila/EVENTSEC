"""add network ids, incidents, and actions

Revision ID: 202503110002
Revises: 202503110001
Create Date: 2025-03-11 00:02:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "202503110002"
down_revision = "202503110001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "detection_rules",
        sa.Column("create_incident", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    op.drop_table("network_events")

    op.create_table(
        "network_sensors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_network_sensors_name", "network_sensors", ["name"], unique=True)

    op.create_table(
        "network_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("src_ip", sa.String(length=64), nullable=True),
        sa.Column("src_port", sa.Integer(), nullable=True),
        sa.Column("dst_ip", sa.String(length=64), nullable=True),
        sa.Column("dst_port", sa.Integer(), nullable=True),
        sa.Column("proto", sa.String(length=32), nullable=True),
        sa.Column("direction", sa.String(length=32), nullable=True),
        sa.Column("sensor_id", sa.Integer(), nullable=True),
        sa.Column("signature", sa.String(length=255), nullable=True),
        sa.Column("category", sa.String(length=128), nullable=True),
        sa.Column("severity", sa.Integer(), nullable=True),
        sa.Column("flow_id", sa.String(length=128), nullable=True),
        sa.Column("uid", sa.String(length=128), nullable=True),
        sa.Column("community_id", sa.String(length=128), nullable=True),
        sa.Column("http_host", sa.String(length=255), nullable=True),
        sa.Column("http_url", sa.String(length=512), nullable=True),
        sa.Column("http_method", sa.String(length=32), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("dns_query", sa.String(length=255), nullable=True),
        sa.Column("dns_type", sa.String(length=64), nullable=True),
        sa.Column("dns_rcode", sa.String(length=64), nullable=True),
        sa.Column("tls_sni", sa.String(length=255), nullable=True),
        sa.Column("tls_ja3", sa.String(length=128), nullable=True),
        sa.Column("tls_version", sa.String(length=64), nullable=True),
        sa.Column("tags", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("raw", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["sensor_id"], ["network_sensors.id"]),
    )

    op.create_table(
        "network_ingest_errors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("sensor_name", sa.String(length=128), nullable=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("raw_snippet", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "response_actions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=True),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("target", sa.String(length=255), nullable=False),
        sa.Column("ttl_minutes", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="requested"),
        sa.Column("requested_by", sa.Integer(), nullable=True),
        sa.Column("details", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"]),
    )

    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="new"),
        sa.Column("assigned_to", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("tags", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
    )

    op.create_table(
        "incident_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("incident_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("ref_id", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("incident_items")
    op.drop_table("incidents")
    op.drop_table("response_actions")
    op.drop_table("network_ingest_errors")
    op.drop_table("network_events")
    op.drop_index("ix_network_sensors_name", table_name="network_sensors")
    op.drop_table("network_sensors")

    op.create_table(
        "network_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hostname", sa.String(length=128), nullable=False),
        sa.Column("username", sa.String(length=128), nullable=False),
        sa.Column("url", sa.String(length=512), nullable=False),
        sa.Column("verdict", sa.String(length=32), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.drop_column("detection_rules", "create_incident")
