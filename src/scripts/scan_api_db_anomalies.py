#!/usr/bin/env python
# man_hours: 3.5
"""Phase 1 anomaly sweep against the *live* ``atoms_vs_ashes`` API DB.

Run modes
---------

``--dry-run`` (default behaviour when the flag is set):
    Read-only.  Scans every check, classifies findings as
    ``auto_fix`` or ``escalate`` and writes the consolidated report.
    No DB writes.

``--apply``:
    Same scan, but for findings classified ``auto_fix`` the deterministic
    fix is applied IN PLACE to ``atoms_vs_ashes``, with one ``audit_log``
    row per change.  Escalations are still report-only.

Bounds source
-------------

Bounds and cross-check rules are encoded directly in this file as
"engineering common sense" (see plan
``/Users/.../data_fusion_strategy_plan_bf292f3e.plan.md``, Phase 1).
``report/business_logic.md`` (Phase 3) will adopt and formalise them.

Reporting
---------

A single Markdown file is produced::

    audit/post_processing/02_data_verification/<date>_api_db_anomalies.md

It is overwritten on each run.  When ``--apply`` is set the report
includes the rows that were modified, with before/after values.

JSON / raw-response triangulation
---------------------------------

Several checks join scalar columns against the JSONB columns:

- ``site_natural_hazards.spectral_accel_json`` (EFEHR PGA payload)
- ``site_infrastructure_v2.n2k_result_json`` (Natura 2000 payload)
- ``site_infrastructure_v2.wdpa_result_json`` (WDPA payload)
- ``site_raw_responses.response_body`` (per-connector raw API JSON)

When the persisted scalar diverges from the source-of-truth JSON value
by more than the per-check tolerance the row is reported as
``parser_bug`` / ``unit_mismatch`` / ``dropped_field`` (see ``kind``
field on each anomaly).
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from atoms_vs_ashes.config import Settings


REPORT_PATH = (
    PROJECT_ROOT
    / "audit"
    / "post_processing"
    / "02_data_verification"
    / "20260421_api_db_anomalies.md"
)

# A finding's "action" is set by the check definition itself.
ACTION_AUTOFIX = "auto_fix"
ACTION_ESCALATE = "escalate"

# Common-sense bounds (engineering judgement; full formal version lives in
# Phase 3 ``report/business_logic.md``).  Numbers reflect "physically
# possible at any candidate coal/SMR site in continental Europe / Türkiye".
BOUNDS: dict[str, dict[str, Any]] = {
    # NH-01
    "pga_475yr_g":          {"min": 0.0,    "max": 1.5,    "unit": "g"},
    "pga_2475yr_g":         {"min": 0.0,    "max": 3.0,    "unit": "g"},
    # NH-02
    "nearest_fault_km":     {"min": 0.0,    "max": 1000.0, "unit": "km"},
    "fault_slip_rate_mm_yr":{"min": 0.0,    "max": 100.0,  "unit": "mm/yr"},
    # NH-03
    "groundwater_depth_m":  {"min": 0.0,    "max": 500.0,  "unit": "m"},
    # NH-04
    "slope_angle_deg":      {"min": 0.0,    "max": 25.0,   "unit": "deg",
                             "implausible_above": 25.0,
                             "comment": "IAEA SSG-9 ranks > 25 deg as severe"},
    # NH-06
    "bearing_capacity_kpa": {"min": 30.0,   "max": 500.0,  "unit": "kPa"},
    "depth_to_bedrock_m":   {"min": 0.0,    "max": 200.0,  "unit": "m"},
    # NH-07
    "nearest_holocene_volcano_km": {"min": 0.0, "max": 5000.0, "unit": "km"},
    # NH-08 / NH-09
    "distance_to_coast_km": {"min": 0.0,    "max": 2000.0, "unit": "km"},
    "nearest_river_km":     {"min": 0.0,    "max": 200.0,  "unit": "km"},
    # NH-10 / NH-12
    "max_wind_speed_ms":    {"min": 0.0,    "max": 80.0,   "unit": "m/s"},
    "extreme_temp_max_c":   {"min": -50.0,  "max": 60.0,   "unit": "C"},
    "extreme_temp_min_c":   {"min": -90.0,  "max": 50.0,   "unit": "C"},
    # NH-11
    "extreme_precip_mm":    {"min": 0.0,    "max": 1500.0, "unit": "mm/day"},
    "mean_annual_precip_mm":{"min": 0.0,    "max": 5000.0, "unit": "mm/yr"},
    # NH-13
    "wildfire_combustible_pct": {"min": 0.0,"max": 100.0,  "unit": "%"},
    "wildfire_wui_ha":          {"min": 0.0,"max": 100000.0,"unit": "ha"},
    # HI-01..HI-08
    "nearest_airport_km":         {"min": 0.0, "max": 500.0, "unit": "km"},
    "nearest_seveso_km":          {"min": 0.0, "max": 500.0, "unit": "km"},
    "nearest_industrial_km":      {"min": 0.0, "max": 500.0, "unit": "km"},
    "nearest_toxic_source_km":    {"min": 0.0, "max": 500.0, "unit": "km"},
    "nearest_flammable_storage_km":{"min": 0.0,"max": 500.0, "unit": "km"},
    "nearest_pipeline_km":        {"min": 0.0, "max": 500.0, "unit": "km"},
    "hazmat_route_distance_km":   {"min": 0.0, "max": 500.0, "unit": "km"},
    "nearest_military_km":        {"min": 0.0, "max": 500.0, "unit": "km"},
    "nearest_transmitter_km":     {"min": 0.0, "max": 500.0, "unit": "km"},
    "nearest_nuclear_km":         {"min": 0.0, "max": 5000.0,"unit": "km"},
    # RI-04 / RI-05 / RI-06
    "pop_density_5km":      {"min": 0.0,    "max": 50000.0, "unit": "/km2"},
    "pop_density_16km":     {"min": 0.0,    "max": 50000.0, "unit": "/km2"},
    "pop_density_25km":     {"min": 0.0,    "max": 50000.0, "unit": "/km2"},
    "pop_density_80km":     {"min": 0.0,    "max": 50000.0, "unit": "/km2"},
    "nearest_city_50k_km":  {"min": 0.0,    "max": 500.0,   "unit": "km"},
    "pop_growth_rate_pct":  {"min": -10.0,  "max": 15.0,    "unit": "%/yr"},
    # RI-01
    "avg_wind_speed_ms":    {"min": 0.0,    "max": 25.0,    "unit": "m/s"},
    "mixing_height_m":      {"min": 100.0,  "max": 5000.0,  "unit": "m"},
    # RI-02
    "nearest_river_flow_m3s":{"min": 0.0,   "max": 50000.0, "unit": "m3/s"},
    # NS-01
    "cooling_distance_km":  {"min": 0.0,    "max": 50.0,    "unit": "km"},
    "cooling_flow_m3s":     {"min": 0.0,    "max": 100000.0,"unit": "m3/s"},
    "water_stress_score":   {"min": 0.0,    "max": 5.0,     "unit": "WRI"},
    # NS-02
    "nearest_substation_km":{"min": 0.0,    "max": 100.0,   "unit": "km"},
    "nearest_hv_line_km":   {"min": 0.0,    "max": 100.0,   "unit": "km"},
    "hv_line_voltage_kv":   {"min": 0,      "max": 800,     "unit": "kV"},
    "grid_export_capacity_mw":{"min": 0.0,  "max": 20000.0, "unit": "MW"},
    # NS-03
    "nearest_highway_km":   {"min": 0.0,    "max": 200.0,   "unit": "km"},
    "nearest_rail_km":      {"min": 0.0,    "max": 500.0,   "unit": "km"},
    "nearest_waterway_km":  {"min": 0.0,    "max": 500.0,   "unit": "km"},
    # NS-04
    "dominant_class_pct":   {"min": 0.0,    "max": 100.0,   "unit": "%"},
    "favourable_land_pct":  {"min": 0.0,    "max": 100.0,   "unit": "%"},
    "moderate_land_pct":    {"min": 0.0,    "max": 100.0,   "unit": "%"},
    "unfavourable_land_pct":{"min": 0.0,    "max": 100.0,   "unit": "%"},
    "favourable_area_ha":   {"min": 0.0,    "max": 50000.0, "unit": "ha"},
    # NS-05
    "buildable_area_ha":    {"min": 0.0,    "max": 50000.0, "unit": "ha"},
    "largest_contiguous_ha":{"min": 0.0,    "max": 50000.0, "unit": "ha"},
    # NS-08
    "n2k_nearest_distance_km":  {"min": 0.0, "max": 500.0,  "unit": "km"},
    "wdpa_nearest_distance_km": {"min": 0.0, "max": 500.0,  "unit": "km"},
    # NS-13
    "laydown_suitable_ha":      {"min": 0.0, "max": 50000.0,"unit": "ha"},
    "laydown_largest_patch_ha": {"min": 0.0, "max": 50000.0,"unit": "ha"},
    # EP-02
    "road_density_km_per_km2":  {"min": 0.0, "max": 50.0,   "unit": "km/km2"},
    "total_road_km":            {"min": 0.0, "max": 100000.0,"unit": "km"},
    # EP-04
    "hospital_count_epz":       {"min": 0,   "max": 5000,   "unit": "count"},
    "prison_count_epz":         {"min": 0,   "max": 5000,   "unit": "count"},
    "care_home_count_epz":      {"min": 0,   "max": 5000,   "unit": "count"},
    # EP-03
    "ep03_gee_relief_16km_m":   {"min": 0.0, "max": 5000.0, "unit": "m"},
}

# Tolerance for JSON-vs-scalar cross-checks (relative).
JSON_REL_TOL = 0.05


# ---------------------------------------------------------------------------
# Anomaly record
# ---------------------------------------------------------------------------

@dataclass
class Anomaly:
    check_id: str
    criterion_id: str | None
    table: str
    site_id: str
    site_name: str
    country: str | None
    column: str | None
    observed: Any
    expected_or_bound: Any
    kind: str             # value_out_of_range | parser_bug | unit_mismatch
                          # | dropped_field | implausible_in_context | null_unexpected
    action: str           # ACTION_AUTOFIX or ACTION_ESCALATE
    fix_value: Any = None # populated for auto-fix rows
    notes: str = ""
    json_evidence: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _audit_insert(
    session: Session,
    *,
    site_id: str,
    table_name: str,
    column: str,
    before: Any,
    after: Any,
    check_id: str,
    notes: str,
    run_id: str,
) -> None:
    """Insert one row in ``audit_log`` for a Phase 1 fix."""

    session.execute(
        text(
            """
            INSERT INTO audit_log
                (operation, table_name, site_id, before_value, after_value,
                 run_id, message)
            VALUES
                ('phase1_fix', :tbl, :sid, :before, :after, :rid, :msg)
            """
        ),
        {
            "tbl": table_name,
            "sid": site_id,
            "before": _to_jsonb({column: _jsonable(before)}),
            "after": _to_jsonb({column: _jsonable(after)}),
            "rid": run_id,
            "msg": f"[{check_id}] {notes}",
        },
    )


def _jsonable(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, (int, float, str, bool)):
        return v
    return str(v)


def _to_jsonb(d: dict) -> str:
    """Serialise a small dict for parameterised JSONB insertion."""
    import json
    return json.dumps(d)


# ---------------------------------------------------------------------------
# Scalar bounds check (data-driven)
# ---------------------------------------------------------------------------

# Mapping: column -> (table, criterion_id, classification_hint)
# classification_hint determines the default action when the value is
# outside bounds.
SCALAR_COLUMNS: list[tuple[str, str, str]] = [
    # natural hazards
    ("pga_475yr_g", "site_natural_hazards", "NH-01"),
    ("pga_2475yr_g", "site_natural_hazards", "NH-01"),
    ("nearest_fault_km", "site_natural_hazards", "NH-02"),
    ("fault_slip_rate_mm_yr", "site_natural_hazards", "NH-02"),
    ("groundwater_depth_m", "site_natural_hazards", "NH-03"),
    ("slope_angle_deg", "site_natural_hazards", "NH-04"),
    ("bearing_capacity_kpa", "site_natural_hazards", "NH-06"),
    ("depth_to_bedrock_m", "site_natural_hazards", "NH-06"),
    ("nearest_holocene_volcano_km", "site_natural_hazards", "NH-07"),
    ("distance_to_coast_km", "site_natural_hazards", "NH-08"),
    ("nearest_river_km", "site_natural_hazards", "NH-09"),
    ("max_wind_speed_ms", "site_natural_hazards", "NH-10"),
    ("extreme_temp_max_c", "site_natural_hazards", "NH-12"),
    ("extreme_temp_min_c", "site_natural_hazards", "NH-12"),
    ("extreme_precip_mm", "site_natural_hazards", "NH-11"),
    ("mean_annual_precip_mm", "site_natural_hazards", "NH-11"),
    ("wildfire_combustible_pct", "site_natural_hazards", "NH-13"),
    ("wildfire_wui_ha", "site_natural_hazards", "NH-13"),
    # human hazards
    ("nearest_airport_km", "site_human_hazards", "HI-01"),
    ("nearest_seveso_km", "site_human_hazards", "HI-02"),
    ("nearest_industrial_km", "site_human_hazards", "HI-02"),
    ("nearest_toxic_source_km", "site_human_hazards", "HI-03"),
    ("nearest_flammable_storage_km", "site_human_hazards", "HI-04"),
    ("nearest_pipeline_km", "site_human_hazards", "HI-04"),
    ("hazmat_route_distance_km", "site_human_hazards", "HI-05"),
    ("nearest_military_km", "site_human_hazards", "HI-06"),
    ("nearest_transmitter_km", "site_human_hazards", "HI-07"),
    ("nearest_nuclear_km", "site_human_hazards", "HI-08"),
    # radiological
    ("pop_density_5km", "site_radiological", "RI-04"),
    ("pop_density_16km", "site_radiological", "RI-04"),
    ("pop_density_25km", "site_radiological", "RI-04"),
    ("pop_density_80km", "site_radiological", "RI-04"),
    ("nearest_city_50k_km", "site_radiological", "RI-05"),
    ("pop_growth_rate_pct", "site_radiological", "RI-06"),
    ("avg_wind_speed_ms", "site_radiological", "RI-01"),
    ("mixing_height_m", "site_radiological", "RI-01"),
    ("nearest_river_flow_m3s", "site_radiological", "RI-02"),
    # infrastructure
    ("cooling_distance_km", "site_infrastructure_v2", "NS-01"),
    ("cooling_flow_m3s", "site_infrastructure_v2", "NS-01"),
    ("water_stress_score", "site_infrastructure_v2", "NS-01"),
    ("nearest_substation_km", "site_infrastructure_v2", "NS-02"),
    ("nearest_hv_line_km", "site_infrastructure_v2", "NS-02"),
    ("hv_line_voltage_kv", "site_infrastructure_v2", "NS-02"),
    ("grid_export_capacity_mw", "site_infrastructure_v2", "NS-02"),
    ("nearest_highway_km", "site_infrastructure_v2", "NS-03"),
    ("nearest_rail_km", "site_infrastructure_v2", "NS-03"),
    ("nearest_waterway_km", "site_infrastructure_v2", "NS-03"),
    ("dominant_class_pct", "site_infrastructure_v2", "NS-04"),
    ("favourable_land_pct", "site_infrastructure_v2", "NS-04"),
    ("moderate_land_pct", "site_infrastructure_v2", "NS-04"),
    ("unfavourable_land_pct", "site_infrastructure_v2", "NS-04"),
    ("favourable_area_ha", "site_infrastructure_v2", "NS-04"),
    ("buildable_area_ha", "site_infrastructure_v2", "NS-05"),
    ("largest_contiguous_ha", "site_infrastructure_v2", "NS-05"),
    ("n2k_nearest_distance_km", "site_infrastructure_v2", "NS-08"),
    ("wdpa_nearest_distance_km", "site_infrastructure_v2", "NS-08"),
    ("laydown_suitable_ha", "site_infrastructure_v2", "NS-13"),
    ("laydown_largest_patch_ha", "site_infrastructure_v2", "NS-13"),
    # emergency planning
    ("road_density_km_per_km2", "site_emergency_planning", "EP-02"),
    ("total_road_km", "site_emergency_planning", "EP-02"),
    ("hospital_count_epz", "site_emergency_planning", "EP-04"),
    ("prison_count_epz", "site_emergency_planning", "EP-04"),
    ("care_home_count_epz", "site_emergency_planning", "EP-04"),
    ("ep03_gee_relief_16km_m", "site_emergency_planning", "EP-03"),
]


def check_scalar_bounds(session: Session) -> list[Anomaly]:
    findings: list[Anomaly] = []
    site_lookup = {
        sid: (name, cc)
        for sid, name, cc in session.execute(
            text("SELECT site_id, name, country_code FROM sites")
        )
    }

    for col, table, crit in SCALAR_COLUMNS:
        bound = BOUNDS.get(col)
        if bound is None:
            continue
        rows = session.execute(
            text(f"SELECT site_id, {col} AS v FROM {table} WHERE {col} IS NOT NULL")
        ).all()
        for sid, v in rows:
            try:
                vf = float(v)
            except (TypeError, ValueError):
                continue
            below = vf < float(bound["min"])
            above = vf > float(bound["max"])
            if not (below or above):
                continue
            name, cc = site_lookup.get(sid, ("?", "??"))
            kind = "value_out_of_range"
            findings.append(
                Anomaly(
                    check_id=f"BOUND::{col}",
                    criterion_id=crit,
                    table=table,
                    site_id=str(sid),
                    site_name=name,
                    country=cc,
                    column=col,
                    observed=vf,
                    expected_or_bound=f"[{bound['min']}, {bound['max']}] {bound['unit']}",
                    kind=kind,
                    action=ACTION_ESCALATE,
                    notes=bound.get("comment", ""),
                )
            )
    return findings


# ---------------------------------------------------------------------------
# JSON / raw-response cross-checks
# ---------------------------------------------------------------------------

def check_n2k_distance_consistency(session: Session) -> list[Anomaly]:
    """Persisted ``n2k_nearest_distance_km`` must equal
    ``n2k_result_json->>'n2k_nearest_distance_km'`` (the ground truth
    from the connector's structured payload).
    """
    findings: list[Anomaly] = []
    rows = session.execute(text("""
        SELECT s.site_id, s.name, s.country_code,
               i.n2k_nearest_distance_km,
               (i.n2k_result_json->>'n2k_nearest_distance_km')::float AS json_dist,
               i.n2k_result_json->>'error' AS err,
               i.n2k_result_json->>'quality' AS qual
        FROM site_infrastructure_v2 i
        JOIN sites s USING (site_id)
        WHERE i.n2k_result_json IS NOT NULL
    """)).all()
    for sid, name, cc, scalar, jsonv, err, qual in rows:
        # Where the JSON is "insufficient" (no Natura 2000 coverage),
        # NULL is the correct scalar value.
        if qual == "insufficient" and scalar is None:
            continue
        if scalar is None and jsonv is None:
            continue
        if scalar is not None and jsonv is None:
            findings.append(Anomaly(
                check_id="JSON::n2k_distance_dropped",
                criterion_id="NS-08", table="site_infrastructure_v2",
                site_id=str(sid), site_name=name, country=cc,
                column="n2k_nearest_distance_km",
                observed=float(scalar), expected_or_bound="JSON has no value",
                kind="dropped_field", action=ACTION_ESCALATE,
                notes=f"json error={err!r}, quality={qual!r}",
            ))
            continue
        if scalar is None and jsonv is not None:
            findings.append(Anomaly(
                check_id="JSON::n2k_distance_dropped",
                criterion_id="NS-08", table="site_infrastructure_v2",
                site_id=str(sid), site_name=name, country=cc,
                column="n2k_nearest_distance_km",
                observed=None, expected_or_bound=float(jsonv),
                kind="parser_bug", action=ACTION_AUTOFIX,
                fix_value=float(jsonv),
                notes="scalar NULL but JSON has value — backfill from JSON",
            ))
            continue
        s = float(scalar); j = float(jsonv)
        denom = max(abs(j), 1e-9)
        if abs(s - j) / denom > JSON_REL_TOL:
            findings.append(Anomaly(
                check_id="JSON::n2k_distance_mismatch",
                criterion_id="NS-08", table="site_infrastructure_v2",
                site_id=str(sid), site_name=name, country=cc,
                column="n2k_nearest_distance_km",
                observed=s, expected_or_bound=j,
                kind="parser_bug", action=ACTION_AUTOFIX,
                fix_value=j,
                notes="scalar drifted from JSON ground truth",
            ))
    return findings


def check_wdpa_distance_consistency(session: Session) -> list[Anomaly]:
    findings: list[Anomaly] = []
    rows = session.execute(text("""
        SELECT s.site_id, s.name, s.country_code,
               i.wdpa_nearest_distance_km,
               (i.wdpa_result_json->>'wdpa_nearest_distance_km')::float AS json_dist,
               i.wdpa_result_json->>'error' AS err,
               i.wdpa_result_json->>'quality' AS qual
        FROM site_infrastructure_v2 i
        JOIN sites s USING (site_id)
        WHERE i.wdpa_result_json IS NOT NULL
    """)).all()
    for sid, name, cc, scalar, jsonv, err, qual in rows:
        if qual == "insufficient" and scalar is None:
            continue
        if scalar is None and jsonv is None:
            continue
        if scalar is None and jsonv is not None:
            findings.append(Anomaly(
                check_id="JSON::wdpa_distance_dropped",
                criterion_id="NS-08", table="site_infrastructure_v2",
                site_id=str(sid), site_name=name, country=cc,
                column="wdpa_nearest_distance_km",
                observed=None, expected_or_bound=float(jsonv),
                kind="parser_bug", action=ACTION_AUTOFIX,
                fix_value=float(jsonv),
                notes="scalar NULL but JSON has value",
            ))
            continue
        if scalar is not None and jsonv is None:
            findings.append(Anomaly(
                check_id="JSON::wdpa_distance_dropped",
                criterion_id="NS-08", table="site_infrastructure_v2",
                site_id=str(sid), site_name=name, country=cc,
                column="wdpa_nearest_distance_km",
                observed=float(scalar), expected_or_bound="JSON missing key",
                kind="dropped_field", action=ACTION_ESCALATE,
                notes=f"json error={err!r}, quality={qual!r}",
            ))
            continue
        s = float(scalar); j = float(jsonv)
        denom = max(abs(j), 1e-9)
        if abs(s - j) / denom > JSON_REL_TOL:
            findings.append(Anomaly(
                check_id="JSON::wdpa_distance_mismatch",
                criterion_id="NS-08", table="site_infrastructure_v2",
                site_id=str(sid), site_name=name, country=cc,
                column="wdpa_nearest_distance_km",
                observed=s, expected_or_bound=j,
                kind="parser_bug", action=ACTION_AUTOFIX,
                fix_value=j,
                notes="scalar drifted from JSON ground truth",
            ))
    return findings


def check_seismic_pga_consistency(session: Session) -> list[Anomaly]:
    """spectral_accel_json carries the EFEHR ground-truth PGA values
    (``pga_475yr`` / ``pga_2475yr``).  The persisted scalars
    (``pga_475yr_g`` / ``pga_2475yr_g``) must agree to within JSON_REL_TOL.
    """
    findings: list[Anomaly] = []
    rows = session.execute(text("""
        SELECT s.site_id, s.name, s.country_code,
               nh.pga_475yr_g, nh.pga_2475yr_g,
               (nh.spectral_accel_json->>'pga_475yr')::float  AS json_475,
               (nh.spectral_accel_json->>'pga_2475yr')::float AS json_2475,
               nh.spectral_accel_json->>'quality' AS qual,
               nh.spectral_accel_json->>'error'   AS err
        FROM site_natural_hazards nh
        JOIN sites s USING (site_id)
        WHERE nh.spectral_accel_json IS NOT NULL
    """)).all()
    for sid, name, cc, p475, p2475, j475, j2475, qual, err in rows:
        for col, scalar, jsonv in (
            ("pga_475yr_g",  p475,  j475),
            ("pga_2475yr_g", p2475, j2475),
        ):
            if scalar is None and jsonv is None:
                continue
            if scalar is None and jsonv is not None:
                findings.append(Anomaly(
                    check_id=f"JSON::seismic_dropped::{col}",
                    criterion_id="NH-01", table="site_natural_hazards",
                    site_id=str(sid), site_name=name, country=cc,
                    column=col, observed=None, expected_or_bound=float(jsonv),
                    kind="parser_bug", action=ACTION_AUTOFIX,
                    fix_value=float(jsonv),
                    notes="scalar NULL but spectral_accel_json has value",
                ))
                continue
            if scalar is not None and jsonv is None:
                findings.append(Anomaly(
                    check_id=f"JSON::seismic_dropped::{col}",
                    criterion_id="NH-01", table="site_natural_hazards",
                    site_id=str(sid), site_name=name, country=cc,
                    column=col, observed=float(scalar),
                    expected_or_bound="JSON missing key",
                    kind="dropped_field", action=ACTION_ESCALATE,
                    notes=f"json quality={qual!r} error={err!r}",
                ))
                continue
            s = float(scalar); j = float(jsonv)
            denom = max(abs(j), 1e-9)
            if abs(s - j) / denom > JSON_REL_TOL:
                findings.append(Anomaly(
                    check_id=f"JSON::seismic_mismatch::{col}",
                    criterion_id="NH-01", table="site_natural_hazards",
                    site_id=str(sid), site_name=name, country=cc,
                    column=col, observed=s, expected_or_bound=j,
                    kind="parser_bug", action=ACTION_AUTOFIX,
                    fix_value=j,
                    notes="scalar drifted from JSON ground truth",
                ))
    return findings


def check_gem_zero_pga_sentinel(session: Session) -> list[Anomaly]:
    """Flag ``pga_475yr_g = 0`` from GEM Global when no hazard curve was
    returned — the connector persisted a **missing-data sentinel** as
    numeric zero.  True PGA ≈ 0 g is not credible for European sites;
    scoring must treat these as NULL / insufficient (see
    ``report/business_logic.md`` L-13).

    Pattern: ``nh01_source`` contains ``gem_global``, scalar 475-yr is 0,
    ``spectral_accel_json->'hazard_curve'`` is null (no curve extracted).
    """
    findings: list[Anomaly] = []
    rows = session.execute(text("""
        SELECT s.site_id, s.name, s.country_code,
               nh.pga_475yr_g, nh.nh01_source,
               nh.spectral_accel_json->>'pga_2475yr' AS j2475
        FROM site_natural_hazards nh
        JOIN sites s USING (site_id)
        WHERE nh.nh01_source LIKE '%gem_global%'
          AND nh.pga_475yr_g = 0
          AND (nh.spectral_accel_json IS NULL
               OR (nh.spectral_accel_json->'hazard_curve') IS NULL)
    """)).all()
    for sid, name, cc, p475, src, j2475 in rows:
        findings.append(Anomaly(
            check_id="NH01::gem_zero_pga_sentinel",
            criterion_id="NH-01", table="site_natural_hazards",
            site_id=str(sid), site_name=name, country=cc,
            column="pga_475yr_g",
            observed=float(p475) if p475 is not None else None,
            expected_or_bound="NULL (missing hazard)",
            kind="sentinel_zero", action=ACTION_ESCALATE,
            notes=(
                f"GEM fallback with no hazard_curve in JSON; "
                f"pga_2475yr in JSON={j2475!r}; source={src!r}. "
                "Fix connector to emit NULL instead of 0; then backfill "
                "or mark nh01_quality=low."
            ),
        ))
    return findings


def check_road_density_consistency(session: Session) -> list[Anomaly]:
    """Cross-check ``road_density_km_per_km2`` / ``total_road_km`` against
    the JSON in ``site_raw_responses`` for ``osm_road_density``.

    Only flags **catastrophic divergence**:
      - scalar is NULL while JSON has a value (parser_bug, autofix);
      - scalar is 0 while JSON is > 0 (silent zero, autofix);
      - scalar is > 0 while JSON is NULL/missing (dropped_field, escalate).

    A ±5 % drift between scalar and JSON is *not* flagged because the
    connector evolved through several buffer radii (EP-02 vs NS-03 vs
    16 km EPZ) and the persisted scalar can legitimately come from a
    different radius than the most recent ``site_raw_responses`` row.
    """
    findings: list[Anomaly] = []
    rows = session.execute(text("""
        SELECT s.site_id, s.name, s.country_code,
               ep.road_density_km_per_km2 AS scalar_density,
               ep.total_road_km           AS scalar_total,
               (rr.response_body #>> '{data,density_km_per_km2}')::float AS json_density,
               (rr.response_body #>> '{data,total_road_km}')::float      AS json_total
        FROM site_emergency_planning ep
        JOIN sites s USING (site_id)
        JOIN site_raw_responses rr ON rr.site_id = s.site_id
                                  AND rr.connector_slug = 'osm_road_density'
    """)).all()
    seen: set[str] = set()
    for sid, name, cc, sdens, stot, jdens, jtot in rows:
        for col, scalar, jsonv in (
            ("road_density_km_per_km2", sdens, jdens),
            ("total_road_km",            stot,  jtot),
        ):
            key = f"{sid}::{col}"
            if key in seen:
                continue
            if scalar is None and jsonv is not None and float(jsonv) > 0:
                seen.add(key)
                findings.append(Anomaly(
                    check_id=f"JSON::road_density_null_scalar::{col}",
                    criterion_id="EP-02", table="site_emergency_planning",
                    site_id=str(sid), site_name=name, country=cc,
                    column=col, observed=None, expected_or_bound=float(jsonv),
                    kind="parser_bug", action=ACTION_AUTOFIX,
                    fix_value=float(jsonv),
                    notes="scalar NULL but raw response carries a positive value",
                ))
                continue
            if (scalar is not None and float(scalar) == 0
                    and jsonv is not None and float(jsonv) > 0):
                seen.add(key)
                findings.append(Anomaly(
                    check_id=f"JSON::road_density_silent_zero::{col}",
                    criterion_id="EP-02", table="site_emergency_planning",
                    site_id=str(sid), site_name=name, country=cc,
                    column=col, observed=0.0, expected_or_bound=float(jsonv),
                    kind="parser_bug", action=ACTION_AUTOFIX,
                    fix_value=float(jsonv),
                    notes="scalar=0 but raw response carries a positive value",
                ))
                continue
            if (scalar is not None and float(scalar) > 0
                    and jsonv is None):
                seen.add(key)
                findings.append(Anomaly(
                    check_id=f"JSON::road_density_dropped::{col}",
                    criterion_id="EP-02", table="site_emergency_planning",
                    site_id=str(sid), site_name=name, country=cc,
                    column=col, observed=float(scalar),
                    expected_or_bound="JSON missing key",
                    kind="dropped_field", action=ACTION_ESCALATE,
                    notes="scalar present but raw response lacks the value",
                ))
                continue
    return findings


# ---------------------------------------------------------------------------
# Implausible-given-context checks (compound)
# ---------------------------------------------------------------------------

def check_cooling_flow_vs_capacity(session: Session) -> list[Anomaly]:
    """A >1000 MW thermal plant cannot be cooled by a sub-1 m³/s stream."""
    findings: list[Anomaly] = []
    rows = session.execute(text("""
        SELECT s.site_id, s.name, s.country_code,
               s.installed_capacity_mw, i.cooling_flow_m3s,
               i.cooling_source_type, i.cooling_source_name,
               i.cooling_distance_km, i.ns01_quality
        FROM site_infrastructure_v2 i
        JOIN sites s USING (site_id)
        WHERE s.installed_capacity_mw > 1000
          AND i.cooling_flow_m3s IS NOT NULL
          AND i.cooling_flow_m3s < 1.0
    """)).all()
    for sid, name, cc, cap, flow, ctype, cname, cdist, qual in rows:
        findings.append(Anomaly(
            check_id="CONTEXT::cooling_flow_too_low_for_capacity",
            criterion_id="NS-01", table="site_infrastructure_v2",
            site_id=str(sid), site_name=name, country=cc,
            column="cooling_flow_m3s",
            observed=float(flow),
            expected_or_bound=f">= 5 m3/s for {cap} MW (rule of thumb)",
            kind="implausible_in_context", action=ACTION_ESCALATE,
            notes=(
                f"cap={cap} MW, source={ctype} '{cname}' "
                f"@ {cdist} km, ns01_quality={qual} "
                "— HydroRIVERS likely snapped to a tributary; needs GloFAS "
                "main-stem re-pull."
            ),
        ))
    return findings


def check_steep_slope(session: Session) -> list[Anomaly]:
    """Slope > 25° is implausibly steep for a candidate SMR site."""
    findings: list[Anomaly] = []
    rows = session.execute(text("""
        SELECT s.site_id, s.name, s.country_code,
               nh.slope_angle_deg,
               nh.nh04_dem_cog_slope_max_deg,
               nh.nh04_gee_slope_mean_deg,
               nh.nh04_quality, nh.nh04_slope_fusion_method
        FROM site_natural_hazards nh
        JOIN sites s USING (site_id)
        WHERE nh.slope_angle_deg > 25.0
    """)).all()
    for sid, name, cc, slope, dem_max, gee_mean, qual, method in rows:
        findings.append(Anomaly(
            check_id="CONTEXT::slope_too_steep",
            criterion_id="NH-04", table="site_natural_hazards",
            site_id=str(sid), site_name=name, country=cc,
            column="slope_angle_deg",
            observed=float(slope),
            expected_or_bound="<= 25 deg (IAEA SSG-9 severe band starts here)",
            kind="implausible_in_context", action=ACTION_ESCALATE,
            notes=(
                f"dem_cog_max={dem_max} gee_mean={gee_mean} "
                f"quality={qual} fusion={method!r}; primary slope is the "
                "max-in-30 m buffer, not the mean — likely overstated. "
                "Re-pull GEE mean slope at finer buffer."
            ),
        ))
    return findings


def check_grid_export_vs_capacity(session: Session) -> list[Anomaly]:
    """``grid_export_capacity_mw`` exactly equal to
    ``installed_capacity_mw`` is the connector's "no zone-level NTC found"
    fallback (FIX-02 / F-01).  Only flag the cases where
    ``ns02_quality='insufficient'`` — those rows used the fallback because
    the connector could not get an authoritative NTC.  When quality is
    medium/high the equality is real signal (single-zone monopolist plant).
    """
    findings: list[Anomaly] = []
    rows = session.execute(text("""
        SELECT s.site_id, s.name, s.country_code,
               s.installed_capacity_mw, i.grid_export_capacity_mw,
               i.ns02_quality
        FROM site_infrastructure_v2 i
        JOIN sites s USING (site_id)
        WHERE s.installed_capacity_mw IS NOT NULL
          AND i.grid_export_capacity_mw IS NOT NULL
          AND ABS(s.installed_capacity_mw - i.grid_export_capacity_mw) < 0.01
          AND s.installed_capacity_mw > 1000
          AND i.ns02_quality = 'insufficient'
    """)).all()
    for sid, name, cc, cap, ge, qual in rows:
        findings.append(Anomaly(
            check_id="CONTEXT::grid_export_equals_capacity_fallback",
            criterion_id="NS-02", table="site_infrastructure_v2",
            site_id=str(sid), site_name=name, country=cc,
            column="grid_export_capacity_mw",
            observed=float(ge),
            expected_or_bound=f"!= installed_capacity_mw ({cap})",
            kind="implausible_in_context", action=ACTION_ESCALATE,
            notes=(
                f"ns02_quality={qual}; perfect equality at >1000 MW "
                "is the connector's no-NTC fallback. Confirm vs ENTSO-E "
                "zone NTC value before treating this as the SMR's grid "
                "export ceiling."
            ),
        ))
    return findings


def check_favourable_area_implausibly_small(session: Session) -> list[Anomaly]:
    """``favourable_area_ha`` < 1 % of ``buildable_area_ha`` while
    buildable > 5 ha suggests a parser bug in CORINE area aggregation."""
    findings: list[Anomaly] = []
    rows = session.execute(text("""
        SELECT s.site_id, s.name, s.country_code,
               i.favourable_area_ha, i.buildable_area_ha,
               i.favourable_land_pct, i.ns04_quality
        FROM site_infrastructure_v2 i
        JOIN sites s USING (site_id)
        WHERE i.favourable_area_ha IS NOT NULL
          AND i.buildable_area_ha IS NOT NULL
          AND i.buildable_area_ha > 5.0
          AND i.favourable_area_ha < 0.01 * i.buildable_area_ha
    """)).all()
    for sid, name, cc, fav, buil, pct, qual in rows:
        findings.append(Anomaly(
            check_id="CONTEXT::favourable_area_implausibly_small",
            criterion_id="NS-04", table="site_infrastructure_v2",
            site_id=str(sid), site_name=name, country=cc,
            column="favourable_area_ha",
            observed=float(fav),
            expected_or_bound=f">= 1 % of buildable ({buil} ha)",
            kind="implausible_in_context", action=ACTION_ESCALATE,
            notes=(
                f"buildable={buil}, favourable_pct={pct}, ns04_quality={qual} "
                "— favourable_area should never be 100× smaller than "
                "buildable when CORINE assigns any non-zero %."
            ),
        ))
    return findings


# ---------------------------------------------------------------------------
# NULL-derivable checks (auto-fix opportunities)
# ---------------------------------------------------------------------------

def check_patch_count_derivable(session: Session) -> list[Anomaly]:
    """``patch_count`` NULL or 0 while ``largest_contiguous_ha`` > 0
    means there is at least one patch — derive ``patch_count = 1``.
    """
    findings: list[Anomaly] = []
    rows = session.execute(text("""
        SELECT s.site_id, s.name, s.country_code,
               i.patch_count, i.largest_contiguous_ha,
               i.buildable_area_ha
        FROM site_infrastructure_v2 i
        JOIN sites s USING (site_id)
        WHERE (i.patch_count IS NULL OR i.patch_count = 0)
          AND COALESCE(i.largest_contiguous_ha, 0) > 0
    """)).all()
    for sid, name, cc, pc, lc, ba in rows:
        findings.append(Anomaly(
            check_id="NULL::patch_count_derivable",
            criterion_id="NS-05", table="site_infrastructure_v2",
            site_id=str(sid), site_name=name, country=cc,
            column="patch_count",
            observed=pc,
            expected_or_bound=">= 1 (largest_contiguous_ha implies a patch exists)",
            kind="null_unexpected", action=ACTION_AUTOFIX,
            fix_value=1,
            notes=f"largest_contiguous_ha={lc}, buildable_area_ha={ba}",
        ))
    return findings


def check_wildfire_all_null(session: Session) -> list[Anomaly]:
    """NH-13 ``wildfire_combustible_pct`` NULL across the board — the
    connector either never ran or always errored.  Reported as one
    aggregate finding (with up to 10 sample sites) so it does not drown
    out everything else.
    """
    findings: list[Anomaly] = []
    rows = session.execute(text("""
        SELECT s.site_id, s.name, s.country_code
        FROM site_natural_hazards nh
        JOIN sites s USING (site_id)
        WHERE nh.wildfire_combustible_pct IS NULL
        ORDER BY s.country_code, s.name
    """)).all()
    if not rows:
        return findings
    sample = ", ".join(f"{n} ({c})" for _, n, c in rows[:8])
    findings.append(Anomaly(
        check_id="NULL::wildfire_uncovered_BULK",
        criterion_id="NH-13", table="site_natural_hazards",
        site_id="(all)", site_name=f"{len(rows)} sites", country=None,
        column="wildfire_combustible_pct",
        observed=f"NULL on {len(rows)} of 363 rows",
        expected_or_bound="0..100 % from CORINE class 311-324",
        kind="null_unexpected", action=ACTION_ESCALATE,
        notes=(
            "Connector-wide gap — not a per-site anomaly. "
            "CorineConnector never populated wildfire_combustible_pct. "
            f"First 8 sites: {sample}. "
            "Two paths: (a) re-run CORINE batch with the wildfire-class "
            "aggregator enabled; (b) accept as `insufficient` quality in "
            "business_logic ladder and use NH-12 + NH-10 as proxy for "
            "wildfire risk."
        ),
    ))
    return findings


# ---------------------------------------------------------------------------
# Registry & runner
# ---------------------------------------------------------------------------

CHECKS: list[tuple[str, Any]] = [
    ("scalar_bounds",              check_scalar_bounds),
    ("seismic_pga_vs_json",        check_seismic_pga_consistency),
    ("gem_zero_pga_sentinel",      check_gem_zero_pga_sentinel),
    ("n2k_distance_vs_json",       check_n2k_distance_consistency),
    ("wdpa_distance_vs_json",      check_wdpa_distance_consistency),
    ("road_density_vs_raw",        check_road_density_consistency),
    ("cooling_flow_vs_capacity",   check_cooling_flow_vs_capacity),
    ("steep_slope_context",        check_steep_slope),
    ("grid_export_fallback",       check_grid_export_vs_capacity),
    ("favourable_area_implausible",check_favourable_area_implausibly_small),
    ("patch_count_derivable",      check_patch_count_derivable),
    ("wildfire_all_null",          check_wildfire_all_null),
]


def apply_fix(session: Session, anom: Anomaly, run_id: str) -> bool:
    """Apply a single auto-fix, write an ``audit_log`` row, return success."""
    if anom.action != ACTION_AUTOFIX or anom.column is None:
        return False
    pk_col = "site_id"
    session.execute(
        text(
            f"UPDATE {anom.table} SET {anom.column} = :v "
            f"WHERE {pk_col} = :sid"
        ),
        {"v": anom.fix_value, "sid": anom.site_id},
    )
    _audit_insert(
        session,
        site_id=anom.site_id,
        table_name=anom.table,
        column=anom.column,
        before=anom.observed,
        after=anom.fix_value,
        check_id=anom.check_id,
        notes=anom.notes,
        run_id=run_id,
    )
    return True


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def fetch_prior_phase1_fixes(session: Session) -> list[tuple[str, str, str, str]]:
    """Return (table_name, message, before, after) for every audit_log
    row tagged ``phase1_fix`` (any prior run of this scanner)."""
    rows = session.execute(text("""
        SELECT table_name, message, before_value::text, after_value::text
        FROM audit_log
        WHERE operation = 'phase1_fix'
        ORDER BY timestamp
    """)).all()
    return [(r[0], r[1], r[2], r[3]) for r in rows]


def write_report(
    findings: list[Anomaly],
    *,
    apply_mode: bool,
    fixed_count: int,
    run_id: str,
    dest: Path,
    prior_fixes: list[tuple[str, str, str, str]] | None = None,
) -> None:
    prior_fixes = prior_fixes or []
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    by_action = defaultdict(list)
    for a in findings:
        by_action[a.action].append(a)
    autofix = by_action[ACTION_AUTOFIX]
    escalate = by_action[ACTION_ESCALATE]

    by_check = defaultdict(list)
    for a in findings:
        by_check[a.check_id].append(a)

    by_criterion = defaultdict(int)
    for a in findings:
        by_criterion[a.criterion_id or "—"] += 1

    lines: list[str] = []
    lines.append("# Phase 1 — API DB anomaly sweep")
    lines.append("")
    lines.append(f"_Generated {timestamp} by `scripts/scan_api_db_anomalies.py`._")
    lines.append("")
    lines.append("**DB scanned:** `atoms_vs_ashes` (live, post-snapshot)  ")
    lines.append("**Snapshot:** `backups/atoms_vs_ashes_raw_20260421.dump` (pg_dump custom)  ")
    lines.append("**Snapshot DB:** `atoms_vs_ashes_raw_20260421` (read-only restore)  ")
    lines.append(f"**Mode:** `{'apply' if apply_mode else 'dry-run'}`  ")
    lines.append(f"**Run id:** `{run_id}`  ")
    lines.append(f"**Bounds source:** engineering common sense (this script's `BOUNDS` dict). ")
    lines.append("Phase 3 `report/business_logic.md` will adopt and formalise them.")
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append(
        "Each row in every domain table (sites, site_natural_hazards, "
        "site_human_hazards, site_radiological, site_emergency_planning, "
        "site_infrastructure_v2) is checked against three families of rules:"
    )
    lines.append("")
    lines.append("1. **Scalar bounds** — common-sense per-column min/max from `BOUNDS` dict.")
    lines.append("2. **JSON / raw-response triangulation** — the persisted scalar must agree, ")
    lines.append("   within 5 % relative tolerance, with the source-of-truth value in the ")
    lines.append("   originating JSONB column (`spectral_accel_json`, `n2k_result_json`, ")
    lines.append("   `wdpa_result_json`) or in the relevant `site_raw_responses.response_body`.")
    lines.append("3. **Implausible-given-context** — compound rules that combine multiple ")
    lines.append("   columns (e.g. cooling flow vs installed capacity).")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total findings: **{len(findings)}**")
    lines.append(f"- Auto-fix candidates: **{len(autofix)}**")
    lines.append(f"- Escalations (human review needed): **{len(escalate)}**")
    if apply_mode:
        lines.append(f"- Fixes actually applied this run: **{fixed_count}**")
    else:
        lines.append(f"- Fixes applied this run: **0** (dry-run)")
    if prior_fixes:
        lines.append(
            f"- Total prior `phase1_fix` rows in `audit_log` (all runs): **{len(prior_fixes)}**"
        )
    lines.append("")
    lines.append("### Findings per check")
    lines.append("")
    lines.append("| Check | Action default | Findings |")
    lines.append("|---|---|---:|")
    for check_id in sorted(by_check):
        items = by_check[check_id]
        actions = sorted({a.action for a in items})
        lines.append(f"| `{check_id}` | {','.join(actions)} | {len(items)} |")
    lines.append("")
    lines.append("### Findings per criterion")
    lines.append("")
    lines.append("| Criterion | Findings |")
    lines.append("|---|---:|")
    for crit in sorted(by_criterion):
        lines.append(f"| {crit} | {by_criterion[crit]} |")
    lines.append("")

    if autofix:
        lines.append("## Auto-fix candidates")
        lines.append("")
        if apply_mode:
            lines.append(f"All rows below were applied to `atoms_vs_ashes` IN PLACE this run "
                         f"(audit_log run_id = `{run_id}`).  Re-running the scanner should "
                         "report zero rows for these checks.")
        else:
            lines.append("Re-run with `--apply` to write these fixes IN PLACE to the DB. "
                         "Each fix produces one `audit_log` row tagged `operation='phase1_fix'`.")
        lines.append("")
        lines.append("| Check | Site | Country | Column | Before | After | Notes |")
        lines.append("|---|---|---|---|---|---|---|")
        for a in autofix[:200]:
            lines.append(
                f"| `{a.check_id}` | {a.site_name} | {a.country or '?'} | `{a.column}` "
                f"| `{_fmt_val(a.observed)}` | `{_fmt_val(a.fix_value)}` | {a.notes} |"
            )
        if len(autofix) > 200:
            lines.append(f"| … {len(autofix) - 200} more rows truncated ||||||  |")
        lines.append("")

    if escalate:
        lines.append("## Escalations (human review required)")
        lines.append("")
        lines.append("These findings cannot be deterministically fixed from data on hand. ")
        lines.append("They are recorded here so Phase 3 (business logic) and Phase 5 (LLM ")
        lines.append("enrichment) can either patch them with cross-source evidence or accept ")
        lines.append("`insufficient` quality with a documented fallback.")
        lines.append("")

        # Group escalations by criterion
        by_crit_esc = defaultdict(list)
        for a in escalate:
            by_crit_esc[a.criterion_id or "—"].append(a)

        for crit in sorted(by_crit_esc):
            items = by_crit_esc[crit]
            lines.append(f"### {crit} — {len(items)} finding(s)")
            lines.append("")
            lines.append("| Check | Site | Country | Column | Observed | Bound / expected | Notes |")
            lines.append("|---|---|---|---|---|---|---|")
            for a in items[:60]:
                lines.append(
                    f"| `{a.check_id}` | {a.site_name} | {a.country or '?'} | "
                    f"`{a.column or '—'}` | `{_fmt_val(a.observed)}` | "
                    f"`{_fmt_val(a.expected_or_bound)}` | {a.notes} |"
                )
            if len(items) > 60:
                lines.append(f"| … {len(items) - 60} more rows truncated ||||||  |")
            lines.append("")

    if prior_fixes:
        lines.append("## Audit-log: previously applied Phase 1 fixes")
        lines.append("")
        lines.append("Every row below is one ``audit_log`` entry created by a previous ")
        lines.append("``--apply`` run of this scanner.  They are reproduced here so the ")
        lines.append("report is a complete record even when the current dry-run finds ")
        lines.append("zero new auto-fix candidates.")
        lines.append("")
        lines.append("| Table | Message | Before | After |")
        lines.append("|---|---|---|---|")
        for tbl, msg, bef, aft in prior_fixes[:200]:
            bef_short = (bef or "")[:80]
            aft_short = (aft or "")[:80]
            msg_short = (msg or "").replace("|", "\\|")
            lines.append(f"| `{tbl}` | {msg_short} | `{bef_short}` | `{aft_short}` |")
        if len(prior_fixes) > 200:
            lines.append(f"| … {len(prior_fixes) - 200} more truncated |||")
        lines.append("")

    lines.append("## Next steps")
    lines.append("")
    lines.append("1. **Re-run with `--apply`** to commit the auto-fixes (or run again in ")
    lines.append("   dry-run with the same DB to verify zero new findings).")
    lines.append("2. **Phase 2** (build `atoms_vs_ashes_merged`) consumes the cleaned API DB.")
    lines.append("3. **Phase 3** (`report/business_logic.md`) formalises every bound used here ")
    lines.append("   and adds a fallback ladder for each escalation.")
    lines.append("4. **Phase 5** (LLM enrichment) uses LLM narratives to patch escalations ")
    lines.append("   where `data_sources` and `confidence` justify it.")
    lines.append("")

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(lines), encoding="utf-8")


def _fmt_val(v: Any) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write auto-fixes IN PLACE to atoms_vs_ashes (with audit_log).",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=REPORT_PATH,
        help=f"Destination report file (default: {REPORT_PATH}).",
    )
    args = parser.parse_args()

    settings = Settings()
    engine = create_engine(settings.database.url)
    SessionLocal = sessionmaker(bind=engine)

    run_id = "phase1_sweep_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    findings: list[Anomaly] = []
    fixed = 0
    with SessionLocal() as session:
        for label, fn in CHECKS:
            print(f"[scan] {label} …", flush=True)
            results = fn(session)
            print(f"  → {len(results)} finding(s)")
            findings.extend(results)

        if args.apply:
            print(f"[apply] writing fixes (run_id={run_id}) …", flush=True)
            for a in findings:
                if a.action == ACTION_AUTOFIX:
                    if apply_fix(session, a, run_id):
                        fixed += 1
            session.commit()
            print(f"[apply] committed {fixed} fix(es).")
        else:
            session.rollback()

        prior_fixes = fetch_prior_phase1_fixes(session)

    write_report(
        findings,
        apply_mode=args.apply,
        fixed_count=fixed,
        run_id=run_id,
        dest=args.report_path,
        prior_fixes=prior_fixes,
    )
    print(f"[report] wrote {args.report_path}")
    print(f"[done] findings={len(findings)} autofix={sum(1 for a in findings if a.action == ACTION_AUTOFIX)} "
          f"escalate={sum(1 for a in findings if a.action == ACTION_ESCALATE)} applied={fixed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
