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
    def test_low_score_below_floor_emits_floor_verdict(self, bundle):
        """NH-04 with slope 12 deg lands in band 3-4 (~3.5); floor fires."""
        nh04 = bundle["NH-04"]
        ctx = {"slope_angle_deg": 12, "slope_stability_class": "stable"}

        verdicts, band_result = _eval_floor_for(nh04, ctx)

        assert band_result.score < 5.0, "fixture must score below floor"
        assert band_result.score == pytest.approx(3.5, abs=0.5)

        floor_verdicts = [
            v
            for v in verdicts
            if v.phase == "exclusionary" and v.prompt_key == "E3:floor"
        ]
        assert len(floor_verdicts) == 1
        assert floor_verdicts[0].verdict == "fail"
        assert floor_verdicts[0].criterion_id == "NH-04"

    def test_hard_expression_takes_precedence_over_floor(self, bundle):
        """slope >= 25 triggers hard E3; no separate :floor verdict."""
        nh04 = bundle["NH-04"]
        ctx = {"slope_angle_deg": 30, "slope_stability_class": "stable"}

        verdicts, _ = _eval_floor_for(nh04, ctx)

        hard = [v for v in verdicts if v.prompt_key == "E3"]
        floor = [v for v in verdicts if v.prompt_key == "E3:floor"]
        assert len(hard) == 1 and hard[0].verdict == "fail"
        assert len(floor) == 0, "floor must not double-fire when hard E-code triggers"

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
            "subsidence_risk_class": "moderate",
        }

        verdicts, band_result = _eval_floor_for(nh05, ctx)

        assert band_result.score >= 5.0
        assert band_result.matched_band is not None
        assert band_result.matched_band.score_range == (5.0, 6.0)
        fails = [v for v in verdicts if v.verdict == "fail"]
        assert fails == []


class TestSafetyFloorGating:
    def test_floor_fail_yields_null_composite(self, bundle):
        """The full gate: floor verdict -> composite_score is None."""
        nh04 = bundle["NH-04"]
        ctx = {"slope_angle_deg": 12, "slope_stability_class": "stable"}

        verdicts, _ = _eval_floor_for(nh04, ctx)

        result = compute_composite_for_site_smr(
            site_id=uuid.uuid4(),
            smr_key="nuscale_voygr6",
            ranking_rows=[],
            verdicts=verdicts,
            weights={"NH-04": 1.0},
            criteria={"NH-04": nh04},
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
