"""vuln intel inventory tables

Revision ID: 202603120001
Revises: 202601050001
Create Date: 2025-03-12 00:01:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "202603120001"
down_revision = "202601050001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "software_components",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("version", sa.String(length=128), nullable=False),
        sa.Column("vendor", sa.String(length=255), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=True),
        sa.Column("purl", sa.String(length=512), nullable=True),
        sa.Column("cpe", sa.String(length=512), nullable=True),
        sa.Column("raw", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["agents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "asset_id",
            "name",
            "version",
            "vendor",
            name="uq_software_component_identity",
        ),
    )
    op.create_index(
        "ix_software_components_asset_tenant",
        "software_components",
        ["tenant_id", "asset_id"],
        unique=False,
    )
    op.create_index(
        "ix_software_components_cpe", "software_components", ["cpe"], unique=False
    )
    op.create_index(
        "ix_software_components_purl", "software_components", ["purl"], unique=False
    )
    op.create_index(
        "ix_software_components_collected_at",
        "software_components",
        ["collected_at"],
        unique=False,
    )
    op.create_index(
        "ix_software_components_last_seen_at",
        "software_components",
        ["last_seen_at"],
        unique=False,
    )

    op.create_table(
        "vulnerabilities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("cve_id", sa.String(length=32), nullable=True),
        sa.Column("osv_id", sa.String(length=64), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("cvss_score", sa.Float(), nullable=True),
        sa.Column("cvss_vector", sa.String(length=255), nullable=True),
        sa.Column("epss_score", sa.Float(), nullable=True),
        sa.Column("kev", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("modified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("references", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_vulnerabilities_cve_id", "vulnerabilities", ["cve_id"], unique=False
    )
    op.create_index(
        "ix_vulnerabilities_epss_score",
        "vulnerabilities",
        ["epss_score"],
        unique=False,
    )
    op.create_index(
        "ix_vulnerabilities_kev", "vulnerabilities", ["kev"], unique=False
    )
    op.create_index(
        "ix_vulnerabilities_osv_id", "vulnerabilities", ["osv_id"], unique=False
    )

    op.create_table(
        "asset_vulnerabilities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("software_component_id", sa.Integer(), nullable=False),
        sa.Column("vulnerability_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("risk_label", sa.String(length=16), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notified_risk_label", sa.String(length=16), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["software_component_id"], ["software_components.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["vulnerability_id"], ["vulnerabilities.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "asset_id",
            "software_component_id",
            "vulnerability_id",
            name="uq_asset_vuln_identity",
        ),
    )
    op.create_index(
        "ix_asset_vuln_risk_label",
        "asset_vulnerabilities",
        ["risk_label"],
        unique=False,
    )
    op.create_index(
        "ix_asset_vuln_tenant_asset",
        "asset_vulnerabilities",
        ["tenant_id", "asset_id"],
        unique=False,
    )
    op.create_index(
        "ix_asset_vulnerabilities_last_seen_at",
        "asset_vulnerabilities",
        ["last_seen_at"],
        unique=False,
    )

    op.create_table(
        "vuln_intel_cache",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cache_key", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cache_key"),
    )
    op.create_index(
        "ix_vuln_intel_cache_expires_at",
        "vuln_intel_cache",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        "ix_vuln_intel_cache_key",
        "vuln_intel_cache",
        ["cache_key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_vuln_intel_cache_key", table_name="vuln_intel_cache")
    op.drop_index("ix_vuln_intel_cache_expires_at", table_name="vuln_intel_cache")
    op.drop_table("vuln_intel_cache")

    op.drop_index("ix_asset_vulnerabilities_last_seen_at", table_name="asset_vulnerabilities")
    op.drop_index("ix_asset_vuln_tenant_asset", table_name="asset_vulnerabilities")
    op.drop_index("ix_asset_vuln_risk_label", table_name="asset_vulnerabilities")
    op.drop_table("asset_vulnerabilities")

    op.drop_index("ix_vulnerabilities_osv_id", table_name="vulnerabilities")
    op.drop_index("ix_vulnerabilities_kev", table_name="vulnerabilities")
    op.drop_index("ix_vulnerabilities_epss_score", table_name="vulnerabilities")
    op.drop_index("ix_vulnerabilities_cve_id", table_name="vulnerabilities")
    op.drop_table("vulnerabilities")

    op.drop_index("ix_software_components_last_seen_at", table_name="software_components")
    op.drop_index("ix_software_components_collected_at", table_name="software_components")
    op.drop_index("ix_software_components_purl", table_name="software_components")
    op.drop_index("ix_software_components_cpe", table_name="software_components")
    op.drop_index("ix_software_components_asset_tenant", table_name="software_components")
    op.drop_table("software_components")
