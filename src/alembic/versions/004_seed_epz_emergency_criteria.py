# man_hours: 2.5
"""Seed screening criteria — RI-04, RI-05, NS-05, EP-01.

Adds the criteria needed by the EPZ population analysis, proximity land
assessment, and emergency planning feasibility modules.

Revision ID: 004
Revises: 003
Create Date: 2026-03-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CRITERIA = [
    {
        "criterion_id": "RI-04",
        "name": "Population Density at EPZ Radii",
        "category": "radiological_impact",
        "phase": "screening",
        "weight": None,
        "iaea_reference": "IAEA SSG-35 Annex II section II-4; NS-R-3 Rev.1",
        "epri_reference": "EPRI coal-to-nuclear siting guide — population density",
        "description": (
            "Evaluates population density within Emergency Planning Zone radii "
            "(5/16/25/80 km per SSG-35).  Sites with extremely high density "
            "(>1 000 persons/km² within 5 km) are flagged for avoidance.  Data "
            "sourced from OSM populated places with population tags."
        ),
    },
    {
        "criterion_id": "RI-05",
        "name": "Distance to Population Centres",
        "category": "radiological_impact",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": "IAEA SSG-35 Annex II section II-4",
        "epri_reference": "EPRI coal-to-nuclear siting guide",
        "description": (
            "Ranks sites by distance to nearest city exceeding 50 000 "
            "population.  Greater distance is more favourable for siting.  "
            "Rank-only criterion — no exclusionary threshold."
        ),
    },
    {
        "criterion_id": "NS-05",
        "name": "Site Footprint Adequacy",
        "category": "site_characteristics",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": "IAEA NS-R-3 Rev.1",
        "epri_reference": "EPRI coal-to-nuclear criteria",
        "description": (
            "Assesses total available land including adjacent developable area "
            "(from CORINE land cover) minus protected areas (Natura 2000, WDPA).  "
            "Produces available_adjacent_ha used to determine whether sites with "
            "small on-site boundaries could still accommodate SMR construction."
        ),
    },
    {
        "criterion_id": "EP-01",
        "name": "Emergency Planning Feasibility",
        "category": "emergency_planning",
        "phase": "screening",
        "weight": None,
        "iaea_reference": "IAEA SSG-35 Annex II; GSR Part 7",
        "epri_reference": "EPRI coal-to-nuclear siting guide — emergency planning",
        "description": (
            "Composite feasibility assessment combining: evacuation route "
            "capacity (EP-02), special populations within EPZ (EP-03), physical "
            "geography barriers (EP-04), and EPZ population magnitude (EP-05).  "
            "Weighted score 0–100; sites below the fail threshold (default 30) "
            "are marked as fail."
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
    ids = ("RI-04", "RI-05", "NS-05", "EP-01")
    for cid in ids:
        op.execute(f"DELETE FROM criteria WHERE criterion_id = '{cid}'")
