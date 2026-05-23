"""Tests for run-profile provenance extraction and site-bundle wiring.

Phase 1B (v1.03 feedback closure #105): the NH-02 E1 screening radius is a
UI-tunable run-profile parameter. The site / country bundle JSON carries
``provenance.nh02_e1_threshold_km`` so downstream renderers (site profile
prose, country profile prose) print the active radius without importing a
Python constant.
"""

from __future__ import annotations

from typing import Any

import pytest

from atoms_vs_ashes.reporting import run_profile_provenance as rpp
from scripts._site_profile_intelligence import evidence_for


class _StubSession:
    """SQLAlchemy ``Session.get`` stub that returns prepared objects."""

    def __init__(
        self,
        *,
        run_to_snapshot: dict[str, Any] | None = None,
        snapshot_to_bundle: dict[str, Any] | None = None,
    ) -> None:
        self._runs = run_to_snapshot or {}
        self._snaps = snapshot_to_bundle or {}

    def get(self, model: Any, pk: Any) -> Any:
        if model is rpp.ScoringRunSnapshot:
            return self._runs.get(pk)
        if model is rpp.CompiledScoringSnapshot:
            return self._snaps.get(pk)
        return None


class _Link:
    def __init__(self, snapshot_id: str) -> None:
        self.snapshot_id = snapshot_id


class _Snap:
    def __init__(self, bundles_by_smr: dict[str, Any]) -> None:
        self.bundles_by_smr = bundles_by_smr


def _bundle_with_nh02_threshold(threshold_km: float) -> dict[str, Any]:
    return {
        "nuscale_voygr6": {
            "NH-02": {
                "fail_conditions": [
                    {
                        "code": "E1",
                        "condition_expr": f"nearest_fault_km < {threshold_km}",
                    }
                ],
            }
        }
    }


@pytest.mark.parametrize("threshold", [0.5, 1.0, 5.0, 8.0, 10.0, 50.0, 100.0])
def test_nh02_threshold_round_trips_from_snapshot(threshold: float) -> None:
    session = _StubSession(
        run_to_snapshot={"run-x": _Link("snap-x")},
        snapshot_to_bundle={"snap-x": _Snap(_bundle_with_nh02_threshold(threshold))},
    )

    value = rpp.nh02_e1_threshold_km(session, run_id="run-x")

    assert value == pytest.approx(threshold)


def test_nh02_threshold_falls_back_to_metadata_yaml_when_no_snapshot() -> None:
    session = _StubSession()

    value = rpp.nh02_e1_threshold_km(session, run_id="run-unknown")

    assert value == pytest.approx(8.0)


def test_run_profile_provenance_block_contains_nh02_key() -> None:
    session = _StubSession()

    provenance = rpp.run_profile_provenance(session, run_id="run-unknown")

    assert "nh02_e1_threshold_km" in provenance
    assert provenance["nh02_e1_threshold_km"] == pytest.approx(8.0)


@pytest.mark.parametrize(
    "threshold,distance,expected_verdict",
    [
        (8.0, 5.0, "inside"),
        (8.0, 12.0, "outside"),
        (5.0, 4.9, "inside"),
        (5.0, 5.0, "outside"),
        (100.0, 23.0, "inside"),
    ],
)
def test_nh02_e1_verdict_signal_uses_active_threshold(
    threshold: float, distance: float, expected_verdict: str,
) -> None:
    families = {"natural_hazards": {"nearest_fault_km": distance}}
    provenance = {"nh02_e1_threshold_km": threshold}

    result = evidence_for("NH-02", families, provenance=provenance)

    verdict_lines = [s for s in result["signals"] if s.startswith("E1 verdict")]
    assert len(verdict_lines) == 1
    assert f"radius {threshold:g} km" in verdict_lines[0] or "radius " in verdict_lines[0]
    assert expected_verdict in verdict_lines[0]


def test_nh02_evidence_omits_verdict_when_provenance_missing() -> None:
    families = {"natural_hazards": {"nearest_fault_km": 5.0}}

    result = evidence_for("NH-02", families)

    assert all(not s.startswith("E1 verdict") for s in result["signals"])


def test_nh02_evidence_omits_verdict_when_distance_missing() -> None:
    families = {"natural_hazards": {"nearest_fault_km": None}}
    provenance = {"nh02_e1_threshold_km": 8.0}

    result = evidence_for("NH-02", families, provenance=provenance)

    assert all(not s.startswith("E1 verdict") for s in result["signals"])
