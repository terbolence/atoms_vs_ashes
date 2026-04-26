# man_hours: 0.5
"""Pure-data tests for the near-miss panel (plan §9.1).

Exercises the single-criterion filter, the gap-threshold cut, and the
``by_country`` / ``by_criterion`` rollups against hand-built
``PerPairFailure`` rows.
"""

from __future__ import annotations

from atoms_vs_ashes.metrics.bundle import PerPairFailure
from atoms_vs_ashes.metrics.near_miss import build_near_miss_panel


def _failure(  # noqa: PLR0913 - test helper
    *,
    site_id: str,
    country: str = "RO",
    smr: str = "smrA",
    crit: str = "NH-02",
    code: str = "E1",
    metric: str = "nearest_fault_km",
    value: float | None = 4.5,
    threshold: float | None = 5.0,
    margin: float | None = -0.5,
    margin_norm: float | None = -0.10,
    severity: str = "minor",
    action: str = "exclude",
    site_name: str | None = None,
) -> PerPairFailure:
    return PerPairFailure(
        site_id=site_id,
        site_name=site_name,
        country_code=country,
        smr_key=smr,
        criterion_id=crit,
        code=code,
        action=action,
        metric=metric,
        value=value,
        threshold=threshold,
        margin=margin,
        margin_norm=margin_norm,
        severity=severity,
    )


def test_near_miss_includes_only_single_criterion_failures() -> None:
    rows = [
        _failure(site_id="a", crit="NH-02", margin_norm=-0.05),
        _failure(site_id="b", crit="NH-02", margin_norm=-0.04),
        _failure(site_id="b", crit="HI-01", margin_norm=-0.02, code="E5"),
    ]
    panel = build_near_miss_panel(rows, gap_threshold_pct=10.0)
    assert {r.site_id for r in panel.rows} == {"a"}


def test_near_miss_respects_gap_threshold() -> None:
    rows = [
        _failure(site_id="a", margin_norm=-0.05),
        _failure(site_id="b", margin_norm=-0.30),
    ]
    panel = build_near_miss_panel(rows, gap_threshold_pct=10.0)
    assert {r.site_id for r in panel.rows} == {"a"}


def test_near_miss_sorts_by_absolute_gap() -> None:
    rows = [
        _failure(site_id="a", margin_norm=-0.08),
        _failure(site_id="b", margin_norm=-0.02),
        _failure(site_id="c", margin_norm=0.04),
    ]
    panel = build_near_miss_panel(rows, gap_threshold_pct=10.0)
    assert [r.site_id for r in panel.rows] == ["b", "c", "a"]


def test_near_miss_aggregates_by_country_and_criterion() -> None:
    rows = [
        _failure(site_id="a", country="RO", crit="NH-02", margin_norm=-0.04),
        _failure(site_id="b", country="RO", crit="HI-01", code="E5",
                 margin_norm=-0.05),
        _failure(site_id="c", country="BG", crit="NH-02", margin_norm=-0.06),
    ]
    panel = build_near_miss_panel(rows, gap_threshold_pct=10.0)
    assert panel.by_country == [
        {"country_code": "RO", "n_near_miss": 2},
        {"country_code": "BG", "n_near_miss": 1},
    ]
    assert {(d["criterion_id"], d["code"]) for d in panel.by_criterion} == {
        ("NH-02", "E1"), ("HI-01", "E5"),
    }


def test_near_miss_would_pass_uses_measured_value() -> None:
    panel = build_near_miss_panel(
        [_failure(site_id="a", value=4.5, margin_norm=-0.05)],
        gap_threshold_pct=10.0,
    )
    assert panel.rows[0].would_pass_at_threshold == 4.5


def test_near_miss_skips_floor_rows() -> None:
    panel = build_near_miss_panel(
        [_failure(site_id="a", margin_norm=None, severity="floor")],
        gap_threshold_pct=10.0,
    )
    assert panel.rows == []
