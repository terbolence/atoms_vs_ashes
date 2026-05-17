# man_hours: 0.4
"""Preview payload carries activation metadata."""

from __future__ import annotations

from atoms_vs_ashes.criterion_spec.loader import load_template_bundle
from atoms_vs_ashes.criterion_spec.preview import build_preview
from atoms_vs_ashes.runprofile.schema import RunProfile, ScoringBlock


def test_preview_includes_inactive_ep05():
    templates = load_template_bundle("config/scoring_specs")
    profile = RunProfile.model_validate(
        {
            "run_label": "test-activation-preview",
            "spec_dir": "config/scoring_specs",
            "scoring": ScoringBlock().model_dump(),
        }
    )
    preview = build_preview(templates, profile, spec_dir="config/scoring_specs")
    ep05 = next(c for c in preview.criteria if c.criterion_id == "EP-05")
    assert ep05.active is False
    assert ep05.pending_implementation is not None
    assert "IMP-0024" in (ep05.required_improvement or "")
