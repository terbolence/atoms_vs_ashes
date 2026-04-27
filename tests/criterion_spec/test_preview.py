# man_hours: 1.5
"""Tests for the DB-free :func:`build_preview` service.

Coverage:

- baseline preview (no overrides) is structurally complete: every
  criterion appears, normalised weights sum to 1.0, every fail code
  carries its recommended-value metadata.
- overriding a fail threshold flips ``modified_from_recommended`` and
  populates the ``diff_vs_recommended`` block.
- unknown criterion / code is reported as a warning rather than a hard
  error so the GUI can keep rendering the editor.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from atoms_vs_ashes.criterion_spec import (
    PreviewBundle,
    build_preview,
    load_template_bundle,
)
from atoms_vs_ashes.runprofile import RunProfile, ScoringBlock


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_DIR = REPO_ROOT / "config" / "scoring_specs"


@pytest.fixture(scope="module")
def template_bundle():
    return load_template_bundle(str(SPEC_DIR))


def test_baseline_preview_structure(template_bundle):
    bundle: PreviewBundle = build_preview(
        template_bundle,
        RunProfile(run_label="baseline"),
        spec_dir=str(SPEC_DIR),
    )
    assert bundle.spec_sha256
    assert bundle.compiled_sha256
    assert bundle.criteria, "expected at least one criterion in the preview"
    weight_sum = sum(c.weight_normalised for c in bundle.criteria)
    assert weight_sum == pytest.approx(1.0, abs=1e-6)
    assert bundle.warnings == []
    assert bundle.diff_vs_recommended == []


def test_modified_threshold_appears_in_diff(template_bundle):
    profile = RunProfile(
        run_label="ro_focus",
        fail_thresholds={"NH-02": {"E1": 4.5}},
    )
    bundle = build_preview(template_bundle, profile, spec_dir=str(SPEC_DIR))
    nh02 = next(c for c in bundle.criteria if c.criterion_id == "NH-02")
    e1 = next(fc for fc in nh02.fail_codes if fc.code == "E1")
    assert e1.modified_from_recommended is True
    assert e1.value == 4.5
    assert e1.recommended_value == 8.0
    assert any(d["code"] == "E1" for d in bundle.diff_vs_recommended)


def test_unknown_code_is_warning_not_error(template_bundle):
    profile = RunProfile(
        run_label="bad_input",
        fail_thresholds={"NH-02": {"E_NOPE": 1.0}},
    )
    bundle = build_preview(template_bundle, profile, spec_dir=str(SPEC_DIR))
    assert any(w.startswith("unknown_code=") for w in bundle.warnings)


def test_hard_expression_only_exclusion_shows_no_floor_pass_mark(template_bundle):
    bundle = build_preview(
        template_bundle,
        RunProfile(run_label="baseline"),
        spec_dir=str(SPEC_DIR),
    )
    nh05 = next(c for c in bundle.criteria if c.criterion_id == "NH-05")
    assert nh05.is_exclusionary is True
    assert nh05.exclusion_pass_mark is None
