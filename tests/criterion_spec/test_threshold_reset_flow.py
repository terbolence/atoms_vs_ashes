# man_hours: 0.5
"""Criteria-wide reset flow checks for editable thresholds."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from atoms_vs_ashes.criterion_spec import compile_bundle, load_template_bundle
from atoms_vs_ashes.criterion_spec.schema import CriterionTemplate, ThresholdSpec
from atoms_vs_ashes.gui._threshold_editor_persistence import (
    fail_thresholds_without_override,
)

SPEC_DIR = Path(__file__).resolve().parents[2] / "config" / "scoring_specs"


def test_reset_prunes_internal_fail_threshold_state() -> None:
    current = {
        "NH-02": {"E1": 10.0},
        "NH-04": {"E3": 25.0},
    }

    out = fail_thresholds_without_override(current, "NH-02", "E1")

    assert out == {"NH-04": {"E3": 25.0}}
    assert current["NH-02"]["E1"] == 10.0


def test_all_editable_thresholds_override_and_reset_into_compiler() -> None:
    bundle = load_template_bundle(str(SPEC_DIR))
    targets = list(_editable_targets(bundle.by_id.values()))

    assert targets
    for cid, code, value in targets:
        overridden = compile_bundle(
            bundle,
            fail_thresholds={cid: {code: value}},
        )
        reset = compile_bundle(
            bundle,
            fail_thresholds=fail_thresholds_without_override(
                {cid: {code: value}}, cid, code,
            ),
        )

        assert any(
            rec.criterion_id == cid and rec.code == code
            for rec in overridden.overrides
        ), f"{cid}/{code} was not ingested by compiler"
        assert not any(
            rec.criterion_id == cid and rec.code == code
            for rec in reset.overrides
        ), f"{cid}/{code} survived reset into compiler"


def _editable_targets(
    templates: list[CriterionTemplate] | Any,
) -> list[tuple[str, str, Any]]:
    targets: list[tuple[str, str, Any]] = []
    for template in templates:
        for fc in template.fail_conditions:
            if fc.threshold is None:
                continue
            targets.append(
                (
                    template.criterion_id,
                    fc.code,
                    _alternate_value(fc.threshold),
                )
            )
    return targets


def _alternate_value(spec: ThresholdSpec) -> Any:
    if spec.kind != "numeric":
        return f"{spec.recommended.value}-override"
    rec = float(spec.recommended.value)
    lo = spec.bounds.min
    hi = spec.bounds.max
    step = max(abs(rec) * 0.1, 1.0)
    if hi is None or rec + step <= hi:
        return rec + step
    if lo is None or rec - step >= lo:
        return rec - step
    return rec
