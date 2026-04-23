"""Add nh05b_quality/nh05b_comment columns and 'deferred' verdict enum value.

NH-05 (karst) and NH-05b (subsidence) previously shared a single quality column.
This migration adds dedicated columns for NH-05b and extends the screening_verdict
enum with 'deferred' for criteria that require API enrichment data before LLM
assessment is worthwhile.

Revision ID: 010
Revises: 009
Create Date: 2026-04-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "site_natural_hazards",
        sa.Column("nh05b_quality", sa.String(20), nullable=True),
    )
    op.add_column(
        "site_natural_hazards",
        sa.Column("nh05b_comment", sa.Text(), nullable=True),
    )

    op.execute("ALTER TYPE screening_verdict ADD VALUE IF NOT EXISTS 'deferred'")


def downgrade() -> None:
    op.drop_column("site_natural_hazards", "nh05b_comment")
    op.drop_column("site_natural_hazards", "nh05b_quality")
