"""Add nh07_hazard_class column to site_natural_hazards.

Stores the volcano hazard classification (negligible / low / avoidance /
exclusionary) as a proper typed column instead of buried in nh07_comment
text.  Backfills from existing nh07_comment where available.

Revision ID: 028
Revises: 027
Create Date: 2026-04-18
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "028"
down_revision: Union[str, None] = "027"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "site_natural_hazards",
        sa.Column("nh07_hazard_class", sa.String(30), nullable=True),
    )

    # Backfill from nh07_comment where the pattern 'hazard_class=<value>' exists
    op.execute(
        sa.text("""
            UPDATE site_natural_hazards
            SET nh07_hazard_class = substring(nh07_comment FROM 'hazard_class=([a-z]+)')
            WHERE nh07_comment IS NOT NULL
              AND nh07_comment LIKE 'hazard_class=%'
              AND nh07_hazard_class IS NULL
        """)
    )


def downgrade() -> None:
    op.drop_column("site_natural_hazards", "nh07_hazard_class")
