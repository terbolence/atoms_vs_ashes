"""SiteContextBuilder — reads main DB and assembles per-site prompt context."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models import (
    Site,
    SiteEmergencyPlanning,
    SiteHumanHazards,
    SiteInfrastructureV2,
    SiteNaturalHazards,
    SiteRadiological,
)
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

RELEVANT_ENRICHMENT_FIELDS: dict[str, dict[str, set[str]]] = {
    "E1": {"natural_hazards": {"pga_475yr_g", "pga_2475yr_g", "nh02_capable_fault_within_8km", "nh02_nearest_fault_km", "nh02_fault_name", "nh02_quality", "nh02_comment"}},
    "E2": {"natural_hazards": {"nh03_liquefaction_suscept", "nh03_soil_type", "nh03_quality", "nh03_comment", "pga_475yr_g"}},
    "E3": {"natural_hazards": {"nh04_slope_angle_deg", "nh04_stability_class", "nh04_quality", "nh04_comment"}},
    "E4": {"natural_hazards": {"nh07_nearest_holocene_volcano_km", "nh07_volcano_name", "nh07_quality", "nh07_comment"}},
    "E5": {"natural_hazards": {"nh05_karst_present", "nh05_karst_severity", "nh05_quality", "nh05_comment"}},
    "E6": {"natural_hazards": {"nh05_mining_void_present", "nh05_subsidence_risk", "nh05_quality", "nh05_comment"}},
    "E7": {"natural_hazards": {"ns08_in_protected_area", "ns08_nearest_pa_km", "ns08_pa_name", "ns08_quality", "ns08_comment"}},
    "E8": {
        "emergency_planning": {"ep01_composite_score", "ep01_evacuation_feasible", "road_density_km_per_km2", "ep01_quality", "ep01_comment"},
        "radiological": {"pop_density_5km", "pop_total_5km"},
    },
    "E9": {"infrastructure": {"ns01_cooling_source_type", "ns01_cooling_source_name", "ns01_estimated_flow_m3s", "ns01_quality", "ns01_comment"}},
    "A1": {"human_hazards": {"hi01_nearest_airport_km", "hi01_nearest_airport_name", "hi01_flight_path_km", "hi01_quality", "hi01_comment"}},
    "A2": {"human_hazards": {"hi01_nearest_airport_km", "hi01_nearest_airport_name", "hi01_quality", "hi01_comment"}},
    "A3": {"human_hazards": {"hi01_nearest_airport_km", "hi01_nearest_airport_name", "hi01_quality", "hi01_comment"}},
    "A4": {"human_hazards": {"hi01_nearest_airport_km", "hi01_nearest_airport_name", "hi01_quality", "hi01_comment"}},
    "A5": {"human_hazards": {"hi06_nearest_military_km", "hi06_nearest_military_name", "hi06_quality", "hi06_comment"}},
    "A6": {"human_hazards": {"hi06_nearest_military_km", "hi06_nearest_military_name", "hi06_quality", "hi06_comment"}},
    "A7": {"human_hazards": {"hi02_nearest_seveso_km", "hi02_nearest_industrial_km", "hi02_quality", "hi02_comment"}},
    "A8": {"human_hazards": {"hi03_nearest_toxic_source_km", "hi03_quality", "hi03_comment"}},
    "A9": {"natural_hazards": {"nh08_distance_to_coast_km", "nh08_quality", "nh08_comment"}},
    "A10": {"natural_hazards": {"pga_475yr_g", "pga_2475yr_g", "nh01_quality", "nh01_comment"}},
    "A11": {"natural_hazards": {"nh09_flood_zone_class", "nh09_nearest_river_km", "nh09_quality", "nh09_comment"}},
    "A12": {"radiological": {"pop_density_5km", "pop_total_5km", "ri04_quality", "ri04_comment"}},
    "A13": {"infrastructure": {"ns02_nearest_substation_km", "ns02_nearest_hv_line_km", "ns02_grid_export_capacity_mw", "ns02_quality", "ns02_comment"}},
    "A14": {"infrastructure": {"ns03_nearest_rail_km", "ns03_nearest_highway_km", "ns03_nearest_waterway_km", "ns03_quality", "ns03_comment"}},
    "A15": {"infrastructure": {"ns05_buildable_area_ha", "ns05_largest_contiguous_ha", "ns05_quality", "ns05_comment"}},
    "NH-01": {"natural_hazards": {"pga_475yr_g", "pga_2475yr_g", "nh01_quality", "nh01_comment"}},
    "NH-06": {"natural_hazards": {"nh06_bearing_capacity_kpa", "nh06_depth_to_bedrock_m", "nh06_quality", "nh06_comment"}},
    "NH-08": {"natural_hazards": {"nh08_distance_to_coast_km", "nh08_storm_surge_risk", "nh08_tsunami_risk", "nh08_quality", "nh08_comment"}},
    "NH-09": {"natural_hazards": {"nh09_flood_zone_class", "nh09_nearest_river_km", "nh09_dam_break_exposure", "nh09_quality", "nh09_comment"}},
    "NH-10": {"natural_hazards": {"nh10_max_wind_speed_ms", "nh10_tornado_risk", "nh10_quality", "nh10_comment"}},
    "NH-11": {"natural_hazards": {"nh11_extreme_precip_mm", "nh11_quality", "nh11_comment"}},
    "NH-12": {"natural_hazards": {"nh12_extreme_temp_max_c", "nh12_extreme_temp_min_c", "nh12_quality", "nh12_comment"}},
    "NH-13": {"natural_hazards": {"nh13_wildfire_combustible_pct", "nh13_quality", "nh13_comment"}},
    "NH-14": {"natural_hazards": {"pga_475yr_g", "nh08_distance_to_coast_km", "nh09_flood_zone_class", "nh13_wildfire_combustible_pct", "nh14_quality", "nh14_comment"}},
    "HI-01": {"human_hazards": {"hi01_nearest_airport_km", "hi01_nearest_airport_name", "hi01_airport_count", "hi01_quality", "hi01_comment"}},
    "HI-02": {"human_hazards": {"hi02_nearest_seveso_km", "hi02_nearest_industrial_km", "hi02_quality", "hi02_comment"}},
    "HI-03": {"human_hazards": {"hi03_nearest_toxic_source_km", "hi03_quality", "hi03_comment"}},
    "HI-04": {"human_hazards": {"hi04_nearest_flammable_storage_km", "hi04_nearest_pipeline_km", "hi04_quality", "hi04_comment"}},
    "HI-05": {"human_hazards": {"hi05_hazmat_route_distance_km", "hi05_quality", "hi05_comment"}},
    "HI-06": {"human_hazards": {"hi06_nearest_military_km", "hi06_nearest_military_name", "hi06_military_count", "hi06_quality", "hi06_comment"}},
    "HI-07": {"human_hazards": {"hi07_nearest_transmitter_km", "hi07_transmitter_type", "hi07_transmitter_count", "hi07_quality", "hi07_comment"}},
    "HI-08": {"human_hazards": {"hi08_nearest_nuclear_km", "hi08_nearest_nuclear_name", "hi08_quality", "hi08_comment"}},
    "RI-01": {"radiological": {"ri01_prevailing_wind_dir", "ri01_avg_wind_speed_ms", "ri01_mixing_height_m", "ri01_quality", "ri01_comment"}},
    "RI-02": {"radiological": {"ri02_nearest_river_flow_m3s", "ri02_quality", "ri02_comment"}},
    "RI-03": {"radiological": {"ri03_aquifer_type", "ri03_groundwater_flow_dir", "ri03_quality", "ri03_comment"}},
    "RI-04": {"radiological": {"pop_density_5km", "pop_density_25km", "pop_total_80km", "ri04_quality", "ri04_comment"}},
    "RI-05": {"radiological": {"ri05_nearest_city_50k_km", "ri05_nearest_city_name", "ri05_nearest_city_pop", "ri05_quality", "ri05_comment"}},
    "RI-06": {"radiological": {"ri06_pop_growth_rate_pct", "ri06_projected_pop_25km_60yr", "ri06_quality", "ri06_comment"}},
    "EP-02": {"emergency_planning": {"road_density_km_per_km2", "has_motorway_access", "ep02_quality", "ep02_comment"}},
    "EP-03": {"emergency_planning": {"major_river_barrier", "waterway_count_epz", "ep03_quality", "ep03_comment"}},
    "EP-04": {"emergency_planning": {"hospital_count_epz", "prison_count_epz", "care_home_count_epz", "ep04_quality", "ep04_comment"}},
    "EP-05": {"emergency_planning": {"ep05_concurrent_hazard_notes", "ep05_quality", "ep05_comment"}},
    "NS-02": {"infrastructure": {"ns02_nearest_substation_km", "ns02_nearest_hv_line_km", "ns02_grid_export_capacity_mw", "ns02_quality", "ns02_comment"}},
    "NS-03": {"infrastructure": {"ns03_nearest_rail_km", "ns03_nearest_highway_km", "ns03_nearest_waterway_km", "ns03_heavy_haul_capable", "ns03_quality", "ns03_comment"}},
    "NS-04": {"infrastructure": {"ns04_dominant_land_class", "ns04_favourable_land_pct", "ns04_quality", "ns04_comment"}},
    "NS-05": {"infrastructure": {"ns05_buildable_area_ha", "ns05_largest_contiguous_ha", "ns05_quality", "ns05_comment"}},
    "NS-06": {"infrastructure": {"ns06_reusable_infra_score", "ns06_reusable_assets", "ns06_quality", "ns06_comment"}},
    "NS-07": {"infrastructure": {"ns07_env_impact_notes", "ns07_quality", "ns07_comment"}},
    "NS-08": {"infrastructure": {"ns08_ecological_natural_pct", "ns08_ecological_patch_count", "ns08_quality", "ns08_comment"}},
    "NS-09": {"infrastructure": {"ns09_socioeconomic_notes", "ns09_quality", "ns09_comment"}},
    "NS-10": {"infrastructure": {"ns10_workforce_notes", "ns10_quality", "ns10_comment"}},
    "NS-11": {"infrastructure": {"ns11_synergy_notes", "ns11_quality", "ns11_comment"}},
    "NS-12": {"infrastructure": {"ns12_regulatory_notes", "ns12_quality", "ns12_comment"}},
    "NS-13": {"infrastructure": {"ns13_laydown_suitable_ha", "ns13_laydown_largest_patch_ha", "ns13_quality", "ns13_comment"}},
}

_DOMAIN_TABLE_MAP = {
    "natural_hazards": SiteNaturalHazards,
    "human_hazards": SiteHumanHazards,
    "radiological": SiteRadiological,
    "emergency_planning": SiteEmergencyPlanning,
    "infrastructure": SiteInfrastructureV2,
}


def _row_to_dict(row: Any | None, exclude: set[str] | None = None) -> dict[str, Any]:
    """Convert an ORM row to a dict, omitting None values and internals."""
    if row is None:
        return {}
    exclude = exclude or set()
    exclude |= {"_sa_instance_state", "site", "site_id"}
    out: dict[str, Any] = {}
    for k in vars(row):
        if k.startswith("_") or k in exclude:
            continue
        v = getattr(row, k)
        if v is not None:
            out[k] = v
    return out


def _filter_enrichment(enrichment: dict[str, Any], prompt_key: str) -> dict[str, Any]:
    """Return only the enrichment fields relevant to the given criterion."""
    field_map = RELEVANT_ENRICHMENT_FIELDS.get(prompt_key)
    if field_map is None:
        return enrichment

    filtered: dict[str, Any] = {}
    for table_key, allowed_fields in field_map.items():
        table_data = enrichment.get(table_key, {})
        if not table_data:
            continue
        relevant = {k: v for k, v in table_data.items() if k in allowed_fields}
        if relevant:
            filtered[table_key] = relevant
    return filtered


def load_sites(session: Session, site_ids: list | None = None, country_codes: list[str] | None = None) -> list[Site]:
    """Load sites from the main DB, optionally filtered."""
    q = session.query(Site)
    if site_ids:
        q = q.filter(Site.site_id.in_(site_ids))
    if country_codes:
        q = q.filter(Site.country_code.in_(country_codes))
    return q.order_by(Site.country_code, Site.name).all()


def preload_site_data(site: Site, session: Session) -> dict[str, Any]:
    """Pre-load site metadata and enrichment for later per-criterion context building.

    Returns a dict with ``"header"`` (site info string) and ``"enrichment"``
    (full domain-table data), to be used with :func:`build_context_for_criterion`.
    """
    nh = session.get(SiteNaturalHazards, site.site_id)
    hh = session.get(SiteHumanHazards, site.site_id)
    ri = session.get(SiteRadiological, site.site_id)
    ep = session.get(SiteEmergencyPlanning, site.site_id)
    infra = session.get(SiteInfrastructureV2, site.site_id)

    enrichment: dict[str, Any] = {}
    for label, row in [
        ("natural_hazards", nh),
        ("human_hazards", hh),
        ("radiological", ri),
        ("emergency_planning", ep),
        ("infrastructure", infra),
    ]:
        d = _row_to_dict(row)
        if d:
            enrichment[label] = d

    header = (
        f"SITE: {site.name}\n"
        f"COUNTRY: {site.country_name} ({site.country_code})\n"
        f"COORDINATES: {site.latitude}°N, {site.longitude}°E\n"
        f"ELEVATION: {site.elevation_m or 'unknown'} m AMSL\n"
        f"STATUS: {site.status or 'unknown'}\n"
        f"INSTALLED CAPACITY: {site.installed_capacity_mw or 'unknown'} MWe\n"
        f"PLANT TYPE: {site.plant_type or 'unknown'}\n"
        f"COAL TYPE: {site.coal_type or 'unknown'}\n"
        f"REGION: {site.subnational_unit or ''}, {site.local_area or ''}\n"
        f"COOLING SOURCE: {site.cooling_water_source or 'unknown'}\n"
        f"SITE AREA: {site.site_area_ha or 'unknown'} ha\n"
        f"GRID VOLTAGE: {site.grid_voltage_kv or 'unknown'} kV\n"
        f"GRID CAPACITY: {site.grid_capacity_mw or 'unknown'} MW\n"
        f"OWNER: {site.owner_operator or 'unknown'}\n"
        f"START YEAR: {site.start_year or 'unknown'}\n"
        f"RETIRED YEAR: {site.retired_year or 'unknown'}\n"
        f"PLANNED RETIREMENT: {site.planned_retirement or 'unknown'}"
    )

    return {"header": header, "enrichment": enrichment}


def build_context_for_criterion(cached: dict[str, Any], prompt_key: str) -> str:
    """Build user-message text for a specific criterion using pre-loaded data.

    Filters enrichment to only include fields relevant to *prompt_key*,
    reducing token waste on ranking/avoidance calls.
    """
    enrichment = _filter_enrichment(cached["enrichment"], prompt_key)

    enrichment_block = ""
    if enrichment:
        enrichment_block = (
            "\n\nEXISTING ENRICHMENT DATA (from API pipeline — use as context, "
            "corroborate or challenge with your own knowledge):\n"
            + json.dumps(enrichment, indent=2, default=str)
        )

    return (
        cached["header"]
        + enrichment_block
        + "\n\nEvaluate this site for the specified criterion. Return your assessment "
        "using the provided tool."
    )


def build_site_context(site: Site, session: Session, prompt_key: str | None = None) -> str:
    """Build the user-message text for a single site, including enrichment data.

    When *prompt_key* is provided the enrichment data is filtered to only
    include fields relevant to that criterion.  For batch use, prefer
    :func:`preload_site_data` + :func:`build_context_for_criterion`.
    """
    cached = preload_site_data(site, session)
    if prompt_key is not None:
        return build_context_for_criterion(cached, prompt_key)

    enrichment = cached["enrichment"]
    enrichment_block = ""
    if enrichment:
        enrichment_block = (
            "\n\nEXISTING ENRICHMENT DATA (from API pipeline — use as context, "
            "corroborate or challenge with your own knowledge):\n"
            + json.dumps(enrichment, indent=2, default=str)
        )

    return (
        cached["header"]
        + enrichment_block
        + "\n\nEvaluate this site for the specified criterion. Return your assessment "
        "using the provided tool."
    )
