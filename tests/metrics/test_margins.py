# man_hours: 1.0
"""Tests for failure-margin helpers and the per-country aggregator.

The orchestrator path (`build_metrics_bundle_from_session`) is covered
by integration tests against the snapshot DB; here we only validate
the pure maths and the dataclass plumbing so they can be tightened
without spinning up Postgres.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from types import SimpleNamespace

from atoms_vs_ashes.metrics._margin_helpers import (
    base_code,
    coerce_numeric,
    is_floor_code,
    normalise_gap,
    parse_measured_json,
    severity_for,
    signed_gap,
    top_examples,
)
from atoms_vs_ashes.metrics.bundle import PerPairFailure
from atoms_vs_ashes.metrics.margins import (
    aggregate_per_country_margins,
    collect_per_pair_failures,
)


def test_signed_gap_uses_value_minus_threshold() -> None:
    assert signed_gap(value=3.6, threshold=5.0, op="<") == -1.4
    assert signed_gap(value=12.0, threshold=10.0, op=">") == 2.0
    assert signed_gap(value=5.0, threshold=5.0, op="==") == 0.0


def test_severity_uses_magnitude() -> None:
    assert severity_for(0.6) == "critical"
    assert severity_for(-0.6) == "critical"
    assert severity_for(0.1) == "minor"
    assert severity_for(0.0) == "trivial"
    assert severity_for(None) is None


def test_normalise_gap_clamps_zero_threshold() -> None:
    assert normalise_gap(0.5, 0.0) >= 1e8


def test_floor_code_helpers() -> None:
    assert is_floor_code("E1:floor")
    assert not is_floor_code("E1")
    assert base_code("E1:floor") == "E1"
    assert base_code(None) is None


def test_parse_measured_json_handles_garbage() -> None:
    assert parse_measured_json('{"x": 1.5}', "x") == 1.5
    assert parse_measured_json("not json", "x") is None
    assert parse_measured_json(None, "x") is None
    assert parse_measured_json('{"x": 1}', None) is None


def test_coerce_numeric_rejects_bools() -> None:
    assert coerce_numeric(True) is None
    assert coerce_numeric("4.2") == 4.2
    assert coerce_numeric("abc") is None


def test_top_examples_keeps_largest_magnitude() -> None:
    rows = [
        {"site_id": "a", "gap": 0.1},
        {"site_id": "b", "gap": -1.4},
        {"site_id": "c", "gap": 0.3},
        {"site_id": "d", "gap": None},
    ]
    picked = top_examples(rows, n=2)
    ids = [r["site_id"] for r in picked]
    assert ids == ["b", "c"]


@dataclass
class FakeRecommended:
    value: float = 5.0


@dataclass
class FakeThreshold:
    metric: str
    op: str
    default_value: float
    units: str | None = None
    label: str = ""
    kind: str = "numeric"
    recommended: FakeRecommended = field(default_factory=FakeRecommended)
    bounds: object | None = None


@dataclass
class FakeTemplate:
    criterion_id: str
    by_code: dict[str, FakeThreshold]

    def threshold_for_code(self, code: str) -> FakeThreshold | None:
        return self.by_code.get(code)


@dataclass
class FakeBundle:
    by_id: dict[str, FakeTemplate]


def _verdict(
    *, site_id, smr_key, criterion_id, code, value, threshold_str="ne",
    metric="nearest_fault_km", phase="exclusionary", verdict="fail",
):
    return SimpleNamespace(
        site_id=site_id,
        smr_key=smr_key,
        criterion_id=criterion_id,
        prompt_key=code,
        phase=phase,
        verdict=verdict,
        measured_value=json.dumps({metric: value}),
        threshold=threshold_str,
    )


def test_collect_per_pair_failures_computes_signed_margin() -> None:
    s1 = uuid.UUID("00000000-0000-0000-0000-000000000001")
    s2 = uuid.UUID("00000000-0000-0000-0000-000000000002")
    bundle = FakeBundle(
        by_id={
            "NH-02": FakeTemplate(
                criterion_id="NH-02",
                by_code={
                    "E1": FakeThreshold(
                        metric="nearest_fault_km", op="<", default_value=5.0
                    )
                },
            ),
        }
    )
    verdicts = {
        (s1, "smrA"): [
            _verdict(site_id=s1, smr_key="smrA", criterion_id="NH-02",
                     code="E1", value=3.6),
        ],
        (s2, "smrA"): [
            _verdict(site_id=s2, smr_key="smrA", criterion_id="NH-02",
                     code="E1:floor", value=4.0),
        ],
    }
    failures = collect_per_pair_failures(
        verdicts,
        template_bundle=bundle,
        country_by_site={s1: "RO", s2: "RO"},
        site_names={str(s1): "Cernavoda", str(s2): "Mintia"},
    )
    assert len(failures) == 2
    by_site = {f.site_id: f for f in failures}
    s1_row = by_site[str(s1)]
    assert s1_row.criterion_id == "NH-02"
    assert s1_row.code == "E1"
    assert s1_row.metric == "nearest_fault_km"
    assert s1_row.value == 3.6
    assert s1_row.threshold == 5.0
    assert s1_row.margin == -1.4
    assert s1_row.severity == "severe"

    floor_row = by_site[str(s2)]
    assert floor_row.code == "E1"  # base
    assert floor_row.severity == "floor"
    assert floor_row.margin is None


def test_aggregate_per_country_margins_orders_by_eliminations() -> None:
    failures = [
        PerPairFailure(
            site_id=f"site{i}", site_name=None, country_code="RO",
            smr_key="smrA", criterion_id="NH-02", code="E1",
            metric="nearest_fault_km", value=v, threshold=5.0,
            margin=v - 5.0, margin_norm=(v - 5.0) / 5.0,
            severity="severe", action="exclude",
        )
        for i, v in enumerate([3.6, 4.0, 4.4])
    ] + [
        PerPairFailure(
            site_id="x", site_name=None, country_code="RO",
            smr_key="smrA", criterion_id="HI-01", code="E5",
            metric="airport_dist_km", value=2.0, threshold=8.0,
            margin=-6.0, margin_norm=-0.75,
            severity="critical", action="exclude",
        )
    ]
    panels = aggregate_per_country_margins(
        failures,
        country_pair_counts={"RO": {"n_total": 10, "n_passed": 6}},
    )
    assert len(panels) == 1
    ro = panels[0]
    assert ro.country_code == "RO"
    assert ro.n_sites_total == 10
    assert ro.n_sites_passed == 6
    assert [c.criterion_id for c in ro.criteria_eliminating_sites] == [
        "NH-02", "HI-01"
    ]
    nh02 = ro.criteria_eliminating_sites[0]
    assert nh02.n_eliminated == 3
    assert nh02.median_gap == -1.0  # nearest-rank: -1.0 of [-1.4,-1.0,-0.6]
    assert len(nh02.examples) == 3
