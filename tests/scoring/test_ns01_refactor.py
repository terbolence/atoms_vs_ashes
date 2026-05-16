# man_hours: 1.5
"""Regression tests for the 2026-05-16 NS-01 refactor (E9 → A16).

Locks the post-refactor behaviour documented in LL-036:

- Source-type sub-score (A, 0.44) is keyed on the HydroRIVERS connector
  vocabulary ``{major_river, river, small_river, stream}`` plus an
  explicit "no source within 50 km" null branch and a degenerate 0-band
  for ``cooling_source_type is null and dry_cooling_viable == false``.
- Distance-to-source sub-score (B, 0.25) unchanged.
- Water-stress sub-score (C, 0.31) is keyed on the categorical
  ``water_stress_label`` rather than the raw ``water_stress_score``
  axis the connector caps at ~2.1 today.
- Seasonal-drought sub-score (D, 0.20) was removed; A/B/C re-normalise
  from 0.35/0.20/0.25 to 0.44/0.25/0.31.
- E9 (exclude) was replaced by A16 (avoidance_penalty) with condition
  ``cooling_distance_km > 10 and water_stress_label in
  ('High', 'Extremely High')``.
- ``dry_cooling_viable`` is now a derived context value:
  ``country_code in ARID_OR_HOT_SUMMER_ISO2`` (TR, CY, MT, ES, PT, GR)
  AND ``water_stress_label == 'Extremely High'`` ⇒ False; else True.
- NS-01 phase flipped from ``[exclusionary, ranking]`` to
  ``[avoidance, ranking]`` and ``participates_in_composite`` is now
  True so NS-01 contributes to the composite weight.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from atoms_vs_ashes.criterion_spec import compile_bundle, load_template_bundle
from atoms_vs_ashes.scoring.bands import evaluate_criterion_value, safe_eval
from atoms_vs_ashes.scoring.merge_context_derivations import (
    DERIVED_CONTEXT_NAMES,
    apply_derived_context_values,
)
from atoms_vs_ashes.scoring.rubric import load_rubric_bundle

REPO_ROOT = Path(__file__).resolve().parents[2]
RUBRIC_DIR = REPO_ROOT / "config" / "scoring_rubrics"
SPEC_DIR = REPO_ROOT / "config" / "scoring_specs"


@pytest.fixture(scope="module")
def rubric_bundle():
    return load_rubric_bundle(RUBRIC_DIR)


@pytest.fixture(scope="module")
def spec_criterion():
    """Compiled NS-01 from the spec bundle (gives `participates_in_composite`)."""
    bundle = compile_bundle(load_template_bundle(SPEC_DIR))
    return bundle.criteria["NS-01"]


# ---------------------------------------------------------------------------
# Phase + composite participation
# ---------------------------------------------------------------------------


class TestPhaseAndComposite:
    def test_ns01_phase_is_avoidance_ranking(self, spec_criterion):
        assert spec_criterion.phases == ["avoidance", "ranking"]

    def test_ns01_participates_in_composite(self, spec_criterion):
        assert spec_criterion.participates_in_composite is True

    def test_ns01_has_no_exclude_fail_conditions(self, rubric_bundle):
        ns01 = rubric_bundle["NS-01"]
        actions = {fc.action for fc in ns01.fail_conditions}
        assert "exclude" not in actions
        assert "avoidance_penalty" in actions

    def test_ns01_a16_is_the_only_fail_condition(self, rubric_bundle):
        ns01 = rubric_bundle["NS-01"]
        codes = [fc.code for fc in ns01.fail_conditions]
        assert codes == ["A16"]

    def test_sub_score_weights_renormalise_to_one(self, rubric_bundle):
        ns01 = rubric_bundle["NS-01"]
        weights = {s.key: s.weight for s in ns01.sub_scores}
        assert weights == {
            "source_type": 0.44,
            "distance_to_source": 0.25,
            "water_stress": 0.31,
        }
        assert sum(weights.values()) == pytest.approx(1.0)

    def test_seasonal_drought_sub_score_removed(self, rubric_bundle):
        ns01 = rubric_bundle["NS-01"]
        keys = {s.key for s in ns01.sub_scores}
        assert "seasonal_drought" not in keys

    def test_spi12_min_dropped_from_db_fields_api(self, rubric_bundle):
        ns01 = rubric_bundle["NS-01"]
        assert "site_natural_hazards.spi12_min" not in ns01.db_fields.api
        assert "site_infrastructure_v2.water_stress_label" in ns01.db_fields.api


# ---------------------------------------------------------------------------
# Source-type sub-score bands (HydroRIVERS vocabulary)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("cooling_source_type", "cooling_distance_km", "expected_band"),
    [
        ("major_river", 0.5, (9.0, 10.0)),
        ("river", 1.0, (7.0, 8.0)),
        ("small_river", 1.0, (5.0, 6.0)),
        ("stream", 1.0, (3.0, 4.0)),
        (None, 15.0, (1.0, 2.0)),
        (None, None, (1.0, 2.0)),
    ],
)
def test_source_type_band_matches_connector_vocabulary(
    rubric_bundle, cooling_source_type, cooling_distance_km, expected_band
):
    ns01 = rubric_bundle["NS-01"]
    sub = next(s for s in ns01.sub_scores if s.key == "source_type")
    ctx = {
        "cooling_source_type": cooling_source_type,
        "cooling_distance_km": cooling_distance_km,
        # dry_cooling_viable=True keeps the 0-band out of reach
        "dry_cooling_viable": True,
    }
    matched = None
    for band in sub.bands:
        if safe_eval(band.condition_expr, ctx) is True:
            matched = tuple(band.score_range)
            break
    assert matched == expected_band, (
        f"Expected {expected_band} for "
        f"(cooling_source_type={cooling_source_type!r}, "
        f"cooling_distance_km={cooling_distance_km}); got {matched}"
    )


def test_source_type_zero_band_requires_dry_cooling_not_viable(rubric_bundle):
    """The 0-band only fires when there is NO source AND dry cooling is judged
    not viable (the degenerate case that replaces the retired E9 hard fail).
    """
    ns01 = rubric_bundle["NS-01"]
    sub = next(s for s in ns01.sub_scores if s.key == "source_type")
    zero_band = next(b for b in sub.bands if tuple(b.score_range) == (0.0, 0.0))

    # Triggers
    ctx_fail = {"cooling_source_type": None, "dry_cooling_viable": False}
    assert safe_eval(zero_band.condition_expr, ctx_fail) is True

    # Does NOT trigger when dry cooling is viable (default for most sites)
    ctx_ok = {"cooling_source_type": None, "dry_cooling_viable": True}
    assert safe_eval(zero_band.condition_expr, ctx_ok) is not True


# ---------------------------------------------------------------------------
# Water-stress sub-score (categorical label)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("water_stress_label", "expected_band"),
    [
        ("Low", (9.0, 10.0)),
        ("Low-Medium", (7.0, 8.0)),
        ("Medium-High", (5.0, 6.0)),
        ("High", (3.0, 4.0)),
        ("Extremely High", (1.0, 2.0)),
    ],
)
def test_water_stress_band_matches_aqueduct_label(
    rubric_bundle, water_stress_label, expected_band
):
    ns01 = rubric_bundle["NS-01"]
    sub = next(s for s in ns01.sub_scores if s.key == "water_stress")
    ctx = {"water_stress_label": water_stress_label}
    matched = None
    for band in sub.bands:
        if safe_eval(band.condition_expr, ctx) is True:
            matched = tuple(band.score_range)
            break
    assert matched == expected_band


# ---------------------------------------------------------------------------
# A16 avoidance penalty
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("cooling_distance_km", "water_stress_label", "expected_trigger"),
    [
        (15.0, "Extremely High", True),
        (11.0, "High", True),
        (10.0, "High", False),  # boundary: > 10 km, so 10 must NOT trigger
        (15.0, "Medium-High", False),
        (5.0, "Extremely High", False),
        (15.0, None, False),  # missing label → no trigger
        (None, "High", False),  # missing distance → no trigger
    ],
)
def test_a16_fires_only_on_distant_and_water_stressed_sites(
    rubric_bundle, cooling_distance_km, water_stress_label, expected_trigger
):
    ns01 = rubric_bundle["NS-01"]
    a16 = next(fc for fc in ns01.fail_conditions if fc.code == "A16")
    assert a16.action == "avoidance_penalty"
    ctx = {
        "cooling_distance_km": cooling_distance_km,
        "water_stress_label": water_stress_label,
    }
    result = safe_eval(a16.condition_expr, ctx)
    assert (result is True) == expected_trigger, (
        f"A16 trigger mismatch for cooling_distance_km={cooling_distance_km}, "
        f"water_stress_label={water_stress_label!r}: got {result}"
    )


# ---------------------------------------------------------------------------
# dry_cooling_viable derivation
# ---------------------------------------------------------------------------


class TestDryCoolingViableDerivation:
    def test_dry_cooling_viable_in_derived_context_names(self):
        assert "dry_cooling_viable" in DERIVED_CONTEXT_NAMES

    @pytest.mark.parametrize(
        ("country_code", "water_stress_label", "expected"),
        [
            ("TR", "Extremely High", False),
            ("ES", "Extremely High", False),
            ("CY", "Extremely High", False),
            ("MT", "Extremely High", False),
            ("PT", "Extremely High", False),
            ("GR", "Extremely High", False),
            # Same country, lower stress → viable
            ("TR", "High", True),
            ("TR", "Low", True),
            # Non-arid country at any stress → viable
            ("PL", "Extremely High", True),
            ("DE", "Extremely High", True),
            ("RO", "Low", True),
            # Missing inputs → conservative True default
            (None, "Extremely High", True),
            ("TR", None, True),
            (None, None, True),
        ],
    )
    def test_derive_dry_cooling_viable(
        self, country_code, water_stress_label, expected
    ):
        values = {
            "country_code": country_code,
            "water_stress_label": water_stress_label,
        }
        apply_derived_context_values(values)
        assert values["dry_cooling_viable"] is expected

    def test_caller_supplied_value_takes_precedence(self):
        """A pre-populated dry_cooling_viable (e.g. from an LLM-promoted
        field) must not be overwritten by the heuristic derivation."""
        values = {
            "dry_cooling_viable": False,
            "country_code": "PL",
            "water_stress_label": "Low",
        }
        apply_derived_context_values(values)
        assert values["dry_cooling_viable"] is False


# ---------------------------------------------------------------------------
# Composite criterion behaviour on representative DB-shaped contexts
# ---------------------------------------------------------------------------


def _ns01_context(**overrides) -> dict:
    """Minimal NS-01 context populated with the columns NS-01 reads."""
    base = {
        "cooling_source_type": "major_river",
        "cooling_source_name": "Danube",
        "cooling_source_hyriv_id": 12345,
        "cooling_distance_km": 0.3,
        "cooling_flow_m3s": 6500.0,
        "water_stress_score": 0.1,
        "water_stress_label": "Low",
        "country_code": "RO",
    }
    base.update(overrides)
    apply_derived_context_values(base)
    return base


def test_ns01_strong_site_scores_above_pass_mark(rubric_bundle):
    """Mellach-shape (AT major river, low stress, 0.03 km)."""
    ns01 = rubric_bundle["NS-01"]
    ctx = _ns01_context(
        cooling_source_type="major_river",
        cooling_distance_km=0.03,
        water_stress_label="Low",
        country_code="AT",
    )
    result = evaluate_criterion_value(ns01, ctx, quality="medium")
    assert result.score >= 9.0


def test_ns01_stream_only_distant_site_scores_low(rubric_bundle):
    """Stream-class source far from the plant, high water stress."""
    ns01 = rubric_bundle["NS-01"]
    ctx = _ns01_context(
        cooling_source_type="stream",
        cooling_distance_km=12.0,
        water_stress_label="Extremely High",
        country_code="TR",
    )
    result = evaluate_criterion_value(ns01, ctx, quality="medium")
    # source_type=stream → 3.5, distance>10 → 1.5, label=ExtremelyHigh → 1.5
    # weighted mean ≈ 0.44*3.5 + 0.25*1.5 + 0.31*1.5 = 1.54 + 0.375 + 0.465 = 2.38
    assert result.score < 3.0


def test_ns01_does_not_floor_fail_today(rubric_bundle):
    """NS-01 has no exclude fail_condition; even a degenerate context must
    not emit a hard-fail or :floor verdict."""
    ns01 = rubric_bundle["NS-01"]
    assert all(fc.action != "exclude" for fc in ns01.fail_conditions)
