"""merge heads after tenant/password/vuln intel branches

Revision ID: 202603120002
Revises: 202603010002, 202603010003, 202603120001
Create Date: 2026-03-12 00:02:00.000000
"""

from __future__ import annotations

from alembic import op  # noqa: F401


revision = "202603120002"
down_revision = ("202603010002", "202603010003", "202603120001")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
