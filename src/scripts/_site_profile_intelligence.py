# man_hours: 1.6
"""Criterion-by-criterion evidence extraction from a site bundle.

Given a ``site_bundle.v1`` JSON payload, this module returns the raw
measured values, units, ranking score, MC bracket, and confidence for
every criterion that has data. The result feeds the site profile
markdown writer so the report quotes real values, not just 0-10
scores.
"""

from __future__ import annotations

from typing import Any

CRITERIA_FAMILY = "criterion_families"

# Every criterion that has a structured measurement column. Each entry
# carries the family table that holds the raw row, plus the
# (column, unit, label) tuples we surface in prose. A few entries pull
# additional context from JSON columns (PGA hazard model, Natura 2000
# nearest site, WDPA designation).

CRITERION_FIELDS: dict[str, dict[str, Any]] = {
    "NH-01": {
        "family_key": "natural_hazards",
        "fields": [
            ("pga_475yr_g", "g", "PGA at 475-year return period"),
            ("pga_2475yr_g", "g", "PGA at 2,475-year return period"),
        ],
        "json_extras": [
            ("spectral_accel_json", "model_name", "hazard model"),
            ("spectral_accel_json", "vs30_reference", "Vs30 reference (m/s)"),
        ],
    },
    "NH-02": {
        "family_key": "natural_hazards",
        "fields": [
            ("nearest_fault_km", "km", "nearest mapped capable fault"),
            ("fault_slip_rate_mm_yr", "mm/yr", "fault slip rate"),
        ],
        "context_fields": [("fault_name", "fault name")],
    },
    "NH-03": {
        "family_key": "natural_hazards",
        "fields": [
            ("groundwater_depth_m", "m", "groundwater depth"),
        ],
        "context_fields": [
            ("liquefaction_suscept", "liquefaction susceptibility"),
            ("soil_type", "dominant soil type"),
        ],
    },
    "NH-04": {
        "family_key": "natural_hazards",
        "fields": [
            ("slope_angle_deg", "deg", "site slope (CopDEM)"),
            ("nh04_dem_cog_slope_max_deg", "deg", "max slope in 1 km box (CopDEM)"),
            ("nh04_gee_slope_max_deg", "deg", "max slope (Earth Engine)"),
        ],
        "context_fields": [
            ("slope_stability_class", "slope stability class"),
            ("nh04_gee_terrain_class", "Earth Engine terrain class"),
        ],
    },
    "NH-05": {
        "family_key": "natural_hazards",
        "context_fields": [
            ("karst_present", "karst present"),
            ("karst_severity", "karst severity"),
            ("karst_formation_type", "formation type"),
        ],
    },
    "NH-05b": {
        "family_key": "natural_hazards",
        "context_fields": [
            ("mining_void_present", "mining void present"),
            ("subsidence_risk_class", "subsidence risk class"),
            ("collapse_mechanism", "collapse mechanism"),
        ],
    },
    "NH-06": {
        "family_key": "natural_hazards",
        "fields": [
            ("bearing_capacity_kpa", "kPa", "bearing capacity"),
            ("depth_to_bedrock_m", "m", "depth to bedrock"),
        ],
    },
    "NH-07": {
        "family_key": "natural_hazards",
        "fields": [
            ("nearest_holocene_volcano_km", "km", "nearest Holocene volcano"),
        ],
        "context_fields": [
            ("volcano_name", "volcano name"),
            ("nh07_hazard_class", "volcanic hazard class"),
        ],
    },
    "NH-08": {
        "family_key": "natural_hazards",
        "fields": [
            ("distance_to_coast_km", "km", "distance to coast"),
        ],
        "context_fields": [
            ("storm_surge_risk", "storm surge risk"),
            ("tsunami_risk", "tsunami risk"),
        ],
    },
    "NH-09": {
        "family_key": "natural_hazards",
        "fields": [
            ("nearest_river_km", "km", "nearest river"),
        ],
        "context_fields": [
            ("flood_zone_class", "flood zone class"),
            ("dam_break_exposure", "dam-break exposure"),
        ],
    },
    "NH-10": {
        "family_key": "natural_hazards",
        "fields": [("max_wind_speed_ms", "m/s", "design wind speed")],
    },
    "NH-11": {
        "family_key": "natural_hazards",
        "fields": [
            ("extreme_precip_mm", "mm", "extreme daily precipitation"),
            ("mean_annual_precip_mm", "mm/yr", "mean annual precipitation"),
        ],
    },
    "NH-12": {
        "family_key": "natural_hazards",
        "fields": [
            ("extreme_temp_max_c", "deg C", "extreme high temperature"),
            ("extreme_temp_min_c", "deg C", "extreme low temperature"),
        ],
    },
    "NH-13": {
        "family_key": "natural_hazards",
        "fields": [
            ("wildfire_combustible_pct", "%", "combustible land cover share"),
            ("wildfire_wui_ha", "ha", "wildland-urban interface area"),
            ("nh13_gee_burn_fraction_mean", "fraction", "mean MODIS burn fraction"),
        ],
        "context_fields": [
            ("nh13_gee_fire_recurrence_class", "fire recurrence class"),
        ],
    },
    "HI-01": {
        "family_key": "human_hazards",
        "fields": [
            ("nearest_airport_km", "km", "nearest airport"),
            ("flight_path_distance_km", "km", "nearest flight path"),
            ("airport_count", "count", "airports within search radius"),
        ],
        "context_fields": [
            ("nearest_airport_name", "airport name"),
            ("nearest_airport_type", "airport type"),
        ],
    },
    "HI-02": {
        "family_key": "human_hazards",
        "fields": [
            ("nearest_seveso_km", "km", "nearest Seveso establishment"),
            ("nearest_industrial_km", "km", "nearest industrial site"),
        ],
    },
    "HI-03": {
        "family_key": "human_hazards",
        "fields": [("nearest_toxic_source_km", "km", "nearest toxic source")],
    },
    "HI-04": {
        "family_key": "human_hazards",
        "fields": [
            ("nearest_flammable_storage_km", "km", "nearest flammable storage"),
            ("nearest_pipeline_km", "km", "nearest hazardous pipeline"),
        ],
    },
    "HI-05": {
        "family_key": "human_hazards",
        "fields": [("hazmat_route_distance_km", "km", "nearest hazmat route")],
    },
    "HI-06": {
        "family_key": "human_hazards",
        "fields": [
            ("nearest_military_km", "km", "nearest military installation"),
            ("military_count", "count", "military installations within radius"),
        ],
        "context_fields": [("nearest_military_name", "installation name")],
    },
    "HI-07": {
        "family_key": "human_hazards",
        "fields": [
            ("nearest_transmitter_km", "km", "nearest high-power transmitter"),
            ("transmitter_count", "count", "transmitters within radius"),
        ],
        "context_fields": [("transmitter_type", "transmitter type")],
    },
    "HI-08": {
        "family_key": "human_hazards",
        "fields": [
            ("nearest_nuclear_km", "km", "nearest other nuclear installation"),
        ],
        "context_fields": [("nearest_nuclear_name", "facility name")],
    },
    "RI-01": {
        "family_key": "radiological",
        "fields": [
            ("avg_wind_speed_ms", "m/s", "annual mean wind speed"),
            ("mixing_height_m", "m", "atmospheric mixing height"),
        ],
        "context_fields": [("prevailing_wind_dir", "prevailing wind direction")],
    },
    "RI-02": {
        "family_key": "radiological",
        "fields": [
            ("nearest_river_flow_m3s", "m3/s", "nearest river mean flow"),
        ],
    },
    "RI-03": {
        "family_key": "radiological",
        "context_fields": [
            ("aquifer_type", "aquifer type"),
            ("groundwater_flow_dir", "groundwater flow direction"),
        ],
    },
    "RI-04": {
        "family_key": "radiological",
        "fields": [
            ("pop_density_5km", "/km2", "population density within 5 km"),
            ("pop_density_16km", "/km2", "population density within 16 km"),
            ("pop_density_25km", "/km2", "population density within 25 km"),
            ("pop_density_80km", "/km2", "population density within 80 km"),
            ("pop_total_25km", "people", "population within 25 km"),
        ],
    },
    "RI-05": {
        "family_key": "radiological",
        "fields": [
            ("nearest_city_50k_km", "km", "nearest city above 50k people"),
            ("nearest_city_pop", "people", "nearest city population"),
        ],
        "context_fields": [("nearest_city_name", "city name")],
    },
    "RI-06": {
        "family_key": "radiological",
        "fields": [
            ("pop_growth_rate_pct", "%/yr", "annual population growth rate"),
            ("projected_pop_25km_60yr", "people", "projected population at 25 km in 60 yr"),
        ],
    },
    "EP-01": {
        "family_key": "emergency_planning",
        "fields": [
            ("ep01_composite_score", "/100", "EP feasibility composite"),
            ("ep01_road_score", "/100", "road sub-score"),
            ("ep01_special_pop_score", "/100", "special-population sub-score"),
            ("ep01_geography_score", "/100", "geography sub-score"),
            ("ep01_population_score", "/100", "population sub-score"),
        ],
        "context_fields": [("ep01_evacuation_feasible", "evacuation feasible")],
    },
    "EP-02": {
        "family_key": "emergency_planning",
        "fields": [
            ("road_density_km_per_km2", "km/km2", "road density in EPZ"),
            ("total_road_km", "km", "road length in EPZ"),
        ],
        "context_fields": [("has_motorway_access", "motorway access")],
    },
    "EP-03": {
        "family_key": "emergency_planning",
        "fields": [
            ("ep03_gee_relief_16km_m", "m", "16-km elevation relief"),
            ("waterway_count_epz", "count", "waterways crossing EPZ"),
        ],
        "context_fields": [("major_river_barrier", "major river barrier")],
    },
    "EP-04": {
        "family_key": "emergency_planning",
        "fields": [
            ("hospital_count_epz", "count", "hospitals in EPZ"),
            ("prison_count_epz", "count", "prisons in EPZ"),
            ("care_home_count_epz", "count", "care homes in EPZ"),
        ],
    },
    "NS-01": {
        "family_key": "infrastructure",
        "fields": [
            ("cooling_distance_km", "km", "distance to cooling source"),
            ("cooling_flow_m3s", "m3/s", "cooling source flow"),
        ],
        "context_fields": [
            ("cooling_source_type", "cooling source type"),
            ("cooling_source_name", "cooling source name"),
            ("water_stress_label", "water stress label"),
        ],
    },
    "NS-02": {
        "family_key": "infrastructure",
        "fields": [
            ("nearest_substation_km", "km", "nearest substation"),
            ("nearest_hv_line_km", "km", "nearest high-voltage line"),
            ("hv_line_voltage_kv", "kV", "highest nearby line voltage"),
            ("grid_export_capacity_mw", "MW", "grid export capacity"),
            ("substation_count", "count", "substations within radius"),
            ("hv_line_count", "count", "HV lines within radius"),
        ],
        "context_fields": [("substation_name", "substation name")],
    },
    "NS-03": {
        "family_key": "infrastructure",
        "fields": [
            ("nearest_highway_km", "km", "nearest highway"),
            ("nearest_rail_km", "km", "nearest rail line"),
            ("nearest_waterway_km", "km", "nearest waterway"),
        ],
        "context_fields": [("heavy_haul_capable", "heavy-haul capable")],
    },
    "NS-04": {
        "family_key": "infrastructure",
        "fields": [
            ("favourable_land_pct", "%", "favourable land cover"),
            ("moderate_land_pct", "%", "moderate land cover"),
            ("unfavourable_land_pct", "%", "unfavourable land cover"),
            ("favourable_area_ha", "ha", "favourable area"),
        ],
        "context_fields": [
            ("dominant_land_class", "dominant CORINE land class"),
            ("ns04_gee_terrain_class", "Earth Engine terrain class"),
        ],
    },
    "NS-05": {
        "family_key": "infrastructure",
        "fields": [
            ("buildable_area_ha", "ha", "buildable area"),
            ("largest_contiguous_ha", "ha", "largest contiguous patch"),
            ("patch_count", "count", "buildable patch count"),
        ],
    },
    "NS-06": {
        "family_key": "infrastructure",
        "fields": [
            ("reusable_infra_score", "/5", "reusable infrastructure score"),
            ("ns06_gee_built_fraction", "fraction", "built-up land fraction"),
        ],
        "context_fields": [("ns06_gee_demolition_class", "demolition class")],
    },
    "NS-08": {
        "family_key": "infrastructure",
        "fields": [
            ("ecological_natural_pct", "%", "natural land cover (CORINE)"),
            ("n2k_nearest_distance_km", "km", "distance to nearest Natura 2000 site"),
            ("wdpa_nearest_distance_km", "km", "distance to nearest WDPA area"),
        ],
        "context_fields": [
            ("n2k_overlap", "Natura 2000 overlap"),
            ("n2k_sensitivity_class", "Natura 2000 sensitivity class"),
            ("wdpa_overlap", "WDPA overlap"),
            ("wdpa_sensitivity_class", "WDPA sensitivity class"),
        ],
        "json_extras": [
            ("n2k_result_json", "n2k_nearest_sitename", "nearest Natura 2000 site"),
            ("n2k_result_json", "n2k_sites_within_5km", "Natura 2000 sites within 5 km"),
            ("wdpa_result_json", "wdpa_nearest_designation", "nearest WDPA designation"),
        ],
    },
    "NS-13": {
        "family_key": "infrastructure",
        "fields": [
            ("laydown_suitable_ha", "ha", "laydown-suitable area"),
            ("laydown_largest_patch_ha", "ha", "largest laydown patch"),
        ],
    },
}


def _fmt(value: Any, unit: str) -> str:
    if value is None:
        return "no data"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        if unit == "count" or unit == "people":
            number = f"{int(value):,}"
        elif abs(value) >= 1000:
            number = f"{value:,.0f}"
        elif abs(value) >= 10:
            number = f"{value:.1f}"
        else:
            number = f"{value:.3f}".rstrip("0").rstrip(".")
        return number if unit in ("count", "") else f"{number} {unit}"
    return str(value)


def _read_json_extra(family_dict: dict[str, Any], col: str, key: str) -> Any:
    payload = (family_dict or {}).get(col)
    if isinstance(payload, dict):
        return payload.get(key)
    return None


def evidence_for(criterion_id: str, families: dict[str, Any]) -> dict[str, Any]:
    """Return measured values + context for one criterion id.

    The returned dict always contains a ``signals`` list of bullet
    fragments. ``signals`` is empty when the criterion is not in the
    structured registry (typically the LLM-derived ranking criteria
    NS-09 to NS-12 or BF-01/02). Callers can fall back to the ranking
    score and justification in that case.
    """
    spec = CRITERION_FIELDS.get(criterion_id)
    if not spec:
        return {"signals": [], "signal_count": 0, "family_key": None}
    family_dict = families.get(spec["family_key"]) or {}
    bits: list[str] = []
    for col, unit, label in spec.get("fields", []):
        value = family_dict.get(col)
        if value in (None, ""):
            continue
        bits.append(f"{label} {_fmt(value, unit)}")
    for col, label in spec.get("context_fields", []):
        value = family_dict.get(col)
        if value in (None, ""):
            continue
        bits.append(f"{label}: {_fmt(value, '')}")
    for col, key, label in spec.get("json_extras", []):
        value = _read_json_extra(family_dict, col, key)
        if value in (None, ""):
            continue
        bits.append(f"{label}: {_fmt(value, '')}")
    return {
        "signals": bits,
        "signal_count": len(bits),
        "family_key": spec["family_key"],
    }


def quality_for(criterion_id: str, families: dict[str, Any]) -> str | None:
    """Return the ``*_quality`` flag for one criterion if present."""
    spec = CRITERION_FIELDS.get(criterion_id)
    if not spec:
        return None
    family_dict = families.get(spec["family_key"]) or {}
    code = criterion_id.lower().replace("-", "")
    return family_dict.get(f"{code}_quality")


__all__ = ["CRITERION_FIELDS", "evidence_for", "quality_for"]
