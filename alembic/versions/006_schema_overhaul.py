# man_hours: 4.0
"""Schema overhaul: replace EAV tables with explicit domain tables.

Drops: site_attributes, site_infrastructure, site_scores,
       screening_results, ranking_results, data_quality_flags.
Creates: smr_designs, site_natural_hazards, site_human_hazards,
         site_radiological, site_emergency_planning,
         site_infrastructure_v2, screening_verdicts, ranking_scores,
         composite_rankings, site_observations.
Adds 'caution' value to screening_verdict enum.

Revision ID: 006
Revises: 005
Create Date: 2026-04-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SMR_SEEDS = [
    ("oklo_aurora", "Oklo Aurora", 75, None, 22, None, None, None, None, "NRC pre-application"),
    ("xe_100", "X-energy Xe-100", 80, 200, 31, None, None, None, 60, "NRC pre-application"),
    ("bwrx_300", "GE Hitachi BWRX-300", 300, 870, 25.3, None, None, None, 60, "Licensing underway (US NRC/Canada CNSC)"),
    ("holtec_smr300", "Holtec SMR-300", 300, 865, 38, None, None, None, 80, "Pre-application ongoing"),
    ("natrium_nominal", "TerraPower Natrium (nominal)", 345, 840, 51, None, None, None, 80, "NRC construction permit authorized"),
    ("nuscale_voygr6", "NuScale VOYGR-6", 462, 1500, 72.8, None, 700, None, 60, "NRC SDA approved"),
    ("rolls_royce_smr", "Rolls-Royce SMR", 470, 1358, 44.5, None, None, None, 60, "UK GDA Step 2 completed"),
    ("natrium_peak", "TerraPower Natrium (peak)", 500, 840, 51, None, None, None, 80, "NRC construction permit authorized"),
]


def upgrade() -> None:
    # Add 'caution' to the screening_verdict enum
    op.execute("ALTER TYPE screening_verdict ADD VALUE IF NOT EXISTS 'caution'")

    # -- Create smr_designs reference table --
    op.create_table(
        "smr_designs",
        sa.Column("smr_key", sa.String(30), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("capacity_mwe", sa.Numeric(10, 2), nullable=False),
        sa.Column("thermal_output_mwt", sa.Numeric(10, 2)),
        sa.Column("land_requirement_ha", sa.Numeric(10, 2), nullable=False),
        sa.Column("epz_radius_km", sa.Numeric(8, 2)),
        sa.Column("module_weight_t", sa.Numeric(10, 2)),
        sa.Column("cooling_type", sa.String(60)),
        sa.Column("design_life_yr", sa.Integer()),
        sa.Column("regulatory_status", sa.String(200)),
    )

    smr_table = sa.table(
        "smr_designs",
        sa.column("smr_key", sa.String),
        sa.column("name", sa.String),
        sa.column("capacity_mwe", sa.Numeric),
        sa.column("thermal_output_mwt", sa.Numeric),
        sa.column("land_requirement_ha", sa.Numeric),
        sa.column("epz_radius_km", sa.Numeric),
        sa.column("module_weight_t", sa.Numeric),
        sa.column("cooling_type", sa.String),
        sa.column("design_life_yr", sa.Integer),
        sa.column("regulatory_status", sa.String),
    )
    op.bulk_insert(smr_table, [
        dict(
            smr_key=r[0], name=r[1], capacity_mwe=r[2],
            thermal_output_mwt=r[3], land_requirement_ha=r[4],
            epz_radius_km=r[5], module_weight_t=r[6],
            cooling_type=r[7], design_life_yr=r[8],
            regulatory_status=r[9],
        )
        for r in _SMR_SEEDS
    ])

    # -- Domain measurement tables --
    _tz = sa.DateTime(timezone=True)

    op.create_table(
        "site_natural_hazards",
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.site_id"), primary_key=True),
        # NH-01
        sa.Column("pga_475yr_g", sa.Numeric(8, 5)),
        sa.Column("pga_2475yr_g", sa.Numeric(8, 5)),
        sa.Column("spectral_accel_json", postgresql.JSONB()),
        sa.Column("nh01_source", sa.String(200)),
        sa.Column("nh01_quality", sa.String(20)),
        sa.Column("nh01_comment", sa.Text()),
        # NH-02
        sa.Column("nearest_fault_km", sa.Numeric(8, 2)),
        sa.Column("fault_name", sa.String(200)),
        sa.Column("fault_slip_rate_mm_yr", sa.Numeric(8, 3)),
        sa.Column("nh02_source", sa.String(200)),
        sa.Column("nh02_quality", sa.String(20)),
        sa.Column("nh02_comment", sa.Text()),
        # NH-03
        sa.Column("liquefaction_suscept", sa.String(30)),
        sa.Column("soil_type", sa.String(100)),
        sa.Column("groundwater_depth_m", sa.Numeric(8, 2)),
        sa.Column("nh03_quality", sa.String(20)),
        sa.Column("nh03_comment", sa.Text()),
        # NH-04
        sa.Column("slope_angle_deg", sa.Numeric(6, 2)),
        sa.Column("slope_stability_class", sa.String(30)),
        sa.Column("nh04_quality", sa.String(20)),
        sa.Column("nh04_comment", sa.Text()),
        # NH-05
        sa.Column("mining_void_present", sa.Boolean()),
        sa.Column("karst_present", sa.Boolean()),
        sa.Column("subsidence_risk_class", sa.String(30)),
        sa.Column("nh05_quality", sa.String(20)),
        sa.Column("nh05_comment", sa.Text()),
        # NH-06
        sa.Column("bearing_capacity_kpa", sa.Numeric(10, 2)),
        sa.Column("depth_to_bedrock_m", sa.Numeric(8, 2)),
        sa.Column("nh06_quality", sa.String(20)),
        sa.Column("nh06_comment", sa.Text()),
        # NH-07
        sa.Column("nearest_holocene_volcano_km", sa.Numeric(8, 2)),
        sa.Column("volcano_name", sa.String(200)),
        sa.Column("nh07_quality", sa.String(20)),
        sa.Column("nh07_comment", sa.Text()),
        # NH-08
        sa.Column("distance_to_coast_km", sa.Numeric(8, 2)),
        sa.Column("storm_surge_risk", sa.String(30)),
        sa.Column("tsunami_risk", sa.String(30)),
        sa.Column("nh08_quality", sa.String(20)),
        sa.Column("nh08_comment", sa.Text()),
        # NH-09
        sa.Column("flood_zone_class", sa.String(30)),
        sa.Column("nearest_river_km", sa.Numeric(8, 2)),
        sa.Column("dam_break_exposure", sa.Boolean()),
        sa.Column("nh09_quality", sa.String(20)),
        sa.Column("nh09_comment", sa.Text()),
        # NH-10
        sa.Column("max_wind_speed_ms", sa.Numeric(8, 2)),
        sa.Column("nh10_quality", sa.String(20)),
        sa.Column("nh10_comment", sa.Text()),
        # NH-11
        sa.Column("extreme_precip_mm", sa.Numeric(8, 2)),
        sa.Column("nh11_quality", sa.String(20)),
        sa.Column("nh11_comment", sa.Text()),
        # NH-12
        sa.Column("extreme_temp_max_c", sa.Numeric(6, 2)),
        sa.Column("extreme_temp_min_c", sa.Numeric(6, 2)),
        sa.Column("nh12_quality", sa.String(20)),
        sa.Column("nh12_comment", sa.Text()),
        # NH-13
        sa.Column("wildfire_combustible_pct", sa.Numeric(5, 2)),
        sa.Column("wildfire_wui_ha", sa.Numeric(10, 2)),
        sa.Column("nh13_quality", sa.String(20)),
        sa.Column("nh13_comment", sa.Text()),
        # NH-14
        sa.Column("combined_hazard_notes", sa.Text()),
        sa.Column("nh14_quality", sa.String(20)),
        sa.Column("nh14_comment", sa.Text()),
        sa.Column("fetched_at", _tz),
        sa.Column("run_id", sa.String(40)),
    )

    op.create_table(
        "site_human_hazards",
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.site_id"), primary_key=True),
        # HI-01
        sa.Column("nearest_airport_km", sa.Numeric(8, 2)),
        sa.Column("nearest_airport_name", sa.String(200)),
        sa.Column("nearest_airport_type", sa.String(30)),
        sa.Column("flight_path_distance_km", sa.Numeric(8, 2)),
        sa.Column("airport_count", sa.Integer()),
        sa.Column("hi01_quality", sa.String(20)),
        sa.Column("hi01_comment", sa.Text()),
        # HI-02
        sa.Column("nearest_seveso_km", sa.Numeric(8, 2)),
        sa.Column("nearest_industrial_km", sa.Numeric(8, 2)),
        sa.Column("hi02_quality", sa.String(20)),
        sa.Column("hi02_comment", sa.Text()),
        # HI-03
        sa.Column("nearest_toxic_source_km", sa.Numeric(8, 2)),
        sa.Column("hi03_quality", sa.String(20)),
        sa.Column("hi03_comment", sa.Text()),
        # HI-04
        sa.Column("nearest_flammable_storage_km", sa.Numeric(8, 2)),
        sa.Column("nearest_pipeline_km", sa.Numeric(8, 2)),
        sa.Column("hi04_quality", sa.String(20)),
        sa.Column("hi04_comment", sa.Text()),
        # HI-05
        sa.Column("hazmat_route_distance_km", sa.Numeric(8, 2)),
        sa.Column("hi05_quality", sa.String(20)),
        sa.Column("hi05_comment", sa.Text()),
        # HI-06
        sa.Column("nearest_military_km", sa.Numeric(8, 2)),
        sa.Column("nearest_military_name", sa.String(200)),
        sa.Column("military_count", sa.Integer()),
        sa.Column("hi06_quality", sa.String(20)),
        sa.Column("hi06_comment", sa.Text()),
        # HI-07
        sa.Column("nearest_transmitter_km", sa.Numeric(8, 2)),
        sa.Column("transmitter_type", sa.String(60)),
        sa.Column("transmitter_count", sa.Integer()),
        sa.Column("hi07_quality", sa.String(20)),
        sa.Column("hi07_comment", sa.Text()),
        # HI-08
        sa.Column("nearest_nuclear_km", sa.Numeric(8, 2)),
        sa.Column("nearest_nuclear_name", sa.String(200)),
        sa.Column("hi08_quality", sa.String(20)),
        sa.Column("hi08_comment", sa.Text()),
        sa.Column("fetched_at", _tz),
        sa.Column("run_id", sa.String(40)),
    )

    op.create_table(
        "site_radiological",
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.site_id"), primary_key=True),
        # RI-04
        sa.Column("pop_density_5km", sa.Numeric(10, 2)),
        sa.Column("pop_density_16km", sa.Numeric(10, 2)),
        sa.Column("pop_density_25km", sa.Numeric(10, 2)),
        sa.Column("pop_density_80km", sa.Numeric(10, 2)),
        sa.Column("pop_total_5km", sa.Integer()),
        sa.Column("pop_total_16km", sa.Integer()),
        sa.Column("pop_total_25km", sa.Integer()),
        sa.Column("pop_total_80km", sa.Integer()),
        sa.Column("ri04_quality", sa.String(20)),
        sa.Column("ri04_comment", sa.Text()),
        # RI-05
        sa.Column("nearest_city_50k_km", sa.Numeric(8, 2)),
        sa.Column("nearest_city_name", sa.String(200)),
        sa.Column("nearest_city_pop", sa.Integer()),
        sa.Column("ri05_quality", sa.String(20)),
        sa.Column("ri05_comment", sa.Text()),
        # RI-06
        sa.Column("pop_growth_rate_pct", sa.Numeric(6, 3)),
        sa.Column("projected_pop_25km_60yr", sa.Integer()),
        sa.Column("ri06_quality", sa.String(20)),
        sa.Column("ri06_comment", sa.Text()),
        # RI-01
        sa.Column("prevailing_wind_dir", sa.String(10)),
        sa.Column("avg_wind_speed_ms", sa.Numeric(6, 2)),
        sa.Column("mixing_height_m", sa.Numeric(8, 2)),
        sa.Column("ri01_quality", sa.String(20)),
        sa.Column("ri01_comment", sa.Text()),
        # RI-02
        sa.Column("nearest_river_flow_m3s", sa.Numeric(12, 2)),
        sa.Column("ri02_quality", sa.String(20)),
        sa.Column("ri02_comment", sa.Text()),
        # RI-03
        sa.Column("aquifer_type", sa.String(60)),
        sa.Column("groundwater_flow_dir", sa.String(30)),
        sa.Column("ri03_quality", sa.String(20)),
        sa.Column("ri03_comment", sa.Text()),
        sa.Column("fetched_at", _tz),
        sa.Column("run_id", sa.String(40)),
    )

    op.create_table(
        "site_emergency_planning",
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.site_id"), primary_key=True),
        # EP-01
        sa.Column("ep01_composite_score", sa.Numeric(5, 1)),
        sa.Column("ep01_road_score", sa.Numeric(5, 1)),
        sa.Column("ep01_special_pop_score", sa.Numeric(5, 1)),
        sa.Column("ep01_geography_score", sa.Numeric(5, 1)),
        sa.Column("ep01_population_score", sa.Numeric(5, 1)),
        sa.Column("ep01_quality", sa.String(20)),
        sa.Column("ep01_comment", sa.Text()),
        # EP-02
        sa.Column("road_density_km_per_km2", sa.Numeric(8, 3)),
        sa.Column("total_road_km", sa.Numeric(10, 2)),
        sa.Column("has_motorway_access", sa.Boolean()),
        sa.Column("ep02_quality", sa.String(20)),
        sa.Column("ep02_comment", sa.Text()),
        # EP-03
        sa.Column("major_river_barrier", sa.Boolean()),
        sa.Column("waterway_count_epz", sa.Integer()),
        sa.Column("ep03_quality", sa.String(20)),
        sa.Column("ep03_comment", sa.Text()),
        # EP-04
        sa.Column("hospital_count_epz", sa.Integer()),
        sa.Column("prison_count_epz", sa.Integer()),
        sa.Column("care_home_count_epz", sa.Integer()),
        sa.Column("ep04_quality", sa.String(20)),
        sa.Column("ep04_comment", sa.Text()),
        # EP-05
        sa.Column("concurrent_hazard_notes", sa.Text()),
        sa.Column("ep05_quality", sa.String(20)),
        sa.Column("ep05_comment", sa.Text()),
        sa.Column("fetched_at", _tz),
        sa.Column("run_id", sa.String(40)),
    )

    op.create_table(
        "site_infrastructure_v2",
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.site_id"), primary_key=True),
        # NS-01
        sa.Column("cooling_source_type", sa.String(60)),
        sa.Column("cooling_source_name", sa.String(200)),
        sa.Column("cooling_distance_km", sa.Numeric(8, 2)),
        sa.Column("cooling_flow_m3s", sa.Numeric(12, 2)),
        sa.Column("ns01_quality", sa.String(20)),
        sa.Column("ns01_comment", sa.Text()),
        # NS-02
        sa.Column("nearest_substation_km", sa.Numeric(8, 2)),
        sa.Column("substation_name", sa.String(200)),
        sa.Column("nearest_hv_line_km", sa.Numeric(8, 2)),
        sa.Column("hv_line_voltage_kv", sa.Integer()),
        sa.Column("hv_line_count", sa.Integer()),
        sa.Column("substation_count", sa.Integer()),
        sa.Column("grid_export_capacity_mw", sa.Numeric(10, 2)),
        sa.Column("ns02_quality", sa.String(20)),
        sa.Column("ns02_comment", sa.Text()),
        # NS-03
        sa.Column("nearest_highway_km", sa.Numeric(8, 2)),
        sa.Column("nearest_rail_km", sa.Numeric(8, 2)),
        sa.Column("nearest_waterway_km", sa.Numeric(8, 2)),
        sa.Column("heavy_haul_capable", sa.Boolean()),
        sa.Column("ns03_quality", sa.String(20)),
        sa.Column("ns03_comment", sa.Text()),
        # NS-04
        sa.Column("dominant_land_class", sa.String(30)),
        sa.Column("dominant_class_pct", sa.Numeric(5, 2)),
        sa.Column("favourable_land_pct", sa.Numeric(5, 2)),
        sa.Column("moderate_land_pct", sa.Numeric(5, 2)),
        sa.Column("unfavourable_land_pct", sa.Numeric(5, 2)),
        sa.Column("ns04_quality", sa.String(20)),
        sa.Column("ns04_comment", sa.Text()),
        # NS-05
        sa.Column("buildable_area_ha", sa.Numeric(10, 2)),
        sa.Column("largest_contiguous_ha", sa.Numeric(10, 2)),
        sa.Column("patch_count", sa.Integer()),
        sa.Column("ns05_quality", sa.String(20)),
        sa.Column("ns05_comment", sa.Text()),
        # NS-06
        sa.Column("reusable_infra_score", sa.SmallInteger()),
        sa.Column("ns06_quality", sa.String(20)),
        sa.Column("ns06_comment", sa.Text()),
        # NS-07
        sa.Column("env_impact_notes", sa.Text()),
        sa.Column("ns07_quality", sa.String(20)),
        sa.Column("ns07_comment", sa.Text()),
        # NS-08
        sa.Column("ecological_natural_pct", sa.Numeric(5, 2)),
        sa.Column("ecological_patch_count", sa.Integer()),
        sa.Column("ecological_largest_patch_ha", sa.Numeric(10, 2)),
        sa.Column("ns08_quality", sa.String(20)),
        sa.Column("ns08_comment", sa.Text()),
        # NS-09
        sa.Column("ns09_quality", sa.String(20)),
        sa.Column("ns09_comment", sa.Text()),
        # NS-10
        sa.Column("ns10_quality", sa.String(20)),
        sa.Column("ns10_comment", sa.Text()),
        # NS-11
        sa.Column("ns11_quality", sa.String(20)),
        sa.Column("ns11_comment", sa.Text()),
        # NS-12
        sa.Column("ns12_quality", sa.String(20)),
        sa.Column("ns12_comment", sa.Text()),
        # NS-13
        sa.Column("laydown_suitable_ha", sa.Numeric(10, 2)),
        sa.Column("laydown_largest_patch_ha", sa.Numeric(10, 2)),
        sa.Column("ns13_quality", sa.String(20)),
        sa.Column("ns13_comment", sa.Text()),
        sa.Column("fetched_at", _tz),
        sa.Column("run_id", sa.String(40)),
    )

    # -- Decision tables with SMR dimension --
    screening_verdict_type = postgresql.ENUM(
        "pass", "fail", "inconclusive", "caution",
        name="screening_verdict", create_type=False,
    )

    op.create_table(
        "screening_verdicts",
        sa.Column("verdict_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.site_id"), nullable=False),
        sa.Column("smr_key", sa.String(30), sa.ForeignKey("smr_designs.smr_key"), nullable=False),
        sa.Column("criterion_id", sa.String(10), sa.ForeignKey("criteria.criterion_id"), nullable=False),
        sa.Column("phase", sa.String(30), nullable=False),
        sa.Column("verdict", screening_verdict_type, nullable=False),
        sa.Column("measured_value", sa.Text()),
        sa.Column("threshold", sa.Text()),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("confidence", sa.String(20), nullable=False),
        sa.Column("data_sources", postgresql.ARRAY(sa.String())),
        sa.Column("run_id", sa.String(40)),
        sa.Column("screened_at", _tz, server_default=sa.text("now()")),
        sa.UniqueConstraint("site_id", "smr_key", "criterion_id", "run_id", name="uq_verdict_site_smr_criterion_run"),
        sa.Index("ix_verdict_site_id", "site_id"),
    )

    op.create_table(
        "ranking_scores",
        sa.Column("score_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.site_id"), nullable=False),
        sa.Column("smr_key", sa.String(30), sa.ForeignKey("smr_designs.smr_key"), nullable=False),
        sa.Column("criterion_id", sa.String(10), sa.ForeignKey("criteria.criterion_id"), nullable=False),
        sa.Column("score", sa.SmallInteger(), nullable=False),
        sa.Column("score_low", sa.SmallInteger()),
        sa.Column("score_high", sa.SmallInteger()),
        sa.Column("confidence", sa.String(20), nullable=False),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("data_sources", postgresql.ARRAY(sa.String())),
        sa.Column("run_id", sa.String(40)),
        sa.Column("scored_at", _tz, server_default=sa.text("now()")),
        sa.CheckConstraint("score BETWEEN 1 AND 5", name="ck_ranking_score_range"),
        sa.CheckConstraint("score_low IS NULL OR score_low BETWEEN 1 AND 5", name="ck_ranking_score_low_range"),
        sa.CheckConstraint("score_high IS NULL OR score_high BETWEEN 1 AND 5", name="ck_ranking_score_high_range"),
        sa.UniqueConstraint("site_id", "smr_key", "criterion_id", "run_id", name="uq_ranking_site_smr_criterion_run"),
    )

    op.create_table(
        "composite_rankings",
        sa.Column("ranking_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.site_id"), nullable=False),
        sa.Column("smr_key", sa.String(30), sa.ForeignKey("smr_designs.smr_key"), nullable=False),
        sa.Column("composite_score", sa.Numeric(6, 3)),
        sa.Column("rank_position", sa.Integer()),
        sa.Column("passed_exclusionary", sa.Boolean(), nullable=False),
        sa.Column("passed_avoidance", sa.Boolean(), nullable=False),
        sa.Column("criteria_coverage", sa.Numeric(5, 2)),
        sa.Column("avg_confidence", sa.String(20)),
        sa.Column("sensitivity_stable", sa.Boolean()),
        sa.Column("per_category_scores", postgresql.JSONB()),
        sa.Column("run_id", sa.String(40)),
        sa.Column("ranked_at", _tz, server_default=sa.text("now()")),
        sa.UniqueConstraint("site_id", "smr_key", "run_id", name="uq_composite_site_smr_run"),
    )

    # -- Observations table --
    op.create_table(
        "site_observations",
        sa.Column("observation_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.site_id"), nullable=False),
        sa.Column("criterion_id", sa.String(10), sa.ForeignKey("criteria.criterion_id"), nullable=False),
        sa.Column("smr_key", sa.String(30), sa.ForeignKey("smr_designs.smr_key")),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("observation", sa.Text(), nullable=False),
        sa.Column("impact", sa.String(20)),
        sa.Column("confidence", sa.String(20)),
        sa.Column("author", sa.String(100)),
        sa.Column("run_id", sa.String(40)),
        sa.Column("created_at", _tz, server_default=sa.text("now()")),
        sa.Index("ix_obs_site_id", "site_id"),
        sa.Index("ix_obs_criterion_id", "criterion_id"),
    )

    # -- Drop old EAV and decision tables (all empty) --
    op.drop_table("data_quality_flags")
    op.drop_table("ranking_results")
    op.drop_table("screening_results")
    op.drop_table("site_scores")
    op.drop_table("site_attributes")
    op.drop_table("site_infrastructure")


def downgrade() -> None:
    # Recreate old tables
    _tz = sa.DateTime(timezone=True)
    _uuid_default = sa.text("gen_random_uuid()")
    screening_verdict_type = postgresql.ENUM(
        "pass", "fail", "inconclusive", "caution",
        name="screening_verdict", create_type=False,
    )

    op.create_table(
        "site_infrastructure",
        sa.Column("infra_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=_uuid_default),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.site_id"), nullable=False, unique=True),
        sa.Column("grid_voltage_kv", sa.Integer()),
        sa.Column("grid_capacity_mw", sa.Numeric(10, 2)),
        sa.Column("substation_distance_km", sa.Numeric(8, 2)),
        sa.Column("cooling_source_type", sa.String(60)),
        sa.Column("cooling_source_name", sa.String(200)),
        sa.Column("cooling_distance_km", sa.Numeric(8, 2)),
        sa.Column("transport_road", sa.Boolean()),
        sa.Column("transport_rail", sa.Boolean()),
        sa.Column("transport_waterway", sa.Boolean()),
        sa.Column("notes", sa.Text()),
    )

    quality_level_type = postgresql.ENUM(
        "high", "medium", "low", "insufficient",
        name="quality_level", create_type=False,
    )

    op.create_table(
        "site_attributes",
        sa.Column("attribute_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=_uuid_default),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.site_id"), nullable=False),
        sa.Column("criterion_id", sa.String(10), sa.ForeignKey("criteria.criterion_id"), nullable=False),
        sa.Column("value_numeric", sa.Numeric()),
        sa.Column("value_text", sa.Text()),
        sa.Column("value_json", postgresql.JSONB()),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("data_sources.source_id")),
        sa.Column("fetched_at", _tz),
        sa.Column("run_id", sa.String(40)),
        sa.Column("cache_status", sa.String(20)),
        sa.UniqueConstraint("site_id", "criterion_id", "run_id", name="uq_site_criterion_run"),
        sa.Index("ix_attr_site_id", "site_id"),
    )

    op.create_table(
        "site_scores",
        sa.Column("score_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=_uuid_default),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.site_id"), nullable=False),
        sa.Column("criterion_id", sa.String(10), sa.ForeignKey("criteria.criterion_id"), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("justification", sa.Text()),
        sa.Column("source_refs", sa.Text()),
        sa.Column("run_id", sa.String(40)),
        sa.Column("scored_at", _tz, server_default=sa.text("now()")),
        sa.UniqueConstraint("site_id", "criterion_id", "run_id", name="uq_score_site_criterion_run"),
    )

    op.create_table(
        "screening_results",
        sa.Column("result_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=_uuid_default),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.site_id"), nullable=False),
        sa.Column("criterion_id", sa.String(10), sa.ForeignKey("criteria.criterion_id"), nullable=False),
        sa.Column("phase", sa.String(30), nullable=False),
        sa.Column("verdict", screening_verdict_type, nullable=False),
        sa.Column("value", sa.Text()),
        sa.Column("threshold", sa.Text()),
        sa.Column("justification", sa.Text()),
        sa.Column("source_refs", sa.Text()),
        sa.Column("run_id", sa.String(40)),
        sa.Column("screened_at", _tz, server_default=sa.text("now()")),
        sa.UniqueConstraint("site_id", "criterion_id", "run_id", name="uq_screening_site_criterion_run"),
    )

    op.create_table(
        "ranking_results",
        sa.Column("ranking_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=_uuid_default),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.site_id"), nullable=False),
        sa.Column("composite_score", sa.Numeric(7, 4), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("per_criterion_scores", postgresql.JSONB()),
        sa.Column("run_id", sa.String(40)),
        sa.Column("ranked_at", _tz, server_default=sa.text("now()")),
        sa.UniqueConstraint("site_id", "run_id", name="uq_ranking_site_run"),
    )

    op.create_table(
        "data_quality_flags",
        sa.Column("flag_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=_uuid_default),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.site_id")),
        sa.Column("dataset", sa.String(120), nullable=False),
        sa.Column("dimension", sa.String(60), nullable=False),
        sa.Column("level", quality_level_type, nullable=False),
        sa.Column("detail", sa.Text()),
        sa.Column("run_id", sa.String(40)),
        sa.Column("flagged_at", _tz, server_default=sa.text("now()")),
    )

    # Drop new tables
    op.drop_table("site_observations")
    op.drop_table("composite_rankings")
    op.drop_table("ranking_scores")
    op.drop_table("screening_verdicts")
    op.drop_table("site_infrastructure_v2")
    op.drop_table("site_emergency_planning")
    op.drop_table("site_radiological")
    op.drop_table("site_human_hazards")
    op.drop_table("site_natural_hazards")
    op.drop_table("smr_designs")
