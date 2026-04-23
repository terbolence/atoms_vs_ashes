"""Add 'not_assessed' to screening_verdict enum.

Used by the sequential elimination strategy: when a site is excluded by
an earlier exclusionary criterion, remaining criteria are marked
not_assessed with justification citing the failing criterion.

Revision ID: 009
Revises: 008
Create Date: 2026-04-13
"""
from typing import Sequence, Union

from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE screening_verdict ADD VALUE IF NOT EXISTS 'not_assessed'")


def downgrade() -> None:
    pass
