"""Post-processing curation step 1 — add columns for cooling river id, NS-04
favourable area, NH-03 source split, and NH-11 annual precipitation.

Adds:
  site_infrastructure_v2.cooling_source_hyriv_id   BIGINT NULL
  site_infrastructure_v2.favourable_area_ha        NUMERIC(10,2) NULL
  site_infrastructure_v2.favourable_area_method    VARCHAR(40) NULL
  site_natural_hazards.nh03_source                 VARCHAR(40) NULL
  site_natural_hazards.mean_annual_precip_mm       NUMERIC(8,2) NULL

Revision ID: 030
Revises: 029
Create Date: 2026-04-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "030"
down_revision: Union[str, None] = "029"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("cooling_source_hyriv_id", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("favourable_area_ha", sa.Numeric(10, 2), nullable=True),
    )
    op.add_column(
        "site_infrastructure_v2",
        sa.Column("favourable_area_method", sa.String(40), nullable=True),
    )
    op.add_column(
        "site_natural_hazards",
        sa.Column("nh03_source", sa.String(40), nullable=True),
    )
    op.add_column(
        "site_natural_hazards",
        sa.Column("mean_annual_precip_mm", sa.Numeric(8, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("site_natural_hazards", "mean_annual_precip_mm")
    op.drop_column("site_natural_hazards", "nh03_source")
    op.drop_column("site_infrastructure_v2", "favourable_area_method")
    op.drop_column("site_infrastructure_v2", "favourable_area_ha")
    op.drop_column("site_infrastructure_v2", "cooling_source_hyriv_id")
