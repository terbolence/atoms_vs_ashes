# man_hours: 1.5
"""Scenario B regression tests for NS-03 / A14 transport access."""

from __future__ import annotations

import uuid
from pathlib import Path

from atoms_vs_ashes.connectors.osm.batch import _write_observations
from atoms_vs_ashes.connectors.osm.models import (
    HighwayResult,
    RailwayResult,
    TransportResult,
    WaterwayResult,
)
from atoms_vs_ashes.connectors.osm.parsers import assess_heavy_haul
from atoms_vs_ashes.criterion_spec import compile_bundle, load_template_bundle
from atoms_vs_ashes.scoring.bands import safe_eval

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC_DIR = REPO_ROOT / "config" / "scoring_specs"


def _a14_condition_expr() -> str:
    ns03 = compile_bundle(load_template_bundle(SPEC_DIR)).criteria["NS-03"]
    return next(fc.condition_expr for fc in ns03.fail_conditions if fc.code == "A14")


def test_unknown_transport_evidence_does_not_trigger_a14():
    capable, confidence = assess_heavy_haul(
        HighwayResult(),
        RailwayResult(),
        WaterwayResult(),
    )

    assert capable is None
    assert confidence == "low"
    assert safe_eval(_a14_condition_expr(), {"heavy_haul_capable": capable}) is False


def test_partial_negative_transport_evidence_remains_unknown():
    capable, confidence = assess_heavy_haul(
        HighwayResult(nearest_highway_km=12.0, highway_heavy_haul=False),
        RailwayResult(),
        WaterwayResult(),
    )

    assert capable is None
    assert confidence == "low"


def test_confirmed_no_path_emits_false_and_triggers_a14():
    capable, confidence = assess_heavy_haul(
        HighwayResult(nearest_highway_km=12.0, highway_heavy_haul=False),
        RailwayResult(
            nearest_rail_km=18.0,
            rail_heavy_haul=False,
            rail_siding_present=False,
        ),
        WaterwayResult(nearest_waterway_km=4.0, waterway_barge_capable=False),
    )

    assert capable is False
    assert confidence == "medium"
    assert safe_eval(_a14_condition_expr(), {"heavy_haul_capable": capable}) is True


class _FakeSession:
    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)


def _transport_result_with_capability(capable: bool | None) -> TransportResult:
    return TransportResult(
        lat=45.27,
        lon=27.96,
        highway=HighwayResult(nearest_highway_km=2.5, element_count=3),
        railway=RailwayResult(nearest_rail_km=0.8, element_count=3),
        waterway=WaterwayResult(nearest_waterway_km=4.2, element_count=2),
        heavy_haul_capable=capable,
        heavy_haul_confidence="low",
    )


def test_unknown_heavy_haul_observation_is_neutral():
    session = _FakeSession()

    _write_observations(
        session,
        site_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        result=_transport_result_with_capability(None),
        run_id="test-ns03",
    )

    heavy_haul_observations = [
        obs for obs in session.added if "Heavy-haul transport capability" in obs.observation
    ]
    assert len(heavy_haul_observations) == 1
    assert heavy_haul_observations[0].impact == "neutral"


def test_explicit_false_heavy_haul_observation_is_negative():
    session = _FakeSession()

    _write_observations(
        session,
        site_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        result=_transport_result_with_capability(False),
        run_id="test-ns03",
    )

    heavy_haul_observations = [
        obs for obs in session.added if "explicitly negative" in obs.observation
    ]
    assert len(heavy_haul_observations) == 1
    assert heavy_haul_observations[0].impact == "negative"
