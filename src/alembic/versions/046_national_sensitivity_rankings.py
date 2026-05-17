# man_hours: 0.8
"""Persist national sensitivity ranking analytics.

Adds national-rank sensitivity artefacts for Phase 1.6 without changing
the existing regional ``composite_rankings`` semantics.

Revision ID: 046
Revises: 045
Create Date: 2026-05-16
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

from atoms_vs_ashes.db.migrations import _046_national_sensitivity as national

revision: str = "046"
down_revision: Union[str, None] = "045"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_DROP_ORDER = (
    "national_mc_rank_distribution",
    "national_sensitivity_summary",
    "national_rank_sensitivity",
)


def upgrade() -> None:
    national.create_national_rank_sensitivity()
    national.create_national_sensitivity_summary()
    national.create_national_mc_rank_distribution()


def downgrade() -> None:
    for table in _DROP_ORDER:
        op.drop_table(table)
