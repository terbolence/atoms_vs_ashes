# man_hours: 1.0
"""NS-08 strict-overlap derivation and bands.

Locks the SSG-35 Table II-1 strict-overlap semantics:

- Natura 2000 polygon overlap (any sitetype) -> E7 strict-protected.
- WDPA polygon overlap with IUCN Ia/Ib/II -> E7 strict-protected.
- WDPA polygon overlap with an international designation (Ramsar, WHS,
  Biosphere, Emerald) -> E7 strict-protected.
- WDPA polygon overlap with IUCN III/IV/V/VI only -> NOT strict. The
  site keeps its band-driven score and surfaces the R1 review_flag from
  ``wdpa_sensitivity_class == 'high'`` if applicable.

Also locks the NULL-as-positive-evidence band behaviour: connector-NULL
distance (search ran, no protected area within 25 km) lifts the site to
the top band, matching NH-07's ``null_policy='best'`` pattern even
though NS-08's bands are hand-written rather than recipe-generated.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from atoms_vs_ashes.criterion_spec import compile_bundle, load_template_bundle
from atoms_vs_ashes.scoring.bands import evaluate_criterion_value, safe_eval
from atoms_vs_ashes.scoring.merge_context_derivations import (
    apply_derived_context_values,
)

SPEC_DIR = Path(__file__).resolve().parents[2] / "config" / "scoring_specs"


@pytest.fixture(scope="module")
def ns08():
    bundle = compile_bundle(load_template_bundle(str(SPEC_DIR)))
    return bundle.criteria["NS-08"]


# ---------------------------------------------------------------------------
# Fail conditions are declared as the contract demands
# ---------------------------------------------------------------------------


def test_e7_fail_condition_uses_derived_strict_flag(ns08):
    e7 = next(fc for fc in ns08.fail_conditions if fc.code == "E7")
    assert e7.action == "exclude"
    assert e7.condition_expr == "site_within_strict_protected == true"


def test_r1_review_flag_is_declared(ns08):
    r1 = next((fc for fc in ns08.fail_conditions if fc.code == "R1"), None)
    assert r1 is not None, "NS-08 missing R1 review_flag"
    assert r1.action == "review_flag"
    assert "n2k_sensitivity_class == 'high'" in r1.condition_expr
    assert "wdpa_sensitivity_class == 'high'" in r1.condition_expr
    # review_flag must not declare a pass_mark.
    assert r1.pass_mark is None


# ---------------------------------------------------------------------------
# Strictness derivation in merge_context_derivations
# ---------------------------------------------------------------------------


def _build_ctx(**fields):
    ctx = {
        "n2k_nearest_distance_km": None,
        "wdpa_nearest_distance_km": None,
        "ecological_natural_pct": None,
        "n2k_overlap": None,
        "wdpa_overlap": None,
        "n2k_sensitivity_class": None,
        "wdpa_sensitivity_class": None,
        "n2k_result_json": None,
        "wdpa_result_json": None,
    }
    ctx.update(fields)
    apply_derived_context_values(ctx)
    return ctx


def test_n2k_polygon_overlap_is_strict():
    ctx = _build_ctx(n2k_overlap=True, n2k_nearest_distance_km=0.0)
    assert ctx["site_within_strict_protected"] is True


def test_wdpa_overlap_iucn_ia_is_strict():
    ctx = _build_ctx(
        wdpa_overlap=True,
        wdpa_nearest_distance_km=0.0,
        wdpa_result_json={
            "wdpa_strictest_iucn_category": "Ia",
            "wdpa_international_designation_count": 0,
        },
    )
    assert ctx["site_within_strict_protected"] is True
    assert ctx["wdpa_strict_overlap"] is True


def test_wdpa_overlap_iucn_iii_is_NOT_strict():
    """IUCN III (Natural Monument) overlap is not exclusionary on its own."""
    ctx = _build_ctx(
        wdpa_overlap=True,
        wdpa_nearest_distance_km=0.0,
        wdpa_sensitivity_class="high",  # connector still flags 'high'
        wdpa_result_json={
            "wdpa_strictest_iucn_category": "III",
            "wdpa_international_designation_count": 0,
        },
    )
    assert ctx["site_within_strict_protected"] is False
    assert ctx["wdpa_strict_overlap"] is False


def test_wdpa_overlap_iucn_iv_is_NOT_strict():
    """IUCN IV (Habitat/Species Management) overlap is not exclusionary."""
    ctx = _build_ctx(
        wdpa_overlap=True,
        wdpa_nearest_distance_km=0.0,
        wdpa_result_json={
            "wdpa_strictest_iucn_category": "IV",
            "wdpa_international_designation_count": 0,
        },
    )
    assert ctx["site_within_strict_protected"] is False


def test_wdpa_overlap_with_international_designation_is_strict():
    """Ramsar / WHS / Emerald polygon overlap is exclusionary even
    when the IUCN slot is 'Not Reported' or low-category."""
    ctx = _build_ctx(
        wdpa_overlap=True,
        wdpa_nearest_distance_km=0.0,
        wdpa_result_json={
            "wdpa_strictest_iucn_category": "IV",
            "wdpa_international_designation_count": 2,
        },
    )
    assert ctx["site_within_strict_protected"] is True


def test_wdpa_close_strict_without_polygon_overlap_is_NOT_e7():
    """A site 1 km from an IUCN Ia polygon (but not inside it) must not
    fire E7. The plant footprint will not reach into the strict zone.
    The R1 review_flag fires via wdpa_sensitivity_class instead."""
    ctx = _build_ctx(
        wdpa_overlap=False,
        wdpa_nearest_distance_km=1.0,
        wdpa_sensitivity_class="high",
        wdpa_result_json={
            "wdpa_strictest_iucn_category": "Ia",
            "wdpa_international_designation_count": 0,
        },
    )
    assert ctx["site_within_strict_protected"] is False


def test_legacy_distance_only_context_still_derives_strict():
    """Callers that build a minimal context (without JSONB / overlap
    booleans) keep the legacy distance-based behaviour. Required so
    older unit tests and scripts do not regress."""
    ctx = {
        "n2k_nearest_distance_km": 0.0,
        "wdpa_nearest_distance_km": None,
    }
    apply_derived_context_values(ctx)
    assert ctx["site_within_strict_protected"] is True


# ---------------------------------------------------------------------------
# Band evaluation — NULL = best, real-data anchors
# ---------------------------------------------------------------------------


def _score(ns08, **fields):
    ctx = _build_ctx(**fields)
    return evaluate_criterion_value(ns08, ctx, quality="medium").score


def test_null_both_networks_lands_top_band(ns08):
    """Connector-NULL on both networks means no protected area within
    the 25 km search radius. With eco_pct also NULL the site reads as
    'no evidence of ecological constraint', so band 9-10 is correct."""
    assert _score(ns08, n2k_nearest_distance_km=None, wdpa_nearest_distance_km=None) == 9.5


def test_null_distance_but_high_eco_pct_drops_to_7_8(ns08):
    """The top-band AND clause requires eco_pct NULL or < 15. High
    eco_pct should drop the score to 7-8 even with both distances NULL."""
    s = _score(
        ns08,
        n2k_nearest_distance_km=None,
        wdpa_nearest_distance_km=None,
        ecological_natural_pct=44.4,
    )
    assert s == 7.5


def test_close_wdpa_but_null_n2k_lands_in_low_band(ns08):
    """A close WDPA boundary must not be rescued by a NULL Natura 2000
    distance. The 1-2 band fires on either network < 2 km."""
    s = _score(
        ns08,
        n2k_nearest_distance_km=None,
        wdpa_nearest_distance_km=0.5,
        wdpa_sensitivity_class="high",
    )
    assert s == 1.5


def test_e7_only_fires_on_strict_overlap(ns08):
    """A site with IUCN III centroid overlap must score in the 1-2 band
    (close WDPA) with verdict pass, not E7."""
    ctx = _build_ctx(
        wdpa_overlap=True,
        wdpa_nearest_distance_km=0.0,
        wdpa_sensitivity_class="high",
        wdpa_result_json={
            "wdpa_strictest_iucn_category": "III",
            "wdpa_international_designation_count": 0,
        },
    )
    e7 = next(fc for fc in ns08.fail_conditions if fc.code == "E7")
    assert safe_eval(e7.condition_expr, ctx) is False

    iucn_ia_ctx = _build_ctx(
        wdpa_overlap=True,
        wdpa_nearest_distance_km=0.0,
        wdpa_result_json={
            "wdpa_strictest_iucn_category": "Ia",
            "wdpa_international_designation_count": 0,
        },
    )
    assert safe_eval(e7.condition_expr, iucn_ia_ctx) is True
