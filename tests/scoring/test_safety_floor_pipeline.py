"""End-to-end regression for the exclusionary safety floor.

Verifies the two key invariants documented in
``report/methodology/exclusionary_floors.md``:

1. **Transparency** — when the floor fires, the underlying ranking row
   keeps its raw 0-10 score (engine writes it; composite skips it). The
   audit trail records exactly how badly the site failed.
2. **Gating** — the synthetic ``:floor`` verdict drives
   ``passed_exclusionary = False`` and ``composite_score = None`` in the
   composite layer, which `_suite_banding` then drops via its
   ``if score is None: continue`` guard. Failed sites cannot leak into
   any ranking, top-N list, or country shortlist.

The test exercises the pure-Python helpers (no DB) so it stays fast and
deterministic; the full pipeline is re-checked at re-score time against
the merged DB in :mod:`scripts.run_phase_1_6_sensitivity`.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from atoms_vs_ashes.scoring.bands import evaluate_criterion_value
from atoms_vs_ashes.scoring.composite import compute_composite_for_site_smr
from atoms_vs_ashes.scoring.exclusionary import evaluate_exclusionary_for_site
from atoms_vs_ashes.scoring.rubric import load_rubric_bundle

REPO_ROOT = Path(__file__).resolve().parents[2]
RUBRIC_DIR = REPO_ROOT / "config" / "scoring_rubrics"


@pytest.fixture(scope="module")
def bundle():
    return load_rubric_bundle(RUBRIC_DIR)


def _eval_floor_for(criterion, context: dict) -> tuple[list, "BandResult"]:
    """Evaluate the criterion's bands and run the exclusionary check.

    Returns ``(verdicts, band_result)``. The verdicts are
    ``ScreeningVerdict`` rows that would be persisted by the engine.
    """
    band_result = evaluate_criterion_value(criterion, context, quality="medium")
    verdicts = evaluate_exclusionary_for_site(
        criterion,
        context,
        site_id=uuid.uuid4(),
        smr_key="nuscale_voygr6",
        run_id="floor-test",
        confidence="medium",
        data_sources=["api:test"],
        band_result=band_result,
    )
    return verdicts, band_result


class TestSafetyFloorTransparency:
    # The single-pivot fix (band_recipe.score5_pivot drives both bands
    # and hard expression) makes the floor STRUCTURALLY unreachable for
    # NH-04 / NH-02 / NH-07 — at any value below the score-5 boundary
    # the hard expression already triggers. The floor is preserved as a
    # backstop for HAND-WRITTEN rubrics where the bands and the hard
    # expression are declared independently; NH-03 is the canonical
    # such criterion. These tests exercise the floor against NH-03,
    # which has a real band/exclusion gap at (very_high, null) by
    # design (see config/scoring_rubrics/nh_natural_hazards.yaml NH-03
    # bands 3-4 descriptor).

    def test_low_score_below_floor_emits_floor_verdict(self, bundle):
        """NH-03 at (very_high, null) lands in band 3-4 (score 3.5) but
        the hard expression requires ``has_remedy == false``; null does
        not satisfy that, so the floor fires."""
        nh03 = bundle["NH-03"]
        ctx = {"liquefaction_suscept": "very_high", "has_remedy": None}

        verdicts, band_result = _eval_floor_for(nh03, ctx)

        assert band_result.score < 5.0, "fixture must score below floor"
        assert band_result.score == pytest.approx(3.5, abs=0.5)

        floor_verdicts = [
            v
            for v in verdicts
            if v.phase == "exclusionary" and v.prompt_key == "E2:floor"
        ]
        assert len(floor_verdicts) == 1
        assert floor_verdicts[0].verdict == "fail"
        assert floor_verdicts[0].criterion_id == "NH-03"

    def test_hard_expression_takes_precedence_over_floor(self, bundle):
        """NH-03 at (very_high, false): hard E2 fires; no :floor verdict.

        Also covers the NH-04 single-pivot path: slope > 25 trips E3
        directly without a separate :floor.
        """
        nh03 = bundle["NH-03"]
        ctx_hard = {"liquefaction_suscept": "very_high", "has_remedy": False}
        verdicts, _ = _eval_floor_for(nh03, ctx_hard)
        hard = [v for v in verdicts if v.prompt_key == "E2"]
        floor = [v for v in verdicts if v.prompt_key == "E2:floor"]
        assert len(hard) == 1 and hard[0].verdict == "fail"
        assert len(floor) == 0, "floor must not double-fire when hard E-code triggers"

        nh04 = bundle["NH-04"]
        ctx_nh04 = {"slope_angle_deg": 30, "slope_stability_class": "stable"}
        verdicts_nh04, _ = _eval_floor_for(nh04, ctx_nh04)
        hard_nh04 = [v for v in verdicts_nh04 if v.prompt_key == "E3"]
        floor_nh04 = [v for v in verdicts_nh04 if v.prompt_key == "E3:floor"]
        assert len(hard_nh04) == 1 and hard_nh04[0].verdict == "fail"
        assert len(floor_nh04) == 0

    def test_passing_score_emits_no_exclusion(self, bundle):
        nh04 = bundle["NH-04"]
        ctx = {"slope_angle_deg": 2, "slope_stability_class": "stable"}

        verdicts, band_result = _eval_floor_for(nh04, ctx)

        assert band_result.score >= 5.0
        fails = [v for v in verdicts if v.verdict == "fail"]
        assert fails == []

    def test_nh05_moderate_areal_subsidence_is_not_exclusionary(self, bundle):
        nh05 = bundle["NH-05"]
        ctx = {
            "karst_severity": "moderate",
            "mining_void_present": False,
            "mining_void_distance_km": None,
            "subsidence_risk_class": "moderate",
        }

        verdicts, band_result = _eval_floor_for(nh05, ctx)

        assert band_result.score >= 5.0
        assert band_result.matched_band is not None
        assert band_result.matched_band.score_range == (5.0, 6.0)
        fails = [v for v in verdicts if v.verdict == "fail"]
        assert fails == []

    def test_nh05_high_areal_subsidence_is_possible_not_exclusionary(self, bundle):
        nh05 = bundle["NH-05"]
        ctx = {
            "karst_severity": "moderate",
            "mining_void_present": False,
            "mining_void_distance_km": None,
            "subsidence_risk_class": "high",
        }

        verdicts, band_result = _eval_floor_for(nh05, ctx)

        assert band_result.score >= 5.0
        assert band_result.matched_band is not None
        assert band_result.matched_band.score_range == (5.0, 6.0)
        fails = [v for v in verdicts if v.verdict == "fail"]
        assert fails == []

    def test_nh05_missing_mining_void_and_subsidence_data_passes(self, bundle):
        """NH-05 with karst='none' and all other risk signals null lands in the
        favourable [9,10] band: the rubric explicitly reads "mine distance
        favourable or unknown with no subsidence signal" → [9,10]. The earlier
        (5.0, 6.0) expectation captured the pre-fix safe_eval bug where a
        TypeError in the first disjunct of the [9,10] / [7,8] bands poisoned
        the whole expression and the site fell through to the conservative
        pass-mark. After the P0-1 AST fix the intended favourable band fires.
        The exclusionary contract (no E5/E6 fails) is unchanged.
        """
        nh05 = bundle["NH-05"]
        ctx = {
            "karst_severity": "none",
            "mining_void_present": None,
            "mining_void_distance_km": None,
            "subsidence_risk_class": None,
        }

        verdicts, band_result = _eval_floor_for(nh05, ctx)

        assert band_result.score >= 5.0
        assert band_result.matched_band is not None
        assert band_result.matched_band.score_range == (9.0, 10.0)
        fails = [v for v in verdicts if v.verdict == "fail"]
        assert fails == []

    def test_nh05_mining_boolean_alone_is_not_exclusionary(self, bundle):
        nh05 = bundle["NH-05"]
        ctx = {
            "karst_severity": "none",
            "mining_void_present": True,
            "mining_void_distance_km": None,
            "subsidence_risk_class": None,
        }

        verdicts, band_result = _eval_floor_for(nh05, ctx)

        assert band_result.score >= 5.0
        assert band_result.matched_band is not None
        hard = [v for v in verdicts if v.prompt_key == "E6" and v.verdict == "fail"]
        assert hard == []

    @pytest.mark.parametrize(
        ("distance_km", "expected_range"),
        [
            (1.9, (3.0, 4.0)),
            (2.0, (5.0, 6.0)),
            (4.9, (7.0, 8.0)),
        ],
    )
    def test_nh05_mine_distance_scores_from_two_km_pivot_without_exclusion(
        self, bundle, distance_km, expected_range,
    ):
        nh05 = bundle["NH-05"]
        ctx = {
            "karst_severity": "none",
            "mining_void_present": True,
            "mining_void_distance_km": distance_km,
            "subsidence_risk_class": "none",
        }

        verdicts, band_result = _eval_floor_for(nh05, ctx)

        assert band_result.matched_band is not None
        assert band_result.matched_band.score_range == expected_range
        if distance_km >= 2.0:
            assert band_result.score >= 5.0
        fails = [v for v in verdicts if v.verdict == "fail"]
        assert fails == []

    @pytest.mark.parametrize(
        ("criterion_id", "ctx"),
        [
            (
                "EP-01",
                {
                    "ep01_composite_score": 35,
                    "nearest_trauma_center_km": 40,
                },
            ),
            (
                "NH-10",
                {"max_wind_speed_ms": 45},
            ),
            (
                "NS-01",
                {
                    "cooling_source_type": "groundwater",
                    "cooling_distance_km": 8,
                    "dry_cooling_viable": False,
                    "spi12_min": -3.0,
                    "strahler_order": None,
                    "water_stress_score": 4.5,
                },
            ),
            (
                "NS-08",
                {
                    "ecological_natural_pct": 90,
                    "n2k_nearest_distance_km": 1,
                    "site_within_strict_protected": False,
                },
            ),
        ],
    )
    def test_low_score_hard_expression_only_criteria_do_not_floor_fail(
        self, bundle, criterion_id, ctx,
    ):
        criterion = bundle[criterion_id]

        verdicts, band_result = _eval_floor_for(criterion, ctx)

        assert band_result.score < 5.0
        floor_fails = [
            v for v in verdicts
            if v.verdict == "fail" and str(v.prompt_key).endswith(":floor")
        ]
        hard_fails = [v for v in verdicts if v.verdict == "fail"]
        assert floor_fails == []
        assert hard_fails == []


class TestSafetyFloorGating:
    def test_floor_fail_yields_null_composite(self, bundle):
        """The full gate: floor verdict -> composite_score is None.

        Uses NH-03 (very_high, null) — the canonical floor-only path,
        since NH-04's single-pivot rubric closes the band/exclusion gap
        and so cannot exercise the floor in isolation.
        """
        nh03 = bundle["NH-03"]
        ctx = {"liquefaction_suscept": "very_high", "has_remedy": None}

        verdicts, _ = _eval_floor_for(nh03, ctx)

        result = compute_composite_for_site_smr(
            site_id=uuid.uuid4(),
            smr_key="nuscale_voygr6",
            ranking_rows=[],
            verdicts=verdicts,
            weights={"NH-03": 1.0},
            criteria={"NH-03": nh03},
        )
        assert result.passed_exclusionary is False
        assert result.composite_score is None
        assert "excluded_by_E_code" in result.notes

    def test_banding_skips_null_composite_rows(self):
        """Documents the contract enforced by `_suite_banding._load_nonbaseline_rows`.

        ``score is None`` rows are dropped before any top-N / band logic
        runs, so a floor-failed pair cannot leak into rankings even if a
        downstream caller forgets to filter on ``passed_exclusionary``.
        See ``src/atoms_vs_ashes/scoring/_suite_banding.py`` L99-101.
        """
        from atoms_vs_ashes.scoring import _suite_banding

        source = (REPO_ROOT / "src/atoms_vs_ashes/scoring/_suite_banding.py").read_text()
        assert "if score is None:" in source
        assert "continue" in source
        # And the helper at top of the module:
        assert hasattr(_suite_banding, "_load_nonbaseline_rows")
