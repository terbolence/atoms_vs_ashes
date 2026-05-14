# man_hours: 0.7
"""Preview metadata needed by universal criterion info popovers."""

from __future__ import annotations

from pathlib import Path

import pytest

from atoms_vs_ashes.criterion_spec import build_preview, load_template_bundle
from atoms_vs_ashes.gui._criterion_info import criterion_infobox, criterion_info_markdown
from atoms_vs_ashes.runprofile import RunProfile

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_DIR = REPO_ROOT / "config" / "scoring_specs"


@pytest.fixture(scope="module")
def preview_bundle():
    bundle = load_template_bundle(str(SPEC_DIR))
    return build_preview(
        bundle,
        RunProfile(run_label="criterion-info-smoke"),
        spec_dir=str(SPEC_DIR),
    )


def _criterion(preview_bundle, criterion_id: str):
    return next(c for c in preview_bundle.criteria if c.criterion_id == criterion_id)


def _fail_code(criterion, code: str):
    return next(fc for fc in criterion.fail_codes if fc.code == code)


def test_descriptor_and_pass_mark_exposed_for_noneditable_nh03(preview_bundle):
    nh03 = _criterion(preview_bundle, "NH-03")
    e2 = _fail_code(nh03, "E2")
    assert e2.user_editable is False
    assert e2.descriptor == "Unacceptable liquefaction with no engineering remedy."
    assert e2.pass_mark == 5.0


def test_descriptor_and_pass_mark_exposed_for_nh07(preview_bundle):
    nh07 = _criterion(preview_bundle, "NH-07")
    e4 = _fail_code(nh07, "E4")
    assert e4.descriptor == "< 50 km Holocene volcano or in mapped hazard zone."
    assert e4.pass_mark == 5.0


def test_criterion_weight_sources_exposed(preview_bundle):
    nh02 = _criterion(preview_bundle, "NH-02")
    assert nh02.weight_factors["epri"] == 5
    assert "SSG-35" in nh02.weight_basis_source["epri"]


def test_ep01_infobox_keeps_fail_value_template(preview_bundle):
    ep01 = _criterion(preview_bundle, "EP-01")
    e8 = _fail_code(ep01, "E8")
    text = criterion_infobox(ep01, e8)
    assert "**Fail value:** `30` points" in text
    assert "**Expression:** `ep01_composite_score < 30" in text
    assert "IAEA GSR Part 7" in text
    assert "Bounds: [10.0, 60.0]" in text


def test_noneditable_avoidance_code_has_infobox(preview_bundle):
    ri05 = _criterion(preview_bundle, "RI-05")
    a12 = _fail_code(ri05, "A12")
    assert a12.user_editable is False
    text = criterion_infobox(ri05, a12)
    assert "**Action:** `avoidance_penalty`" in text
    assert "Project thresholds: 25k/>=8 km" in text
    assert "User-tunable: `no`" in text


def test_complete_criterion_info_includes_epri_weight(preview_bundle):
    nh03 = _criterion(preview_bundle, "NH-03")
    text = criterion_info_markdown(nh03)
    assert "**EPRI weight:** `4`" in text
    assert "NS-G-3.6" in text
    assert "User-tunable: `no`" in text
