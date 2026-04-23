"""Widen karst_formation_type column from VARCHAR(100) to VARCHAR(200).

Revision ID: 013
Revises: 012
Create Date: 2026-04-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "site_natural_hazards",
        "karst_formation_type",
        type_=sa.String(200),
        existing_type=sa.String(100),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "site_natural_hazards",
        "karst_formation_type",
        type_=sa.String(100),
        existing_type=sa.String(200),
        existing_nullable=True,
    )
