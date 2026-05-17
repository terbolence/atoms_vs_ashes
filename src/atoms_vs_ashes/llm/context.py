# man_hours: 0.2
"""SiteContextBuilder — reads main DB and assembles per-site prompt context.

All column names in ``RELEVANT_ENRICHMENT_FIELDS`` must exist on the ORM model
for the declared domain table; see :func:`validate_relevant_enrichment_fields`
and the import-time check at the bottom of this module.

The ORM (see ``src/atoms_vs_ashes/db/models.py``) uses the convention:
- Data columns: unprefixed (e.g. ``nearest_airport_km``, ``buildable_area_ha``,
  ``nearest_military_km``).
- Quality/comment/source metadata columns: prefixed by criterion family
  (e.g. ``hi01_quality``, ``ns05_comment``, ``nh02_source``).

Do NOT add made-up prefixed names to this mapping — the regression test in
``tests/test_relevant_enrichment_fields.py`` will fail the build.
"""

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
    "E1": {"natural_hazards": {"pga_475yr_g", "pga_2475yr_g", "nearest_fault_km", "fault_name", "fault_slip_rate_mm_yr", "nh02_source", "nh02_quality", "nh02_comment"}},
    "E2": {"natural_hazards": {"liquefaction_suscept", "soil_type", "groundwater_depth_m", "nh03_quality", "nh03_comment", "pga_475yr_g"}},
    "E3": {"natural_hazards": {"slope_angle_deg", "slope_stability_class", "landslide_inventory_notes", "nh04_quality", "nh04_comment"}},
    "E4": {"natural_hazards": {"nearest_holocene_volcano_km", "volcano_name", "nh07_quality", "nh07_comment"}},
    "E5": {"natural_hazards": {"karst_present", "karst_severity", "karst_formation_type", "nh05_quality", "nh05_comment"}},
    "E6": {"natural_hazards": {"mining_void_present", "subsidence_risk_class", "collapse_mechanism", "nh05b_quality", "nh05b_comment"}},
    "E7": {"infrastructure": {"n2k_overlap", "n2k_nearest_distance_km", "n2k_sensitivity_class", "wdpa_overlap", "wdpa_nearest_distance_km", "wdpa_sensitivity_class", "ns08_quality", "ns08_comment", "wdpa_quality", "wdpa_comment"}},
    "E8": {
        "emergency_planning": {
            "ep01_composite_score", "ep01_evacuation_feasible", "ep01_terrain_score",
            "ep01_road_score", "ep01_special_pop_score", "ep01_geography_score", "ep01_population_score",
            "road_density_km_per_km2", "has_motorway_access",
            "waterway_count_epz", "major_river_barrier",
            "hospital_count_epz", "prison_count_epz", "care_home_count_epz",
            "ep01_quality", "ep01_comment",
        },
        "radiological": {"pop_density_5km", "pop_total_5km"},
    },
    "E9": {"infrastructure": {"cooling_source_type", "cooling_source_name", "cooling_distance_km", "cooling_flow_m3s", "water_stress_score", "water_stress_label", "ns01_quality", "ns01_comment"}},
    "A1": {"human_hazards": {"nearest_airport_km", "nearest_airport_name", "flight_path_distance_km", "hi01_quality", "hi01_comment"}},
    "A2": {"human_hazards": {"nearest_airport_km", "nearest_airport_name", "hi01_quality", "hi01_comment"}},
    "A3": {"human_hazards": {"nearest_airport_km", "nearest_airport_name", "hi01_quality", "hi01_comment"}},
    "A4": {"human_hazards": {"nearest_airport_km", "nearest_airport_name", "hi01_quality", "hi01_comment"}},
    "A5": {"human_hazards": {"nearest_military_km", "nearest_military_name", "military_count", "hi06_quality", "hi06_comment"}},
    "A6": {"human_hazards": {"nearest_military_km", "nearest_military_name", "military_count", "hi06_quality", "hi06_comment"}},
    "A7": {"human_hazards": {"nearest_seveso_km", "nearest_industrial_km", "hi02_quality", "hi02_comment"}},
    "A8": {"human_hazards": {"nearest_toxic_source_km", "hi03_quality", "hi03_comment"}},
    "A9": {"natural_hazards": {"distance_to_coast_km", "nh08_quality", "nh08_comment"}},
    "A10": {"natural_hazards": {"pga_475yr_g", "pga_2475yr_g", "nh01_quality", "nh01_comment"}},
    "A11": {"natural_hazards": {"flood_zone_class", "nearest_river_km", "nh09_quality", "nh09_comment"}},
    "A12": {"radiological": {"nearest_city_50k_km", "nearest_city_name", "nearest_city_pop", "ri05_quality", "ri05_comment"}},
    "A13": {"infrastructure": {"nearest_substation_km", "nearest_hv_line_km", "grid_export_capacity_mw", "ns02_quality", "ns02_comment"}},
    "A14": {"infrastructure": {"nearest_rail_km", "nearest_highway_km", "nearest_waterway_km", "ns03_quality", "ns03_comment"}},
    "A15": {"infrastructure": {"favourable_area_ha", "favourable_area_method", "patch_count", "ns05_quality", "ns05_comment"}},
    "NH-01": {"natural_hazards": {"pga_475yr_g", "pga_2475yr_g", "nh01_quality", "nh01_comment"}},
    "NH-06": {"natural_hazards": {"bearing_capacity_kpa", "depth_to_bedrock_m", "nh06_quality", "nh06_comment"}},
    "NH-08": {"natural_hazards": {"distance_to_coast_km", "storm_surge_risk", "tsunami_risk", "nh08_quality", "nh08_comment"}},
    "NH-09": {"natural_hazards": {"flood_zone_class", "nearest_river_km", "dam_break_exposure", "nh09_quality", "nh09_comment"}},
    "NH-10": {"natural_hazards": {"max_wind_speed_ms", "nh10_quality", "nh10_comment"}},
    "NH-11": {"natural_hazards": {"extreme_precip_mm", "nh11_quality", "nh11_comment"}},
    "NH-12": {"natural_hazards": {"extreme_temp_max_c", "extreme_temp_min_c", "nh12_quality", "nh12_comment"}},
    "NH-13": {"natural_hazards": {"wildfire_combustible_pct", "wildfire_wui_ha", "nh13_quality", "nh13_comment"}},
    "NH-14": {"natural_hazards": {"pga_475yr_g", "distance_to_coast_km", "flood_zone_class", "wildfire_combustible_pct", "combined_hazard_notes", "nh14_quality", "nh14_comment"}},
    "HI-01": {"human_hazards": {"nearest_airport_km", "nearest_airport_name", "nearest_airport_type", "flight_path_distance_km", "airport_count", "hi01_quality", "hi01_comment"}},
    "HI-02": {"human_hazards": {"nearest_seveso_km", "nearest_industrial_km", "hi02_quality", "hi02_comment"}},
    "HI-03": {"human_hazards": {"nearest_toxic_source_km", "hi03_quality", "hi03_comment"}},
    "HI-04": {"human_hazards": {"nearest_flammable_storage_km", "nearest_pipeline_km", "hi04_quality", "hi04_comment"}},
    "HI-05": {"human_hazards": {"hazmat_route_distance_km", "hi05_quality", "hi05_comment"}},
    "HI-06": {"human_hazards": {"nearest_military_km", "nearest_military_name", "military_count", "hi06_quality", "hi06_comment"}},
    "HI-07": {"human_hazards": {"nearest_transmitter_km", "transmitter_type", "transmitter_count", "hi07_quality", "hi07_comment"}},
    "HI-08": {"human_hazards": {"nearest_nuclear_km", "nearest_nuclear_name", "hi08_quality", "hi08_comment"}},
    "RI-01": {"radiological": {"prevailing_wind_dir", "avg_wind_speed_ms", "mixing_height_m", "ri01_quality", "ri01_comment"}},
    "RI-02": {"radiological": {"nearest_river_flow_m3s", "ri02_quality", "ri02_comment"}},
    "RI-03": {"radiological": {"aquifer_type", "groundwater_flow_dir", "ri03_quality", "ri03_comment"}},
    "RI-04": {"radiological": {"pop_density_5km", "pop_density_25km", "pop_total_80km", "ri04_quality", "ri04_comment"}},
    "RI-05": {"radiological": {"nearest_city_50k_km", "nearest_city_name", "nearest_city_pop", "ri05_quality", "ri05_comment"}},
    "RI-06": {"radiological": {"pop_growth_rate_pct", "projected_pop_25km_60yr", "ri06_quality", "ri06_comment"}},
    "EP-02": {"emergency_planning": {"road_density_km_per_km2", "total_road_km", "has_motorway_access", "ep02_quality", "ep02_comment"}},
    "EP-03": {"emergency_planning": {"major_river_barrier", "waterway_count_epz", "ep03_quality", "ep03_comment"}},
    "EP-04": {"emergency_planning": {"hospital_count_epz", "prison_count_epz", "care_home_count_epz", "ep04_quality", "ep04_comment"}},
    "EP-05": {"emergency_planning": {"concurrent_hazard_notes", "ep05_quality", "ep05_comment"}},
    "NS-02": {"infrastructure": {"nearest_substation_km", "substation_name", "nearest_hv_line_km", "hv_line_voltage_kv", "hv_line_count", "substation_count", "grid_export_capacity_mw", "ns02_quality", "ns02_comment"}},
    "NS-03": {"infrastructure": {"nearest_rail_km", "nearest_highway_km", "nearest_waterway_km", "heavy_haul_capable", "ns03_quality", "ns03_comment"}},
    "NS-04": {"infrastructure": {"dominant_land_class", "dominant_class_pct", "favourable_land_pct", "moderate_land_pct", "unfavourable_land_pct", "ns04_quality", "ns04_comment"}},
    "NS-05": {"infrastructure": {"favourable_area_ha", "favourable_area_method", "patch_count", "ns05_quality", "ns05_comment"}},
    "NS-06": {"infrastructure": {"reusable_infra_score", "ns06_quality", "ns06_comment"}},
    "NS-07": {"infrastructure": {"env_impact_notes", "ns07_quality", "ns07_comment"}},
    "NS-08": {"infrastructure": {"ecological_natural_pct", "ecological_patch_count", "ecological_largest_patch_ha", "n2k_overlap", "n2k_nearest_distance_km", "n2k_sensitivity_class", "wdpa_overlap", "wdpa_nearest_distance_km", "wdpa_sensitivity_class", "ns08_quality", "ns08_comment", "wdpa_quality", "wdpa_comment"}},
    "NS-09": {"infrastructure": {"ns09_quality", "ns09_comment"}},
    "NS-10": {"infrastructure": {"ns10_quality", "ns10_comment"}},
    "NS-11": {"infrastructure": {"ns11_quality", "ns11_comment"}},
    "NS-12": {"infrastructure": {"ns12_quality", "ns12_comment"}},
    "NS-13": {"infrastructure": {"laydown_suitable_ha", "laydown_largest_patch_ha", "ns13_quality", "ns13_comment"}},
}

_DOMAIN_TABLE_MAP = {
    "natural_hazards": SiteNaturalHazards,
    "human_hazards": SiteHumanHazards,
    "radiological": SiteRadiological,
    "emergency_planning": SiteEmergencyPlanning,
    "infrastructure": SiteInfrastructureV2,
}


def validate_relevant_enrichment_fields(
    mapping: dict[str, dict[str, set[str]]] | None = None,
) -> list[tuple[str, str, str]]:
    """Return a list of ``(prompt_key, domain, field)`` that don't map to a real ORM column.

    A healthy mapping returns an empty list. This is the programmatic guard that
    replaces the old silent-drop behaviour: callers (import-time assertion below,
    regression test, coverage script) use this to fail loudly.
    """
    mapping = mapping if mapping is not None else RELEVANT_ENRICHMENT_FIELDS
    problems: list[tuple[str, str, str]] = []
    for prompt_key, domains in mapping.items():
        for domain, fields in domains.items():
            model = _DOMAIN_TABLE_MAP.get(domain)
            if model is None:
                for field in sorted(fields):
                    problems.append((prompt_key, domain, f"<unknown domain: {domain}>"))
                continue
            real_cols = {c.key for c in model.__table__.columns}
            for field in sorted(fields):
                if field not in real_cols:
                    problems.append((prompt_key, domain, field))
    return problems


_wiring_problems = validate_relevant_enrichment_fields()
if _wiring_problems:
    _preview = "; ".join(
        f"{pk}.{dom}.{fld}" for pk, dom, fld in _wiring_problems[:5]
    )
    _extra = "" if len(_wiring_problems) <= 5 else f" (+{len(_wiring_problems) - 5} more)"
    raise RuntimeError(
        "RELEVANT_ENRICHMENT_FIELDS contains phantom columns not present on the "
        f"ORM models: {_preview}{_extra}. Run "
        "`python -c \"from atoms_vs_ashes.llm.context import validate_relevant_enrichment_fields as v; "
        "print(v())\"` for the full list."
    )


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


def compute_enrichment_coverage(cached: dict[str, Any], prompt_key: str) -> dict[str, Any]:
    """Compute enrichment coverage for a site/criterion pair.

    Returns a dict with expected_fields, available_fields, and coverage_pct
    suitable for audit logging.
    """
    field_map = RELEVANT_ENRICHMENT_FIELDS.get(prompt_key)
    if field_map is None:
        return {"expected_fields": [], "available_fields": [], "coverage_pct": 1.0}

    enrichment = cached.get("enrichment", {})
    expected: list[str] = []
    available: list[str] = []

    for table_key, allowed_fields in field_map.items():
        quality_and_comment = {f for f in allowed_fields if f.endswith("_quality") or f.endswith("_comment")}
        data_fields = allowed_fields - quality_and_comment
        table_data = enrichment.get(table_key, {})
        for field in sorted(data_fields):
            expected.append(field)
            if table_data.get(field) is not None:
                available.append(field)

    coverage = len(available) / len(expected) if expected else 1.0
    return {
        "expected_fields": expected,
        "available_fields": available,
        "coverage_pct": round(coverage, 2),
    }


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

    return {
        "header": header,
        "enrichment": enrichment,
        "country_code": site.country_code,
    }


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
