# man_hours: 0.5
"""Regression coverage for the NS-07 Option A tier source."""

from __future__ import annotations

from pathlib import Path

import pytest

from atoms_vs_ashes.criterion_spec import compile_bundle, load_template_bundle
from atoms_vs_ashes.db.models import SiteInfrastructureV2
from atoms_vs_ashes.llm.persist import _FIELD_MAP
from atoms_vs_ashes.llm.schemas import NS07EnvImpact
from atoms_vs_ashes.scoring.bands import evaluate_criterion_value


SPEC_DIR = Path(__file__).resolve().parents[2] / "config" / "scoring_specs"


@pytest.fixture(scope="module")
def ns07():
    bundle = load_template_bundle(str(SPEC_DIR))
    return compile_bundle(bundle).criteria["NS-07"]


def test_ns07_spec_reads_persisted_env_impact_tier(ns07) -> None:
    assert ns07.primary_metric == "env_impact_tier"
    assert ns07.db_fields.api == ["site_infrastructure_v2.env_impact_tier"]
    assert not ns07.fail_conditions


def test_ns07_bands_score_from_env_impact_tier(ns07) -> None:
    assert evaluate_criterion_value(ns07, {"env_impact_tier": "industrial"}).score == 9.5
    assert evaluate_criterion_value(ns07, {"env_impact_tier": "typical"}).score == 5.5
    assert evaluate_criterion_value(ns07, {"env_impact_tier": "showstopper_risk"}).score == 1.5


def test_ns07_llm_schema_and_persist_mapping_expose_tier() -> None:
    assert "env_impact_tier" in SiteInfrastructureV2.__table__.columns
    assert _FIELD_MAP["NS-07"]["env_impact_tier"] == "env_impact_tier"

    schema = NS07EnvImpact(
        score=3,
        confidence="medium",
        justification="Significant non-radiological permitting issues.",
        data_quality="medium",
        cited_sources=[],
        env_impact_tier="significant",
        env_impact_notes="Thermal and visual-impact mitigations likely required.",
    )
    assert schema.env_impact_tier == "significant"

    with pytest.raises(ValueError):
        NS07EnvImpact(
            score=3,
            confidence="medium",
            justification="Invalid tier.",
            data_quality="medium",
            cited_sources=[],
            env_impact_tier="free_text_note",
        )
