"""add triage results

Revision ID: 202603200001
Revises: 202603150001
Create Date: 2025-03-20 00:01:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "202603200001"
down_revision = "202603150001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "triage_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("endpoint_id", sa.Integer(), sa.ForeignKey("endpoints.id"), nullable=False),
        sa.Column("agent_id", sa.Integer(), sa.ForeignKey("agents.id"), nullable=True),
        sa.Column("action_id", sa.Integer(), sa.ForeignKey("endpoint_actions.id"), nullable=True),
        sa.Column("summary", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("report", sa.JSON(), nullable=True),
        sa.Column("artifact_name", sa.String(length=255), nullable=True),
        sa.Column("artifact_zip_base64", sa.Text(), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("triage_results")
