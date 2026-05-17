# man_hours: 1.5
"""Compiler parity smoke tests for Bucket C partial-data criteria."""

from __future__ import annotations

from pathlib import Path

import pytest

from atoms_vs_ashes.criterion_spec import compile_bundle, load_template_bundle
from atoms_vs_ashes.scoring.rubric import load_rubric_bundle

REPO_ROOT = Path(__file__).resolve().parents[2]
RUBRIC_DIR = REPO_ROOT / "config" / "scoring_rubrics"
SPEC_DIR = REPO_ROOT / "config" / "scoring_specs"

CRITERIA = ("EP-03", "HI-02", "HI-03", "HI-04", "NH-09", "NH-11", "RI-03", "RI-05")

@pytest.fixture(scope="module")
def bundle():
    return load_rubric_bundle(str(RUBRIC_DIR))


@pytest.fixture(scope="module")
def compiled():
    return compile_bundle(load_template_bundle(str(SPEC_DIR))).criteria


@pytest.mark.parametrize("criterion_id", CRITERIA)
def test_partial_data_spec_and_rubric_align(bundle, compiled, criterion_id: str) -> None:
    rubric = bundle[criterion_id]

    assert compiled[criterion_id].criterion_id == rubric.criterion_id
    assert compiled[criterion_id].primary_metric == rubric.primary_metric
    assert compiled[criterion_id].db_fields == rubric.db_fields
    if criterion_id not in {"HI-02", "HI-03", "HI-04"}:
        assert compiled[criterion_id].bands == rubric.bands
    assert compiled[criterion_id].sub_scores == rubric.sub_scores
    assert compiled[criterion_id].aggregation == rubric.aggregation
