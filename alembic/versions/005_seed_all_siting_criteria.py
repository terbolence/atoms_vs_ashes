# man_hours: 3.0
"""Seed all 46 siting criteria from requirements/05_siting_criteria.md.

Previous migrations (002–004) seeded BF-01, BF-02, RI-04, RI-05, NS-05,
EP-01.  This migration adds every remaining criterion so that connectors
writing to ``site_attributes`` never hit a FK violation on
``criteria.criterion_id``.

Revision ID: 005
Revises: 004
Create Date: 2026-04-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Criteria already seeded by earlier migrations — skip these.
_ALREADY_SEEDED = {"BF-01", "BF-02", "RI-04", "RI-05", "NS-05", "EP-01"}

CRITERIA = [
    # ── Natural Hazards ──────────────────────────────────────────────
    {
        "criterion_id": "NH-01",
        "name": "Seismic: Ground Motion",
        "category": "natural_hazard",
        "phase": "screening",
        "weight": None,
        "iaea_reference": "SSG-9; NS-R-3 §3.1–3.15",
        "epri_reference": "Exclusionary/Suitability",
        "description": (
            "Peak Ground Acceleration (PGA), spectral acceleration, "
            "return period.  Screen + Rank."
        ),
    },
    {
        "criterion_id": "NH-02",
        "name": "Seismic: Surface Rupture",
        "category": "natural_hazard",
        "phase": "screening",
        "weight": None,
        "iaea_reference": "SSG-9; NS-R-3 §3.7",
        "epri_reference": "Exclusionary",
        "description": (
            "Capable fault distance, fault activity classification, "
            "slip rate.  Exclusionary screening."
        ),
    },
    {
        "criterion_id": "NH-03",
        "name": "Geotechnical: Liquefaction",
        "category": "natural_hazard",
        "phase": "screening",
        "weight": None,
        "iaea_reference": "NS-R-3 §3.38–3.40; NS-G-3.6",
        "epri_reference": "Exclusionary/Suitability",
        "description": (
            "Soil type, groundwater depth, PGA interaction.  "
            "Screen + Rank."
        ),
    },
    {
        "criterion_id": "NH-04",
        "name": "Geotechnical: Slope Stability",
        "category": "natural_hazard",
        "phase": "screening",
        "weight": None,
        "iaea_reference": "SSG-35 Table I-1; NS-G-3.6",
        "epri_reference": "Exclusionary/Suitability",
        "description": (
            "Slope angle, soil/rock type, seismic amplification.  "
            "Screen + Rank."
        ),
    },
    {
        "criterion_id": "NH-05",
        "name": "Geotechnical: Subsidence",
        "category": "natural_hazard",
        "phase": "screening",
        "weight": None,
        "iaea_reference": "NS-R-3 §3.35–3.36",
        "epri_reference": "Exclusionary/Suitability",
        "description": (
            "Mining history, karst, oil/gas extraction, ground "
            "settlement.  Screen + Rank."
        ),
    },
    {
        "criterion_id": "NH-06",
        "name": "Geotechnical: Foundation",
        "category": "natural_hazard",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": "NS-G-3.6",
        "epri_reference": "Suitability",
        "description": (
            "Bearing capacity, depth to bedrock, groundwater regime.  "
            "Ranking only."
        ),
    },
    {
        "criterion_id": "NH-07",
        "name": "Volcanism",
        "category": "natural_hazard",
        "phase": "screening",
        "weight": None,
        "iaea_reference": "SSG-21; SSG-35 Table I-1",
        "epri_reference": "Exclusionary",
        "description": (
            "Proximity to Holocene volcanoes, volcanic product hazards.  "
            "Exclusionary screening."
        ),
    },
    {
        "criterion_id": "NH-08",
        "name": "Coastal Flooding",
        "category": "natural_hazard",
        "phase": "screening",
        "weight": None,
        "iaea_reference": "SSG-18; SSG-35 §A.19–A.27",
        "epri_reference": "Avoidance/Suitability",
        "description": (
            "Storm surge, seiche, tsunami, tidal extremes, wave action.  "
            "Screen + Rank."
        ),
    },
    {
        "criterion_id": "NH-09",
        "name": "River Flooding",
        "category": "natural_hazard",
        "phase": "screening",
        "weight": None,
        "iaea_reference": "SSG-18; SSG-35 §A.28–A.30",
        "epri_reference": "Avoidance/Suitability",
        "description": (
            "Overtopping, dam break, ice hazard, flash flood.  "
            "Screen + Rank."
        ),
    },
    {
        "criterion_id": "NH-10",
        "name": "Extreme Winds",
        "category": "natural_hazard",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": "SSG-18; SSG-35 Table I-1",
        "epri_reference": "Suitability",
        "description": "Straight winds, tornadoes, tropical storms.  Ranking only.",
    },
    {
        "criterion_id": "NH-11",
        "name": "Extreme Precipitation",
        "category": "natural_hazard",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": "SSG-18",
        "epri_reference": "Suitability",
        "description": (
            "Snow, hail, freezing rain, intense rainfall, drought.  "
            "Ranking only."
        ),
    },
    {
        "criterion_id": "NH-12",
        "name": "Extreme Temperatures",
        "category": "natural_hazard",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": "SSG-18",
        "epri_reference": "Suitability",
        "description": (
            "Air and water temperature extremes, climate projections.  "
            "Ranking only."
        ),
    },
    {
        "criterion_id": "NH-13",
        "name": "Forest/Wildfire",
        "category": "natural_hazard",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": "SSG-35 §4.3(l)",
        "epri_reference": "Suitability",
        "description": (
            "Proximity to combustible vegetation, fire history.  "
            "Ranking only."
        ),
    },
    {
        "criterion_id": "NH-14",
        "name": "Combined Hazards",
        "category": "natural_hazard",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": "SSG-35 §4.3(m)",
        "epri_reference": "Suitability",
        "description": (
            "Credible combinations (e.g., seismic + flood, wind + snow).  "
            "Ranking only."
        ),
    },
    # ── Human-Induced Hazards ────────────────────────────────────────
    {
        "criterion_id": "HI-01",
        "name": "Aircraft Crash",
        "category": "human_induced_hazard",
        "phase": "screening",
        "weight": None,
        "iaea_reference": "NS-G-3.1; SSG-35 Table II-1 (Nos. 2–5)",
        "epri_reference": "Avoidance/Suitability",
        "description": (
            "Airport distance, flight path proximity, air traffic density.  "
            "Screen + Rank."
        ),
    },
    {
        "criterion_id": "HI-02",
        "name": "Industrial Explosions",
        "category": "human_induced_hazard",
        "phase": "screening",
        "weight": None,
        "iaea_reference": "NS-G-3.1; NS-R-3 §3.49–3.50",
        "epri_reference": "Avoidance/Suitability",
        "description": (
            "Distance to chemical/petrochemical/munitions facilities.  "
            "Screen + Rank."
        ),
    },
    {
        "criterion_id": "HI-03",
        "name": "Toxic/Gas Releases",
        "category": "human_induced_hazard",
        "phase": "screening",
        "weight": None,
        "iaea_reference": "NS-G-3.1; SSG-35 Table II-1 (No. 9)",
        "epri_reference": "Avoidance/Suitability",
        "description": "Distance to hazardous cloud sources.  Screen + Rank.",
    },
    {
        "criterion_id": "HI-04",
        "name": "External Fires",
        "category": "human_induced_hazard",
        "phase": "screening",
        "weight": None,
        "iaea_reference": "NS-G-3.1",
        "epri_reference": "Avoidance/Suitability",
        "description": (
            "Proximity to flammable storage, pipeline infrastructure.  "
            "Screen + Rank."
        ),
    },
    {
        "criterion_id": "HI-05",
        "name": "Transport Hazards",
        "category": "human_induced_hazard",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": "NS-G-3.1",
        "epri_reference": "Suitability",
        "description": (
            "Road/rail/pipeline proximity carrying hazardous materials.  "
            "Ranking only."
        ),
    },
    {
        "criterion_id": "HI-06",
        "name": "Military Installations",
        "category": "human_induced_hazard",
        "phase": "screening",
        "weight": None,
        "iaea_reference": "NS-G-3.1; SSG-35 Table II-1 (Nos. 6–7)",
        "epri_reference": "Avoidance/Suitability",
        "description": (
            "Distance to ranges, arsenals, restricted airspace.  "
            "Screen + Rank."
        ),
    },
    {
        "criterion_id": "HI-07",
        "name": "Electromagnetic Interference",
        "category": "human_induced_hazard",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": "SSG-35 §4.4(c)",
        "epri_reference": "Suitability",
        "description": (
            "Proximity to high-power broadcasting/communication.  "
            "Ranking only."
        ),
    },
    {
        "criterion_id": "HI-08",
        "name": "Other Nuclear Installations",
        "category": "human_induced_hazard",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": "SSG-35 §3.24–3.27",
        "epri_reference": "Suitability",
        "description": (
            "Distance to existing nuclear facilities (combined risk).  "
            "Ranking only."
        ),
    },
    # ── Radiological Impact ──────────────────────────────────────────
    {
        "criterion_id": "RI-01",
        "name": "Atmospheric Dispersion",
        "category": "radiological_impact",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": "NS-G-3.2; SSG-35 §4.5",
        "epri_reference": "Suitability",
        "description": (
            "Wind rose, stability classes, terrain effects, mixing height.  "
            "Ranking only."
        ),
    },
    {
        "criterion_id": "RI-02",
        "name": "Surface Water Dispersion",
        "category": "radiological_impact",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": "NS-G-3.2",
        "epri_reference": "Suitability",
        "description": (
            "River flow, dilution capacity, downstream population/intake.  "
            "Ranking only."
        ),
    },
    {
        "criterion_id": "RI-03",
        "name": "Groundwater Dispersion",
        "category": "radiological_impact",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": "NS-G-3.2",
        "epri_reference": "Suitability",
        "description": (
            "Aquifer characteristics, flow direction, downstream use.  "
            "Ranking only."
        ),
    },
    # RI-04, RI-05 already seeded in migration 004
    {
        "criterion_id": "RI-06",
        "name": "Population Projections",
        "category": "radiological_impact",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": "SSG-35 §A.39",
        "epri_reference": "Suitability",
        "description": (
            "Projected density over 60-year design life.  Ranking only."
        ),
    },
    # ── Emergency Planning ───────────────────────────────────────────
    # EP-01 already seeded in migration 004
    {
        "criterion_id": "EP-02",
        "name": "Evacuation Routes",
        "category": "emergency_planning",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": "SSG-35 §4.6(a)–(b)",
        "epri_reference": "Suitability",
        "description": (
            "Road network capacity, alternative routes, seasonal constraints.  "
            "Ranking only."
        ),
    },
    {
        "criterion_id": "EP-03",
        "name": "Physical Geography Constraints",
        "category": "emergency_planning",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": "SSG-35 §4.6(a)",
        "epri_reference": "Suitability",
        "description": (
            "Islands, mountains, rivers obstructing evacuation.  "
            "Ranking only."
        ),
    },
    {
        "criterion_id": "EP-04",
        "name": "Special Populations",
        "category": "emergency_planning",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": "SSG-35 §4.6(c)",
        "epri_reference": "Suitability",
        "description": (
            "Hospitals, prisons, elderly care within EPZ.  "
            "Ranking only."
        ),
    },
    {
        "criterion_id": "EP-05",
        "name": "Concurrent Hazard Impact",
        "category": "emergency_planning",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": "SSG-35 §4.6(f)",
        "epri_reference": "Suitability",
        "description": (
            "External hazards degrading emergency infrastructure.  "
            "Ranking only."
        ),
    },
    # ── Non-Safety ───────────────────────────────────────────────────
    {
        "criterion_id": "NS-01",
        "name": "Cooling Water Availability",
        "category": "non_safety",
        "phase": "screening",
        "weight": None,
        "iaea_reference": "SSG-35 §4.9",
        "epri_reference": "EPRI coal-to-nuclear criteria",
        "description": (
            "Source type, volume, seasonal variation, competing demands.  "
            "Screen + Rank."
        ),
    },
    {
        "criterion_id": "NS-02",
        "name": "Grid Connection",
        "category": "non_safety",
        "phase": "screening",
        "weight": None,
        "iaea_reference": None,
        "epri_reference": "EPRI coal-to-nuclear criteria",
        "description": (
            "Transmission voltage, capacity, distance to substation.  "
            "Screen + Rank."
        ),
    },
    {
        "criterion_id": "NS-03",
        "name": "Transport Access",
        "category": "non_safety",
        "phase": "screening",
        "weight": None,
        "iaea_reference": None,
        "epri_reference": "EPRI coal-to-nuclear criteria; NuScale logistics",
        "description": (
            "Heavy-haul road, rail gauge/capacity, navigable waterway.  "
            "Screen + Rank."
        ),
    },
    {
        "criterion_id": "NS-04",
        "name": "Site Topography",
        "category": "non_safety",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": "SSG-35 Table I-1",
        "epri_reference": "Suitability",
        "description": (
            "Terrain suitability, grading requirements, drainage.  "
            "Ranking only."
        ),
    },
    # NS-05 already seeded in migration 004
    {
        "criterion_id": "NS-06",
        "name": "Existing Infrastructure",
        "category": "non_safety",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": None,
        "epri_reference": "DOE coal-to-nuclear guidance",
        "description": (
            "Reusable structures, roads, services, demolition burden.  "
            "Ranking only."
        ),
    },
    {
        "criterion_id": "NS-07",
        "name": "Environmental Impact (non-rad)",
        "category": "non_safety",
        "phase": "screening",
        "weight": None,
        "iaea_reference": "SSG-35 §4.9",
        "epri_reference": "EPRI coal-to-nuclear criteria",
        "description": (
            "Thermal discharge, chemical discharge, noise, visual.  "
            "Screen + Rank."
        ),
    },
    {
        "criterion_id": "NS-08",
        "name": "Ecological Sensitivity",
        "category": "non_safety",
        "phase": "screening",
        "weight": None,
        "iaea_reference": "SSG-35 Table II-1 (No. 10)",
        "epri_reference": "EPRI coal-to-nuclear criteria",
        "description": (
            "Proximity to Natura 2000, RAMSAR, IBAs, protected species.  "
            "Screen + Rank."
        ),
    },
    {
        "criterion_id": "NS-09",
        "name": "Socioeconomic Impact",
        "category": "non_safety",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": "SSG-35 §4.9",
        "epri_reference": "EPRI coal-to-nuclear criteria",
        "description": (
            "Employment, tax revenue, community benefit, public acceptance.  "
            "Ranking only."
        ),
    },
    {
        "criterion_id": "NS-10",
        "name": "Workforce Availability",
        "category": "non_safety",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": None,
        "epri_reference": "DOE coal-to-nuclear guidance",
        "description": (
            "Existing skilled workforce, retraining potential, housing.  "
            "Ranking only."
        ),
    },
    {
        "criterion_id": "NS-11",
        "name": "Coal-to-Nuclear Synergies",
        "category": "non_safety",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": None,
        "epri_reference": "DOE/INL; EPRI",
        "description": (
            "Degree of infrastructure reuse, cost savings potential.  "
            "Ranking only."
        ),
    },
    {
        "criterion_id": "NS-12",
        "name": "Regulatory/Political Environment",
        "category": "non_safety",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": None,
        "epri_reference": "EPRI; national policy",
        "description": (
            "National nuclear policy, public opinion, licensing pathway.  "
            "Ranking only."
        ),
    },
    {
        "criterion_id": "NS-13",
        "name": "Construction Logistics",
        "category": "non_safety",
        "phase": "ranking",
        "weight": None,
        "iaea_reference": "SSG-35 Annex II §II-9(c)",
        "epri_reference": None,
        "description": (
            "Material supply, construction water, temporary facilities.  "
            "Ranking only."
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
    ids = [c["criterion_id"] for c in CRITERIA]
    for cid in ids:
        op.execute(f"DELETE FROM criteria WHERE criterion_id = '{cid}'")
