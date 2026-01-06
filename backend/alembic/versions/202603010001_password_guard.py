"""password guard migration (recovered)

Revision ID: 202603010001
Revises: 202601050001
Create Date: 2026-03-01 00:01:00.000000
"""

from __future__ import annotations

from alembic import op

revision = "202603010001"
down_revision = "202601050001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No-op: recovered migration contained no schema operations.
    pass


def downgrade() -> None:
    pass
