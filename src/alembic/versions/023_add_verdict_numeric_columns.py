"""Add numeric companion columns to screening_verdicts.

Addresses audit finding W-05: measured_value and threshold were stored
as TEXT (e.g. "7.48 km", "≥2 km from protected areas"), making them
unusable for aggregation and regression.

Also adds missing index on criterion_id (W-15).

Revision ID: 023
Revises: 022
Create Date: 2026-04-16
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "023"
down_revision: Union[str, None] = "022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "screening_verdicts",
        sa.Column("measured_value_numeric", sa.Numeric(), nullable=True),
    )
    op.add_column(
        "screening_verdicts",
        sa.Column("threshold_numeric", sa.Numeric(), nullable=True),
    )
    op.add_column(
        "screening_verdicts",
        sa.Column("measured_units", sa.String(20), nullable=True),
    )
    op.create_index(
        "ix_verdict_criterion_id", "screening_verdicts", ["criterion_id"]
    )

    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE screening_verdicts
        SET measured_value_numeric = (
                regexp_replace(measured_value, '[^0-9.]', '', 'g')
            )::numeric,
            measured_units = CASE
                WHEN measured_value LIKE '%%km%%' THEN 'km'
                WHEN measured_value LIKE '%%ha%%' THEN 'ha'
                WHEN measured_value LIKE '%%MWe%%' OR measured_value LIKE '%%MW%%' THEN 'MWe'
                WHEN measured_value LIKE '%%g%%' THEN 'g'
                ELSE NULL
            END
        WHERE measured_value IS NOT NULL
          AND regexp_replace(measured_value, '[^0-9.]', '', 'g') ~ '^[0-9]+\\.?[0-9]*$'
    """))


def downgrade() -> None:
    op.drop_index("ix_verdict_criterion_id", table_name="screening_verdicts")
    op.drop_column("screening_verdicts", "measured_units")
    op.drop_column("screening_verdicts", "threshold_numeric")
    op.drop_column("screening_verdicts", "measured_value_numeric")
