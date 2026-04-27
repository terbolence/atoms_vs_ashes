# man_hours: 1.0
"""Unit tests for the pure helpers that back the targeted-threshold sweep.

Validates target enumeration (numeric only, base-value resolution from
``profile.fail_thresholds`` ↔ recommended), perturbation arithmetic,
and the writer artefact contract — all without touching the DB. The
end-to-end sweep itself is covered by the integration tests that drive
:func:`run_targeted_threshold_sensitivity` against the snapshot
session.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from atoms_vs_ashes.criterion_spec import load_template_bundle
from atoms_vs_ashes.runprofile import RunProfile
from atoms_vs_ashes.scoring._suite_threshold_targeted_helpers import (
    TargetedThreshold,
    TargetedThresholdRow,
    TargetedThresholdSuiteResult,
    build_overrides,
    diff_results,
    list_targeted_thresholds,
    make_row,
    percentile,
    perturb_value,
)
from atoms_vs_ashes.scoring._targeted_threshold_writer import (
    render_targeted_threshold_md,
    write_targeted_threshold_artefacts,
)
from atoms_vs_ashes.scoring.composite import CompositeResult


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_DIR = REPO_ROOT / "config" / "scoring_specs"


@pytest.fixture(scope="module")
def template_bundle():
    return load_template_bundle(str(SPEC_DIR))


def test_targets_skip_categorical_and_pickup_numeric(template_bundle):
    profile = RunProfile(run_label="baseline")
    targets = list_targeted_thresholds(template_bundle, profile)
    assert targets, "expected at least one numeric user-controlled threshold"
    nh02_e1 = next(
        (t for t in targets if t.criterion_id == "NH-02" and t.code == "E1"), None
    )
    assert nh02_e1 is not None
    assert nh02_e1.metric == "nearest_fault_km"
    assert nh02_e1.op == "<"
    assert nh02_e1.base_value == pytest.approx(8.0)
    assert nh02_e1.recommended_value == pytest.approx(8.0)


def test_user_override_becomes_base_value(template_bundle):
    profile = RunProfile(
        run_label="custom",
        fail_thresholds={"NH-02": {"E1": 7.5}},
    )
    targets = list_targeted_thresholds(template_bundle, profile)
    nh02_e1 = next(t for t in targets if t.criterion_id == "NH-02" and t.code == "E1")
    assert nh02_e1.base_value == pytest.approx(7.5)
    assert nh02_e1.recommended_value == pytest.approx(8.0)


def test_perturb_value_signed_correctly():
    assert perturb_value(10.0, 25.0, "down") == pytest.approx(7.5)
    assert perturb_value(10.0, 25.0, "up") == pytest.approx(12.5)


def test_build_overrides_clones_existing_thresholds():
    profile = RunProfile(
        run_label="custom",
        fail_thresholds={"NH-02": {"E1": 5.0}, "NH-04": {"E3": 25.0}},
    )
    out = build_overrides(profile, "NH-02", "E1", 4.5)
    assert out["NH-02"]["E1"] == 4.5
    assert out["NH-04"]["E3"] == 25.0
    assert profile.fail_thresholds["NH-02"]["E1"] == 5.0  # unmutated


def _result(passed: bool, score: float | None) -> CompositeResult:
    return CompositeResult(
        site_id="00000000-0000-0000-0000-000000000000",  # type: ignore[arg-type]
        smr_key="x",
        composite_score=score,
        composite_score_low=None,
        composite_score_high=None,
        passed_exclusionary=passed,
        passed_avoidance=True,
        criteria_coverage=1.0,
        unscored_fraction=0.0,
        per_category_scores={},
        confidence="high",
    )


def test_diff_results_counts_add_remove_and_collects_deltas():
    base = {
        ("a", "x"): _result(True, 6.0),
        ("b", "x"): _result(True, 5.5),
        ("c", "x"): _result(False, None),
    }
    perturbed = {
        ("a", "x"): _result(True, 6.4),
        ("b", "x"): _result(False, None),
        ("c", "x"): _result(True, 5.0),
    }
    added, removed, deltas = diff_results(base, perturbed)
    assert added == 1
    assert removed == 1
    assert deltas == [pytest.approx(0.4)]


def test_percentile_clamps_to_bounds():
    assert percentile([], 0.5) is None
    assert percentile([1.0], 0.95) == 1.0
    assert percentile([1.0, 2.0, 3.0, 4.0], 0.95) == 4.0


def test_make_row_aggregates_summary_stats():
    target = TargetedThreshold(
        criterion_id="NH-02", code="E1",
        metric="nearest_fault_km", op="<", units="km",
        base_value=5.0, recommended_value=5.0,
    )
    row = make_row(
        target, pct=10.0, direction="up", perturbed_value=5.5,
        added=2, removed=1, deltas=[0.1, 0.2, 0.3], n_pairs=42,
    )
    assert row.criterion_id == "NH-02"
    assert row.n_pairs_added == 2
    assert row.mean_margin_delta == pytest.approx(0.2)
    assert row.median_margin_delta == pytest.approx(0.2)
    assert row.p95_margin_delta == pytest.approx(0.3)


def _sample_suite() -> TargetedThresholdSuiteResult:
    target = TargetedThreshold(
        criterion_id="NH-02", code="E1",
        metric="nearest_fault_km", op="<", units="km",
        base_value=5.0, recommended_value=5.0,
    )
    rows = [
        TargetedThresholdRow(
            criterion_id="NH-02", code="E1",
            metric="nearest_fault_km", op="<", units="km",
            base_value=5.0, perturbed_value=4.5,
            perturbation_pct=10.0, direction="down",
            n_pairs_added=2, n_pairs_removed=0, n_pairs_evaluated=10,
            mean_margin_delta=0.05, median_margin_delta=0.04,
            p95_margin_delta=0.10,
        ),
    ]
    return TargetedThresholdSuiteResult(
        rows=rows, targets=[target],
        pct_steps=(10.0, 25.0), n_pairs=10,
    )


def test_writer_emits_csv_and_json(tmp_path: Path):
    suite = _sample_suite()
    paths = write_targeted_threshold_artefacts(
        suite, audit_dir=tmp_path, run_id="run-1", stamp="20260427",
    )
    assert paths["csv"].exists()
    assert paths["json"].exists()
    with open(paths["csv"]) as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 1
    assert rows[0]["criterion_id"] == "NH-02"
    assert rows[0]["direction"] == "down"
    payload = json.loads(paths["json"].read_text())
    assert payload["run_id"] == "run-1"
    assert payload["pct_steps"] == [10.0, 25.0]


def test_md_renders_top_n_rows():
    suite = _sample_suite()
    md = render_targeted_threshold_md(suite, top_n=5)
    assert "NH-02" in md
    assert "down" in md
    assert "10.0" in md
