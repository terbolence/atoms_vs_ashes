# man_hours: 1.0
"""HI-02/A7 Option A compiled-spec regression tests."""

from __future__ import annotations

import uuid
from pathlib import Path

from atoms_vs_ashes.criterion_spec import compile_bundle, load_template_bundle
from atoms_vs_ashes.scoring.avoidance import evaluate_avoidance_for_site
from atoms_vs_ashes.scoring.bands import evaluate_criterion_value
from atoms_vs_ashes.scoring.exclusionary import evaluate_fail_conditions
from atoms_vs_ashes.scoring.rubric import load_rubric_bundle

SPEC_DIR = Path(__file__).resolve().parents[2] / "config" / "scoring_specs"
RUBRIC_DIR = Path(__file__).resolve().parents[2] / "config" / "scoring_rubrics"


def test_hi02_recipe_preserves_completed_search_sentinel() -> None:
    bundle = load_template_bundle(str(SPEC_DIR))
    hi02 = compile_bundle(bundle).criteria["HI-02"]

    top = next(b for b in hi02.bands if b.score_range == (9.0, 10.0))
    assert top.condition_expr == (
        "(nearest_seveso_km is null and hi02_search_completed == true) "
        "or nearest_seveso_km >= 25.0"
    )

    completed = evaluate_criterion_value(
        hi02,
        {"nearest_seveso_km": None, "hi02_search_completed": True},
        quality="medium",
    )
    missing = evaluate_criterion_value(
        hi02,
        {"nearest_seveso_km": None, "hi02_search_completed": False},
        quality="medium",
    )

    assert completed.matched_band is not None
    assert completed.matched_band.score_range == (9.0, 10.0)
    assert missing.matched_band is None
    assert missing.notes == ["unscored"]


def test_hi02_a7_completed_search_null_passes_avoidance() -> None:
    bundle = load_template_bundle(str(SPEC_DIR))
    hi02 = compile_bundle(bundle).criteria["HI-02"]

    assert _single_avoidance_verdict(
        hi02, {"nearest_seveso_km": None, "hi02_search_completed": True}
    ) == "pass"
    assert _single_avoidance_verdict(
        hi02, {"nearest_seveso_km": None, "hi02_search_completed": False}
    ) == "inconclusive"
    assert _single_avoidance_verdict(
        hi02, {"nearest_seveso_km": 4.9, "hi02_search_completed": True}
    ) == "caution"
    assert _single_avoidance_verdict(
        hi02, {"nearest_seveso_km": 5.0, "hi02_search_completed": True}
    ) == "pass"


def test_hi02_legacy_rubric_a7_completed_search_null_passes() -> None:
    hi02 = load_rubric_bundle(RUBRIC_DIR)["HI-02"]

    completed = evaluate_fail_conditions(
        hi02,
        {"nearest_seveso_km": None, "hi02_search_completed": True},
        action="avoidance_penalty",
    )[0]
    missing = evaluate_fail_conditions(
        hi02,
        {"nearest_seveso_km": None, "hi02_search_completed": False},
        action="avoidance_penalty",
    )[0]
    inside = evaluate_fail_conditions(
        hi02,
        {"nearest_seveso_km": 4.9, "hi02_search_completed": True},
        action="avoidance_penalty",
    )[0]

    assert completed.verdict == "pass"
    assert missing.verdict == "inconclusive"
    assert inside.verdict == "fail"


def _single_avoidance_verdict(criterion, context: dict[str, object]) -> str:
    rows = evaluate_avoidance_for_site(
        criterion,
        context,
        site_id=uuid.uuid4(),
        smr_key="nuscale_voygr6",
        run_id="hi02-a7-unit",
        confidence="medium",
        data_sources=["unit"],
    )
    assert len(rows) == 1
    return str(rows[0].verdict)
