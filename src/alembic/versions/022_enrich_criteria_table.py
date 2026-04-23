"""Enrich criteria table with operational metadata.

Addresses audit finding W-10: the criteria table lacked threshold
expressions, units, expected value types, domain table column mappings,
and source priorities.  These were hardcoded across connector code and
config YAML.

Revision ID: 022
Revises: 021
Create Date: 2026-04-16
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from alembic import op

revision: str = "022"
down_revision: Union[str, None] = "021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "criteria",
        sa.Column("criterion_class", sa.String(30), nullable=True),
    )
    op.add_column(
        "criteria",
        sa.Column("threshold_expression", sa.Text(), nullable=True),
    )
    op.add_column(
        "criteria",
        sa.Column("units", sa.String(30), nullable=True),
    )
    op.add_column(
        "criteria",
        sa.Column("value_type", sa.String(20), nullable=True),
    )
    op.add_column(
        "criteria",
        sa.Column("domain_table", sa.String(50), nullable=True),
    )
    op.add_column(
        "criteria",
        sa.Column("domain_column_prefix", sa.String(20), nullable=True),
    )
    op.add_column(
        "criteria",
        sa.Column("source_priority", JSONB(), nullable=True),
    )

    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE criteria SET
            criterion_class = CASE
                WHEN criterion_id IN ('BF-01','BF-02') THEN 'basic_filter'
                WHEN criterion_id LIKE 'E%%' THEN 'exclusionary'
                WHEN phase = 'screening' THEN 'exclusionary'
                WHEN phase = 'ranking' THEN 'ranking'
                ELSE 'ranking'
            END,
            domain_table = CASE
                WHEN criterion_id LIKE 'NH-%%' THEN 'site_natural_hazards'
                WHEN criterion_id LIKE 'HI-%%' THEN 'site_human_hazards'
                WHEN criterion_id LIKE 'RI-%%' THEN 'site_radiological'
                WHEN criterion_id LIKE 'EP-%%' THEN 'site_emergency_planning'
                WHEN criterion_id LIKE 'NS-%%' THEN 'site_infrastructure_v2'
                WHEN criterion_id LIKE 'BF-%%' THEN 'sites'
                ELSE NULL
            END,
            domain_column_prefix = CASE
                WHEN criterion_id = 'BF-01' THEN 'grid'
                WHEN criterion_id = 'BF-02' THEN 'site_area'
                ELSE lower(replace(criterion_id, '-', ''))
            END
    """))

    _seed_thresholds(conn)


def _seed_thresholds(conn):
    """Seed threshold_expression and units for key criteria."""
    data = [
        ("BF-01", ">= SMR net output MWe", "MWe", "numeric"),
        ("BF-02", ">= nuclear island requirement ha", "ha", "numeric"),
        ("NH-01", "PGA thresholds per SSG-35", "g", "numeric"),
        ("NH-02", ">= 8 km from capable fault", "km", "numeric"),
        ("NH-03", "not high susceptibility", None, "text"),
        ("NH-04", "< 15 deg slope", "deg", "numeric"),
        ("NH-05", "no massive karst at site", None, "boolean"),
        ("NH-07", ">= 40 km from Holocene volcano", "km", "numeric"),
        ("NH-08", "> 1 km from coast or adequate protection", "km", "numeric"),
        ("NH-09", "not in high-risk flood zone", None, "text"),
        ("HI-01", ">= 8 km from large airport", "km", "numeric"),
        ("HI-02", ">= 5 km from Seveso site", "km", "numeric"),
        ("HI-06", ">= 10 km from military installation", "km", "numeric"),
        ("RI-04", "< 500 people/km² in 5 km radius", "people/km²", "numeric"),
        ("EP-01", "composite feasibility score >= 3", None, "numeric"),
        ("NS-08", ">= 2 km from protected area", "km", "numeric"),
    ]
    for crit_id, threshold, units, vtype in data:
        conn.execute(
            sa.text("""
                UPDATE criteria
                SET threshold_expression = :threshold,
                    units = :units,
                    value_type = :vtype
                WHERE criterion_id = :crit_id
            """),
            {"crit_id": crit_id, "threshold": threshold, "units": units, "vtype": vtype},
        )


def downgrade() -> None:
    op.drop_column("criteria", "source_priority")
    op.drop_column("criteria", "domain_column_prefix")
    op.drop_column("criteria", "domain_table")
    op.drop_column("criteria", "value_type")
    op.drop_column("criteria", "units")
    op.drop_column("criteria", "threshold_expression")
    op.drop_column("criteria", "criterion_class")
