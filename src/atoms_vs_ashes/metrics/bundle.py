# man_hours: 1.5
"""Run-level :class:`MetricsBundle` dataclass shape.

Mirrors plan §9 verbatim: a single JSON-serialisable payload that backs
the audit MD, the future ``GET /metrics/{run_id}`` endpoint, and the
GUI dashboard. Each panel is a sibling dataclass so individual todos
(``per-country-margins``, ``near-miss-panel``, ``qualification-mode``)
can tighten their fields without rewriting the bundle.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class SummaryPanel:
    """Top-line counts for the dashboard banner."""

    total_pairs: int
    survived: int
    hard_only: int
    floor_only: int
    both: int
    n_distinct_sites: int
    n_distinct_smrs: int
    qualification_mode: str = "normal"


@dataclass
class CriterionStatPanel:
    """Per-criterion fail/floor counts for the bar chart."""

    criterion_id: str
    criterion_name: str
    hard_pairs: int
    floor_pairs: int
    union_pairs: int
    intersection_pairs: int


@dataclass
class CountryStatPanel:
    """Per-country survival snapshot — the dashboard's headline row."""

    country_code: str
    n_sites: int
    n_pairs: int
    survived: int
    hard_only: int
    floor_only: int
    both: int
    n_sites_with_survivor: int
    mean_composite: float | None = None
    p10_composite: float | None = None
    p90_composite: float | None = None


@dataclass
class SmrStatPanel:
    """Per-SMR survivor + failure breakdown."""

    smr_key: str
    n_pairs: int
    survived: int
    hard_only: int
    floor_only: int
    both: int


@dataclass
class PerPairFailure:
    """Long-format failure row for the country drill-down view."""

    site_id: str
    site_name: str | None
    country_code: str
    smr_key: str
    criterion_id: str
    code: str | None
    action: str | None
    metric: str | None
    value: Any
    threshold: Any
    margin: float | None
    margin_norm: float | None
    severity: str | None


@dataclass
class TopNRow:
    """One row in the per-country shortlist."""

    country_code: str
    smr_key: str
    rank: int
    site_id: str
    site_name: str | None
    composite_score: float | None
    composite_score_low: float | None
    composite_score_high: float | None
    family_scores: dict[str, float] = field(default_factory=dict)
    qualification_mode: str = "normal"


@dataclass
class PerCriterionMargin:
    """One eliminator row inside a country's drill-down panel."""

    criterion_id: str
    code: str | None
    metric: str | None
    units: str | None
    n_eliminated: int
    median_gap: float | None
    p90_gap: float | None
    max_gap: float | None
    examples: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class PerCountryMarginPanel:
    """Country envelope of the eliminator rows."""

    country_code: str
    n_sites_total: int
    n_sites_passed: int
    criteria_eliminating_sites: list[PerCriterionMargin] = field(default_factory=list)


@dataclass
class NearMissRow:
    """One pair that failed by a small margin on a single criterion."""

    site_id: str
    site_name: str | None
    country_code: str
    smr_key: str
    criterion_id: str
    code: str | None
    metric: str | None
    value: Any
    threshold: Any
    gap: float | None
    gap_norm: float | None
    would_pass_at_threshold: float | None = None
    composite_if_passed: float | None = None


@dataclass
class NearMissPanel:
    """First-class near-miss view (plan §9.1)."""

    gap_threshold_pct: float = 10.0
    rows: list[NearMissRow] = field(default_factory=list)
    by_country: list[dict[str, Any]] = field(default_factory=list)
    by_criterion: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SensitivityPanel:
    """Four-panel sensitivity blob; populated when sensitivity has run."""

    mc: dict[str, Any] | None = None
    threshold_targeted: list[dict[str, Any]] = field(default_factory=list)
    threshold_global_stress: list[dict[str, Any]] | None = None
    oat_top5: list[dict[str, Any]] = field(default_factory=list)
    weights: dict[str, Any] | None = None
    country_balance: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class MetricsBundle:
    """Top-level dashboard payload (plan §9)."""

    run_id: str
    summary: SummaryPanel
    per_criterion: list[CriterionStatPanel] = field(default_factory=list)
    per_country: list[CountryStatPanel] = field(default_factory=list)
    per_smr: list[SmrStatPanel] = field(default_factory=list)
    per_pair_failures: list[PerPairFailure] = field(default_factory=list)
    top_n_per_country: list[TopNRow] = field(default_factory=list)
    per_country_margins: list[PerCountryMarginPanel] = field(default_factory=list)
    near_miss: NearMissPanel = field(default_factory=NearMissPanel)
    sensitivity: SensitivityPanel = field(default_factory=SensitivityPanel)
    provenance: dict[str, Any] = field(default_factory=dict)
    multi_failure_histogram: dict[int, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


__all__ = [
    "CountryStatPanel",
    "CriterionStatPanel",
    "MetricsBundle",
    "NearMissPanel",
    "NearMissRow",
    "PerCountryMarginPanel",
    "PerCriterionMargin",
    "PerPairFailure",
    "SensitivityPanel",
    "SmrStatPanel",
    "SummaryPanel",
    "TopNRow",
]
