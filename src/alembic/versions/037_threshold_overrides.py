# man_hours: 1.0
"""Create threshold_overrides table for GUI / DB-backed fail-threshold edits.

Revision ID: 037
Revises: 036
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "037"
down_revision: Union[str, None] = "036"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "threshold_overrides",
        sa.Column("criterion_id", sa.String(20), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column(
            "smr_key",
            sa.String(30),
            nullable=False,
            server_default="",
        ),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_by", sa.String(200), nullable=True),
        sa.PrimaryKeyConstraint("criterion_id", "code", "smr_key"),
    )
    op.create_index(
        "ix_threshold_overrides_smr_key",
        "threshold_overrides",
        ["smr_key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_threshold_overrides_smr_key", table_name="threshold_overrides")
    op.drop_table("threshold_overrides")
