# man_hours: 0.3
"""Regression checks for Site Selection Criteria role colors."""

from __future__ import annotations

from pathlib import Path

from atoms_vs_ashes.criterion_spec import load_template_bundle
from atoms_vs_ashes.criterion_spec.preview import build_preview
from atoms_vs_ashes.gui._threshold_editor_palette import criterion_importance
from atoms_vs_ashes.runprofile.schema import RunProfile

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_DIR = REPO_ROOT / "config" / "scoring_specs"


def _criteria_by_id():
    bundle = load_template_bundle(str(SPEC_DIR))
    preview = build_preview(
        bundle,
        RunProfile(run_label="palette-test"),
        spec_dir=str(SPEC_DIR),
    )
    return {criterion.criterion_id: criterion for criterion in preview.criteria}


def test_palette_uses_source_of_truth_roles() -> None:
    criteria = _criteria_by_id()

    assert criterion_importance(criteria["NH-05"]) == "ranking"
    assert criterion_importance(criteria["HI-04"]) == "avoidance"
    assert criterion_importance(criteria["NS-07"]) == "avoidance"

    for criterion in criteria.values():
        importance = criterion_importance(criterion)
        if importance == "exclusionary":
            assert criterion.is_exclusionary is True
        elif importance == "avoidance":
            assert "avoidance" in criterion.phases or any(
                fc.action == "avoidance_penalty" for fc in criterion.fail_codes
            )
        else:
            assert not criterion.is_exclusionary
            assert "avoidance" not in criterion.phases
