"""Sync test for ``report/methodology/exclusionary_floors.md``.

Re-runs the generator against ``config/scoring_rubrics/*.yaml`` and
asserts the on-disk doc matches byte-for-byte. Failure means the YAMLs
were edited without re-running ``python -m scripts.generate_exclusionary_floors``.

Also asserts every ``action: exclude`` fail condition declares a
``pass_mark`` unless it has an explicit hard-expression-only waiver.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from atoms_vs_ashes.scoring.rubric import load_rubric_bundle
from scripts.generate_exclusionary_floors import (
    DEFAULT_OUT_PATH,
    DEFAULT_RUBRIC_DIR,
    render_document,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
# NH-10/project_wind_envelope was previously waived as an exclude-without-floor;
# post-2026-05-16 it is a `review_flag` (not an `exclude`), so the waiver no
# longer applies — the test below only inspects `action == "exclude"` rows.
NO_FLOOR_WAIVERS = {
    "EP-01/E8",
    "NS-08/E7",
}


def test_exclusionary_floors_doc_matches_generator() -> None:
    rubric_dir = REPO_ROOT / DEFAULT_RUBRIC_DIR
    out_path = REPO_ROOT / DEFAULT_OUT_PATH

    bundle = load_rubric_bundle(rubric_dir)
    expected = render_document(bundle)

    assert out_path.exists(), (
        f"{out_path} not found. Run `python -m scripts.generate_exclusionary_floors`."
    )
    actual = out_path.read_text()
    if actual != expected:
        pytest.fail(
            f"{out_path} is out of sync with {rubric_dir}. "
            "Re-run `python -m scripts.generate_exclusionary_floors` and commit."
        )


def test_every_exclude_condition_declares_pass_mark() -> None:
    rubric_dir = REPO_ROOT / DEFAULT_RUBRIC_DIR
    bundle = load_rubric_bundle(rubric_dir)
    missing: list[str] = []
    for crit in bundle.values():
        for fc in crit.fail_conditions:
            key = f"{crit.criterion_id}/{fc.code}"
            if (
                fc.action == "exclude"
                and fc.pass_mark is None
                and key not in NO_FLOOR_WAIVERS
            ):
                missing.append(f"{crit.criterion_id}/{fc.code}")
    assert not missing, (
        "Every action: exclude condition must declare pass_mark "
        f"(missing on: {missing})."
    )
