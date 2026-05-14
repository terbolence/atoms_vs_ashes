# man_hours: 0.5
"""RI-04 remains ranking-only after gate removal."""

from __future__ import annotations

import uuid
from pathlib import Path

from atoms_vs_ashes.analysis.epz_population import evaluate_ri04
from atoms_vs_ashes.connectors.population import RingPopulation
from atoms_vs_ashes.scoring.avoidance import evaluate_avoidance_for_site
from atoms_vs_ashes.scoring.exclusionary import evaluate_exclusionary_for_site
from atoms_vs_ashes.scoring.rubric import load_rubric_bundle

REPO_ROOT = Path(__file__).resolve().parents[2]
RUBRIC_DIR = REPO_ROOT / "config" / "scoring_rubrics"


def test_ri04_extreme_population_no_longer_excludes() -> None:
    criterion = load_rubric_bundle(RUBRIC_DIR)["RI-04"]
    context = {
        "pop_density_5km": 2000,
        "pop_density_16km": 1500,
        "pop_density_25km": 900,
        "pop_density_80km": 400,
    }
    exclusionary = evaluate_exclusionary_for_site(
        criterion,
        context,
        site_id=uuid.uuid4(),
        smr_key="nuscale_voygr6",
        run_id="ri04-unit",
        confidence="high",
        data_sources=["unit"],
    )
    avoidance = evaluate_avoidance_for_site(
        criterion,
        context,
        site_id=uuid.uuid4(),
        smr_key="nuscale_voygr6",
        run_id="ri04-unit",
        confidence="high",
        data_sources=["unit"],
    )
    assert exclusionary == []
    assert avoidance == []


def test_ri04_specs_no_longer_define_fail_conditions() -> None:
    specs = load_rubric_bundle(REPO_ROOT / "config" / "scoring_specs")
    criterion = specs["RI-04"]
    assert criterion.fail_conditions == []
    assert criterion.phases == ["ranking"]


def test_legacy_epz_population_high_density_is_not_fail() -> None:
    rings = [
        RingPopulation(
            inner_km=0,
            outer_km=5,
            population=160_000,
            area_km2=78.5,
            density_per_km2=2038.0,
            place_count=3,
        )
    ]

    verdict, payload, justification = evaluate_ri04(rings, density_threshold=1000)

    assert verdict == "pass"
    assert payload["exceeds_threshold"] is True
    assert "ranking/review only" in justification
