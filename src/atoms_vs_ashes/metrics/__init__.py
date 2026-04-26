# man_hours: 0.25
"""Public API for the run-level :class:`MetricsBundle` dashboard payload.

See ``.cursor/plans/scoring_control_gui_872d4eb7.plan.md`` §9 for the
shape and the reasoning behind it. Every consumer (the GUI, audit MDs,
the future ``GET /metrics/{run_id}`` endpoint) reads this single
payload — there is no second source of truth.
"""

from atoms_vs_ashes.metrics.bundle import (
    CriterionStatPanel,
    CountryStatPanel,
    MetricsBundle,
    NearMissPanel,
    NearMissRow,
    PerCountryMarginPanel,
    PerCriterionMargin,
    PerPairFailure,
    SensitivityPanel,
    SmrStatPanel,
    SummaryPanel,
    TopNRow,
)
from atoms_vs_ashes.metrics.builder import build_metrics_bundle
from atoms_vs_ashes.metrics.csv_writer import write_metrics_csvs
from atoms_vs_ashes.metrics.json_writer import write_metrics_json
from atoms_vs_ashes.metrics.near_miss import build_near_miss_panel
from atoms_vs_ashes.metrics.runtime import build_metrics_bundle_from_session

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
    "build_metrics_bundle",
    "build_metrics_bundle_from_session",
    "build_near_miss_panel",
    "write_metrics_csvs",
    "write_metrics_json",
]
