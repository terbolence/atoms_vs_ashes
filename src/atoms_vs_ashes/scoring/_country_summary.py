# man_hours: 1.25
"""Per-country shortlist-stability summary against baseline.

For every country with ≥ 1 scored pair in the baseline profile, compute:

- ``n_sites`` — count of distinct sites scored in that country.
- ``K`` — shortlist size (see :func:`_band_rules.shortlist_size`).
- ``mean_jaccard_vs_baseline_topk`` / ``min_jaccard_vs_baseline_topk`` —
  Jaccard between baseline country top-K and each non-baseline scenario's
  country top-K, aggregated across scenarios.

Optional ``smr_filter`` restricts to a single ``smr_key`` (e.g.
``nuscale_voygr6``) so the NuScale-specific summary uses the same code.
Band counts (A/B/C) are **not** computed here — they are attached by
the driver from the matching per-country bands CSV.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models import CompositeRanking, Site
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring._band_rules import shortlist_size

log = get_logger(__name__)

SUMMARY_CSV_FIELDS = (
    "country_code",
    "n_sites",
    "K",
    "scenarios_compared",
    "mean_jaccard_vs_baseline_topk",
    "min_jaccard_vs_baseline_topk",
)


@dataclass(frozen=True)
class _Row:
    profile: str
    site_id: str
    country: str
    smr_key: str
    score: float


@dataclass
class CountrySummaryRow:
    country_code: str
    n_sites: int
    K: int
    scenarios_compared: int
    mean_jaccard: float
    min_jaccard: float


def _load_rows(
    session: Session, smr_filter: str | None
) -> list[_Row]:
    stmt = (
        select(
            CompositeRanking.weight_profile,
            CompositeRanking.site_id,
            Site.country_code,
            CompositeRanking.smr_key,
            CompositeRanking.composite_score,
        )
        .join(Site, Site.site_id == CompositeRanking.site_id)
    )
    if smr_filter is not None:
        stmt = stmt.where(CompositeRanking.smr_key == smr_filter)
    rows: list[_Row] = []
    for profile, site_id, country, smr_key, score in session.execute(stmt).all():
        if score is None:
            continue
        rows.append(
            _Row(
                profile=str(profile),
                site_id=str(site_id),
                country=str(country or "??"),
                smr_key=str(smr_key),
                score=float(score),
            )
        )
    return rows


def _best_score_per_site(rows: list[_Row]) -> dict[str, float]:
    best: dict[str, float] = {}
    for r in rows:
        prev = best.get(r.site_id)
        if prev is None or r.score > prev:
            best[r.site_id] = r.score
    return best


def _country_topk(
    best: dict[str, float],
    site_country: dict[str, str],
    country: str,
    k: int,
) -> set[str]:
    pairs = [
        (sid, score)
        for sid, score in best.items()
        if site_country.get(sid, "??") == country
    ]
    pairs.sort(key=lambda t: (-t[1], t[0]))
    return {sid for sid, _ in pairs[:k]}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    u = len(a | b)
    if u == 0:
        return 1.0
    return len(a & b) / u


def compute_country_summary(
    session: Session,
    *,
    baseline_label: str = "baseline",
    smr_filter: str | None = None,
) -> list[CountrySummaryRow]:
    """Return per-country summary rows (no DB writes)."""
    all_rows = _load_rows(session, smr_filter)
    by_profile: dict[str, list[_Row]] = defaultdict(list)
    site_country: dict[str, str] = {}
    for r in all_rows:
        by_profile[r.profile].append(r)
        site_country.setdefault(r.site_id, r.country)

    baseline_rows = by_profile.get(baseline_label, [])
    if not baseline_rows:
        log.warning(
            "country_summary_no_baseline",
            baseline=baseline_label,
            smr_filter=smr_filter,
        )
        return []

    scenarios = sorted(k for k in by_profile if k != baseline_label)
    base_best = _best_score_per_site(baseline_rows)
    countries = sorted(
        {site_country.get(sid, "??") for sid in base_best},
        key=lambda c: (c == "??", c),
    )

    # Cache scenario "best score per site"
    scen_best: dict[str, dict[str, float]] = {
        label: _best_score_per_site(by_profile[label]) for label in scenarios
    }

    results: list[CountrySummaryRow] = []
    for country in countries:
        n = sum(
            1 for sid in base_best if site_country.get(sid, "??") == country
        )
        k = shortlist_size(n)
        baseline_topk = _country_topk(base_best, site_country, country, k)
        jac_values: list[float] = []
        for label in scenarios:
            scen_topk = _country_topk(
                scen_best[label], site_country, country, k
            )
            jac_values.append(_jaccard(baseline_topk, scen_topk))
        mean_j = round(sum(jac_values) / len(jac_values), 4) if jac_values else 1.0
        min_j = round(min(jac_values), 4) if jac_values else 1.0
        results.append(
            CountrySummaryRow(
                country_code=country,
                n_sites=n,
                K=k,
                scenarios_compared=len(scenarios),
                mean_jaccard=mean_j,
                min_jaccard=min_j,
            )
        )
    return results


def _csv_filename(stamp: str, *, smr_filter: str | None) -> str:
    parts = [stamp, "country_rankings_summary"]
    if smr_filter is not None:
        parts.append(smr_filter)
    return "_".join(parts) + ".csv"


def write_country_summary_csv(
    audit_dir: Path,
    rows: list[CountrySummaryRow],
    *,
    smr_filter: str | None = None,
    extra_columns: dict[str, dict[str, object]] | None = None,
    stamp: str | None = None,
) -> Path:
    """Write the country summary CSV and return its path.

    ``extra_columns``: optional mapping of ``country_code → {col: value}``
    merged into each row before writing. Used by the orchestrator to
    inject per-country band A/B/C counts once the banding CSVs exist.
    ``stamp`` overrides the default current-UTC-date filename stamp.
    """
    audit_dir.mkdir(parents=True, exist_ok=True)
    stamp_value = stamp or datetime.now(timezone.utc).strftime("%Y%m%d")
    path = audit_dir / _csv_filename(stamp_value, smr_filter=smr_filter)
    fieldnames = list(SUMMARY_CSV_FIELDS)
    extra_cols: set[str] = set()
    if extra_columns:
        for extras in extra_columns.values():
            extra_cols.update(extras.keys())
    fieldnames.extend(sorted(extra_cols - set(fieldnames)))
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            row_dict: dict[str, object] = {
                "country_code": r.country_code,
                "n_sites": r.n_sites,
                "K": r.K,
                "scenarios_compared": r.scenarios_compared,
                "mean_jaccard_vs_baseline_topk": r.mean_jaccard,
                "min_jaccard_vs_baseline_topk": r.min_jaccard,
            }
            if extra_columns and r.country_code in extra_columns:
                row_dict.update(extra_columns[r.country_code])
            for col in fieldnames:
                row_dict.setdefault(col, "")
            writer.writerow(row_dict)
    return path
