# man_hours: 1.5
"""Compiler parity test: spec_dir + empty fail_thresholds == legacy rubric.

This is the migration safety net for the two-layer
:mod:`atoms_vs_ashes.criterion_spec` model. Any drift between the
verbatim rubric YAMLs in ``config/scoring_rubrics/`` and the compiled
bundle from ``config/scoring_specs/`` (with no overrides) fails this
test, preventing silent rubric divergence.

See ``.cursor/plans/scoring_control_gui_872d4eb7.plan.md`` Phase A
acceptance criteria.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atoms_vs_ashes.criterion_spec import compile_bundle, load_template_bundle
from atoms_vs_ashes.scoring.rubric import Criterion, load_rubric_bundle


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_DIR = REPO_ROOT / "config" / "scoring_specs"
RUBRIC_DIR = REPO_ROOT / "config" / "scoring_rubrics"


def _canon(c: Criterion) -> str:
    return json.dumps(c.model_dump(mode="json"), sort_keys=True)


@pytest.fixture(scope="module")
def legacy() -> dict[str, Criterion]:
    return load_rubric_bundle(str(RUBRIC_DIR))


@pytest.fixture(scope="module")
def compiled():
    bundle = load_template_bundle(str(SPEC_DIR))
    return compile_bundle(bundle).criteria


def test_same_criterion_ids(legacy, compiled):
    assert set(legacy) == set(compiled)


def test_per_criterion_byte_equivalent(legacy, compiled):
    diffs: list[str] = []
    for cid in sorted(legacy):
        if _canon(legacy[cid]) != _canon(compiled[cid]):
            diffs.append(cid)
    assert not diffs, f"Compiled criteria drifted from legacy: {diffs}"


def test_compiled_hash_is_stable():
    bundle = load_template_bundle(str(SPEC_DIR))
    a = compile_bundle(bundle).sha256
    b = compile_bundle(bundle).sha256
    assert a == b


def test_override_regenerates_condition_expr():
    bundle = load_template_bundle(str(SPEC_DIR))
    out = compile_bundle(bundle, fail_thresholds={"NH-02": {"E1": 8.0}})
    e1 = next(
        fc for fc in out.criteria["NH-02"].fail_conditions if fc.code == "E1"
    )
    assert e1.condition_expr == "nearest_fault_km < 8"
    rec = next(o for o in out.overrides if o.code == "E1")
    assert rec.user_value == 8.0
    assert rec.recommended_value == 5.0
    assert rec.deviation_pct == pytest.approx(60.0)


def test_out_of_bounds_rejected_without_expert_flag():
    bundle = load_template_bundle(str(SPEC_DIR))
    with pytest.raises(ValueError, match="outside bounds"):
        compile_bundle(bundle, fail_thresholds={"NH-02": {"E1": 100.0}})


def test_expert_override_accepts_out_of_bounds():
    bundle = load_template_bundle(str(SPEC_DIR))
    out = compile_bundle(
        bundle,
        fail_thresholds={"NH-02": {"E1": 100.0}},
        expert_override=True,
    )
    rec = next(o for o in out.overrides if o.code == "E1")
    assert rec.out_of_bounds is True


def test_unknown_code_rejected():
    bundle = load_template_bundle(str(SPEC_DIR))
    with pytest.raises(ValueError, match="Unknown code"):
        compile_bundle(bundle, fail_thresholds={"NH-02": {"E99": 5}})
