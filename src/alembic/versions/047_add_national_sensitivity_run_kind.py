# man_hours: 0.4
"""Add national_sensitivity run kind.

Revision ID: 047
Revises: 046
Create Date: 2026-05-17
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "047"
down_revision: Union[str, None] = "046"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE run_kind ADD VALUE IF NOT EXISTS 'national_sensitivity'")


def downgrade() -> None:
    # PostgreSQL cannot drop enum values safely while rows or defaults may
    # reference them. Keep downgrade non-destructive.
    pass
