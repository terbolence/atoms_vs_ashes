# man_hours: 1.0
"""Project a :class:`MetricsBundle` into the long-format CSVs the GUI
loads in tabular views.

Each panel becomes a single CSV under ``<out_dir>/metrics/`` so the
GUI can link directly to download buttons (plan §9 deliverables) and
so reviewers can pivot in Excel without parsing JSON. Top-level
counts are also exported as a flat ``summary.csv`` for inclusion in
audit MDs.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, Mapping

from atoms_vs_ashes.metrics.bundle import MetricsBundle


def _write_csv(path: Path, header: list[str], rows: Iterable[Mapping]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in header})
    return path


def _summary_rows(bundle: MetricsBundle) -> list[dict]:
    s = bundle.summary
    return [
        {"key": "total_pairs", "value": s.total_pairs},
        {"key": "survived", "value": s.survived},
        {"key": "hard_only", "value": s.hard_only},
        {"key": "floor_only", "value": s.floor_only},
        {"key": "both", "value": s.both},
        {"key": "n_distinct_sites", "value": s.n_distinct_sites},
        {"key": "n_distinct_smrs", "value": s.n_distinct_smrs},
        {"key": "qualification_mode", "value": s.qualification_mode},
    ]


def _criterion_rows(bundle: MetricsBundle) -> list[dict]:
    return [asdict(p) for p in bundle.per_criterion]


def _country_rows(bundle: MetricsBundle) -> list[dict]:
    return [asdict(p) for p in bundle.per_country]


def _smr_rows(bundle: MetricsBundle) -> list[dict]:
    return [asdict(p) for p in bundle.per_smr]


def _top_n_rows(bundle: MetricsBundle) -> list[dict]:
    rows: list[dict] = []
    for r in bundle.top_n_per_country:
        d = asdict(r)
        d["family_scores_json"] = json.dumps(d.pop("family_scores", {}), sort_keys=True)
        rows.append(d)
    return rows


def _per_pair_rows(bundle: MetricsBundle) -> list[dict]:
    return [asdict(r) for r in bundle.per_pair_failures]


def _multi_failure_rows(bundle: MetricsBundle) -> list[dict]:
    return [
        {"distinct_criteria_failed": k, "n_pairs": v}
        for k, v in sorted(bundle.multi_failure_histogram.items())
    ]


def _country_margin_rows(bundle: MetricsBundle) -> list[dict]:
    rows: list[dict] = []
    for panel in bundle.per_country_margins:
        for crit in panel.criteria_eliminating_sites:
            rows.append(
                {
                    "country_code": panel.country_code,
                    "n_sites_total": panel.n_sites_total,
                    "n_sites_passed": panel.n_sites_passed,
                    "criterion_id": crit.criterion_id,
                    "code": crit.code,
                    "metric": crit.metric,
                    "units": crit.units,
                    "n_eliminated": crit.n_eliminated,
                    "median_gap": crit.median_gap,
                    "p90_gap": crit.p90_gap,
                    "max_gap": crit.max_gap,
                    "examples_json": json.dumps(crit.examples, sort_keys=True),
                }
            )
    return rows


def _near_miss_rows(bundle: MetricsBundle) -> list[dict]:
    return [asdict(r) for r in bundle.near_miss.rows]


def write_metrics_csvs(bundle: MetricsBundle, out_dir: Path) -> dict[str, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}

    written["summary"] = _write_csv(
        out_dir / "summary.csv", ["key", "value"], _summary_rows(bundle)
    )
    written["per_criterion"] = _write_csv(
        out_dir / "per_criterion.csv",
        [
            "criterion_id",
            "criterion_name",
            "hard_pairs",
            "floor_pairs",
            "union_pairs",
            "intersection_pairs",
        ],
        _criterion_rows(bundle),
    )
    written["per_country"] = _write_csv(
        out_dir / "per_country.csv",
        [
            "country_code",
            "n_sites",
            "n_pairs",
            "survived",
            "hard_only",
            "floor_only",
            "both",
            "n_sites_with_survivor",
            "mean_composite",
            "p10_composite",
            "p90_composite",
        ],
        _country_rows(bundle),
    )
    written["per_smr"] = _write_csv(
        out_dir / "per_smr.csv",
        [
            "smr_key",
            "n_pairs",
            "survived",
            "hard_only",
            "floor_only",
            "both",
        ],
        _smr_rows(bundle),
    )
    written["top_n_per_country"] = _write_csv(
        out_dir / "top_n_per_country.csv",
        [
            "country_code",
            "smr_key",
            "rank",
            "site_id",
            "site_name",
            "composite_score",
            "composite_score_low",
            "composite_score_high",
            "qualification_mode",
            "family_scores_json",
        ],
        _top_n_rows(bundle),
    )
    written["per_pair_failures"] = _write_csv(
        out_dir / "per_pair_failures.csv",
        [
            "site_id",
            "site_name",
            "country_code",
            "smr_key",
            "criterion_id",
            "code",
            "action",
            "metric",
            "value",
            "threshold",
            "margin",
            "margin_norm",
            "severity",
        ],
        _per_pair_rows(bundle),
    )
    written["multi_failure_histogram"] = _write_csv(
        out_dir / "multi_failure_histogram.csv",
        ["distinct_criteria_failed", "n_pairs"],
        _multi_failure_rows(bundle),
    )
    written["per_country_margins"] = _write_csv(
        out_dir / "per_country_margins.csv",
        [
            "country_code",
            "n_sites_total",
            "n_sites_passed",
            "criterion_id",
            "code",
            "metric",
            "units",
            "n_eliminated",
            "median_gap",
            "p90_gap",
            "max_gap",
            "examples_json",
        ],
        _country_margin_rows(bundle),
    )
    written["near_miss"] = _write_csv(
        out_dir / "near_miss.csv",
        [
            "site_id",
            "site_name",
            "country_code",
            "smr_key",
            "criterion_id",
            "code",
            "metric",
            "value",
            "threshold",
            "gap",
            "gap_norm",
            "would_pass_at_threshold",
            "composite_if_passed",
        ],
        _near_miss_rows(bundle),
    )
    return written


__all__ = ["write_metrics_csvs"]
