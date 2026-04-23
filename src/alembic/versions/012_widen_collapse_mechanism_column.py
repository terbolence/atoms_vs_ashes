"""Widen collapse_mechanism column from VARCHAR(100) to VARCHAR(500).

LLM responses can produce longer mechanism descriptions than 100 characters.

Revision ID: 012
Revises: 011
Create Date: 2026-04-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "site_natural_hazards",
        "collapse_mechanism",
        type_=sa.String(500),
        existing_type=sa.String(100),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "site_natural_hazards",
        "collapse_mechanism",
        type_=sa.String(100),
        existing_type=sa.String(500),
        existing_nullable=True,
    )
