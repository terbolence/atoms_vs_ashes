# man_hours: 0.3
"""Add persisted NS-07 environmental-impact tier.

Revision ID: 045
Revises: 044
Create Date: 2026-05-16
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "045"
down_revision: Union[str, None] = "044"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return insp.has_table(table) and any(c["name"] == column for c in insp.get_columns(table))


def upgrade() -> None:
    if not _column_exists("site_infrastructure_v2", "env_impact_tier"):
        op.add_column(
            "site_infrastructure_v2",
            sa.Column("env_impact_tier", sa.String(30), nullable=True),
        )


def downgrade() -> None:
    if _column_exists("site_infrastructure_v2", "env_impact_tier"):
        op.drop_column("site_infrastructure_v2", "env_impact_tier")
