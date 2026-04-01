# man_hours: 1.0
"""Seed screening criteria — BF-02 Land Area Basic Filter.

Revision ID: 003
Revises: 002
Create Date: 2026-03-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CRITERIA = [
    {
        "criterion_id": "BF-02",
        "name": "Land Area Basic Filter",
        "category": "basic_filter",
        "phase": "screening",
        "weight": None,
        "iaea_reference": "IAEA NS-R-3 Rev.1, SSG-35 Annex II",
        "epri_reference": "EPRI coal-to-nuclear criteria A15",
        "description": (
            "Checks whether the site's available land area (from OSM plant "
            "boundary measurement) can accommodate one or more reference SMR "
            "designs.  Sites below 22 ha (minimum: Oklo Aurora full-project "
            "footprint) are marked as fail.  The 14 ha nuclear-island minimum "
            "from A15 is subsumed by the full project land requirements."
        ),
    },
]


def upgrade() -> None:
    criteria = sa.table(
        "criteria",
        sa.column("criterion_id", sa.String),
        sa.column("name", sa.String),
        sa.column("category", sa.String),
        sa.column("phase", sa.String),
        sa.column("weight", sa.Numeric),
        sa.column("iaea_reference", sa.String),
        sa.column("epri_reference", sa.String),
        sa.column("description", sa.Text),
    )
    op.bulk_insert(criteria, CRITERIA)


def downgrade() -> None:
    op.execute("DELETE FROM criteria WHERE criterion_id = 'BF-02'")
