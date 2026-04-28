# man_hours: 1.0
"""Regression tests for suitable-site audit diagnostics and fixes."""

from __future__ import annotations

from atoms_vs_ashes.db.models import Site, SiteNaturalHazards
from atoms_vs_ashes.gui._results_data_detail import _status_label
from atoms_vs_ashes.scoring.merge_context_derivations import (
    apply_derived_context_values,
)
from atoms_vs_ashes.scoring.merge_resolver import (
    resolve_scalar,
)
from atoms_vs_ashes.scoring_audit import collect_audit_rules
from atoms_vs_ashes.scoring_audit.status import build_audit_status_rows


def _site() -> Site:
    site = Site(
        name="Example",
        country_code="RO",
        country_name="Romania",
        latitude=45.0,
        longitude=25.0,
    )
    site.natural_hazards = SiteNaturalHazards(
        nearest_holocene_volcano_km=12.5,
        distance_to_coast_km=3.0,
        nearest_river_km=1.2,
    )
    return site


def test_merge_resolver_supports_rubric_era_aliases() -> None:
    site = _site()

    assert resolve_scalar(site, "site_natural_hazards", "nearest_volcano_km") == 12.5
    assert resolve_scalar(site, "site_natural_hazards", "coast_distance_km") == 3.0
    assert resolve_scalar(site, "site_natural_hazards", "river_distance_km") == 1.2


def test_derived_context_values_unlock_multi_clause_expressions() -> None:
    values = {
        "flight_path_distance_km": 3.5,
        "hospital_count_epz": 2,
        "prison_count_epz": 1,
        "care_home_count_epz": 4,
        "pg_class_f_fraction": 7.5,
        "pg_class_e_fraction": 2.5,
        "n2k_nearest_distance_km": 0.0,
    }

    apply_derived_context_values(values)

    assert values["under_flight_path"] is False
    assert values["nearest_military_airfield_km"] == 999.0
    assert values["special_pop_count"] == 7
    assert values["pg_fe_fraction"] == 10.0
    assert values["site_within_strict_protected"] is True


def test_audit_catalogue_includes_all_live_ea_rules() -> None:
    rules = collect_audit_rules()
    codes = {(r.criterion_id, r.code, r.action) for r in rules}

    assert ("EP-01", "E8", "exclude") in codes
    assert ("NH-05", "E5", "exclude") not in codes
    assert ("NH-05", "E6", "exclude") not in codes
    assert ("RI-04", "A12", "avoidance_penalty") in codes
    assert ("NS-05", "A15", "avoidance_penalty") in codes
    assert any("dry_cooling_viable" in r.missing_context_names for r in rules)


def test_audit_status_expands_exclusionary_floors_and_avoidance_roles() -> None:
    rows = build_audit_status_rows(collect_audit_rules(), [])
    by_code = {r.code: r for r in rows}

    assert "E1:floor" in by_code
    assert by_code["A15"].decision == "valid_as_risk_flag"
    assert by_code["A15"].suitability_role.startswith("avoidance caution")


def test_avoidance_status_is_not_labeled_as_floor_failure() -> None:
    class Row:
        passed_exclusionary = True
        passed_avoidance = False

    assert _status_label(Row()) == "avoidance-flag"
