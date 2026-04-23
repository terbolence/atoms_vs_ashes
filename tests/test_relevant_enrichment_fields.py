# man_hours: 1.0
"""Regression tests for RELEVANT_ENRICHMENT_FIELDS wiring.

Guards against the "phantom column" bug class where the mapping referenced
non-existent ORM columns (see LL-006 / the April 2026 wiring audit).

Every (criterion, domain, field) entry MUST resolve to a real column on the
target ORM model. If any entry does not, the entire mapping is suspect
because the silent-drop behaviour hides it at runtime.
"""

from __future__ import annotations

from atoms_vs_ashes.db import models as orm
from atoms_vs_ashes.llm.context import (
    RELEVANT_ENRICHMENT_FIELDS,
    _DOMAIN_TABLE_MAP,
    _filter_enrichment,
    _row_to_dict,
    compute_enrichment_coverage,
    validate_relevant_enrichment_fields,
)


def test_no_phantom_columns():
    """Every field in RELEVANT_ENRICHMENT_FIELDS must exist on the ORM model."""
    problems = validate_relevant_enrichment_fields()
    assert problems == [], (
        "RELEVANT_ENRICHMENT_FIELDS has phantom columns not on the ORM. "
        "Either add the column to the model (and migration) or drop it from "
        f"the mapping. Offending entries: {problems}"
    )


def test_all_domains_resolve_to_known_orm_models():
    """Every domain key must map to a real ORM class."""
    expected_classes = {
        "natural_hazards": orm.SiteNaturalHazards,
        "human_hazards": orm.SiteHumanHazards,
        "radiological": orm.SiteRadiological,
        "emergency_planning": orm.SiteEmergencyPlanning,
        "infrastructure": orm.SiteInfrastructureV2,
    }
    assert _DOMAIN_TABLE_MAP == expected_classes


def test_validator_detects_injected_phantom():
    """Sanity check the validator itself — injected phantom must be caught."""
    rigged = {
        "E_FAKE": {"natural_hazards": {"this_column_does_not_exist"}},
    }
    problems = validate_relevant_enrichment_fields(rigged)
    assert problems == [("E_FAKE", "natural_hazards", "this_column_does_not_exist")]


def test_validator_accepts_real_columns():
    """Real columns must not be flagged."""
    clean = {
        "E1": {"natural_hazards": {"pga_475yr_g", "nearest_fault_km", "nh02_quality"}},
        "A5": {"human_hazards": {"nearest_military_km", "hi06_quality"}},
    }
    assert validate_relevant_enrichment_fields(clean) == []


def test_filter_enrichment_passes_through_real_data():
    """_filter_enrichment must keep real ORM columns, not drop them."""
    enrichment = {
        "human_hazards": {
            "nearest_military_km": 12.5,
            "nearest_military_name": "Range X",
            "military_count": 1,
            "hi06_quality": "high",
            "hi06_comment": "OSM military polygon",
            "unrelated_field": "noise",
        }
    }
    filtered = _filter_enrichment(enrichment, "A5")
    kept = filtered["human_hazards"]
    assert set(kept.keys()) == {
        "nearest_military_km",
        "nearest_military_name",
        "military_count",
        "hi06_quality",
        "hi06_comment",
    }
    assert "unrelated_field" not in kept


def test_compute_enrichment_coverage_counts_real_data():
    """Coverage must count only data fields that exist on the ORM model."""
    cached = {
        "enrichment": {
            "infrastructure": {
                "buildable_area_ha": 45.0,
                "largest_contiguous_ha": 30.0,
                "patch_count": 3,
                "ns05_quality": "medium",
                "ns05_comment": "ok",
            }
        }
    }
    cov = compute_enrichment_coverage(cached, "A15")
    assert set(cov["expected_fields"]) == {
        "buildable_area_ha",
        "largest_contiguous_ha",
        "patch_count",
    }
    assert set(cov["available_fields"]) == {
        "buildable_area_ha",
        "largest_contiguous_ha",
        "patch_count",
    }
    assert cov["coverage_pct"] == 1.0


def test_row_to_dict_emits_real_orm_keys():
    """_row_to_dict must emit the actual ORM attribute names, proving the
    field set used for filtering is the one the ORM produces.
    """
    row = orm.SiteHumanHazards(
        site_id=None,
        nearest_military_km=5.0,
        nearest_military_name="Sample Range",
        military_count=1,
        hi06_quality="high",
    )
    out = _row_to_dict(row)
    assert "nearest_military_km" in out
    assert "nearest_military_name" in out
    assert "hi06_quality" in out
    assert "hi06_nearest_military_km" not in out
