"""Add observation_class column to site_observations.

Addresses audit finding W-02: the source_type field alone did not
distinguish the semantic role of an observation (machine explanation
vs analyst note vs review comment vs connector warning).

Revision ID: 024
Revises: 023
Create Date: 2026-04-16
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "024"
down_revision: Union[str, None] = "023"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "site_observations",
        sa.Column("observation_class", sa.String(30), nullable=True),
    )

    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE site_observations
        SET observation_class = CASE
            WHEN source_type IN ('api', 'bulk_csv', 'raster', 'vector')
                THEN 'machine_explanation'
            WHEN source_type = 'llm'
                THEN 'machine_explanation'
            WHEN source_type = 'llm_error_migrated'
                THEN 'connector_warning'
            WHEN source_type IN ('expert', 'manual')
                THEN 'analyst_note'
            ELSE 'machine_explanation'
        END
        WHERE observation_class IS NULL
    """))


def downgrade() -> None:
    op.drop_column("site_observations", "observation_class")
