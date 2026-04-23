# man_hours: 1.5
"""Site stability banding across non-baseline sensitivity scenarios.

Reads every ``composite_rankings`` profile that is not ``baseline``,
computes top-5 % / top-10 % site sets per scenario, and assigns each
site a stability band:

    A  top-5 %  in ≥ 80 % of scenarios
    B  top-10 % in ≥ 80 % of scenarios (not A)
    C  top-10 % in 50–79 % of scenarios
    D  below top-10 % in every scenario

A site is "in top-N %" of a scenario when *any* of its (site, SMR)
pairs falls in the top-N % of the scenario's scored pairs. Output is
one CSV row per scored passing site.
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

log = get_logger(__name__)

BAND_CSV_FIELDS = (
    "site_id",
    "site_name",
    "country",
    "band",
    "top5pct_hit_rate",
    "top10pct_hit_rate",
    "scenarios_total",
    "scenarios_scored",
)

TOP_PCTS: tuple[float, float] = (0.05, 0.10)


@dataclass(frozen=True)
class _Row:
    site_id: str
    smr_key: str
    score: float


@dataclass
class SiteBand:
    """Per-site banding record for CSV output."""

    site_id: str
    site_name: str
    country: str
    band: str
    top5pct_hit_rate: float
    top10pct_hit_rate: float
    scenarios_total: int
    scenarios_scored: int


@dataclass
class BandingRunResult:
    """Summary for the driver/audit."""

    csv_path: Path
    sites_total: int
    band_counts: dict[str, int]
    scenarios_used: list[str]


def _load_nonbaseline_rows(
    session: Session, baseline_label: str
) -> dict[str, list[_Row]]:
    stmt = select(
        CompositeRanking.weight_profile,
        CompositeRanking.site_id,
        CompositeRanking.smr_key,
        CompositeRanking.composite_score,
    ).where(CompositeRanking.weight_profile != baseline_label)
    out: dict[str, list[_Row]] = defaultdict(list)
    for profile, site_id, smr_key, score in session.execute(stmt).all():
        if score is None:
            continue
        out[profile].append(_Row(str(site_id), smr_key, float(score)))
    return dict(out)


def _top_sites(rows: list[_Row], pct: float) -> set[str]:
    """Return the distinct site_ids whose best pair falls in the top-``pct``."""
    if not rows:
        return set()
    rows_sorted = sorted(rows, key=lambda r: r.score, reverse=True)
    n = max(1, int(pct * len(rows_sorted)))
    return {r.site_id for r in rows_sorted[:n]}


def _assign_band(rate5: float, rate10: float) -> str:
    if rate5 >= 0.80:
        return "A"
    if rate10 >= 0.80:
        return "B"
    if rate10 >= 0.50:
        return "C"
    return "D"


def _site_lookup(session: Session) -> dict[str, tuple[str, str]]:
    return {
        str(sid): (name, code)
        for sid, name, code in session.execute(
            select(Site.site_id, Site.name, Site.country_code)
        ).all()
    }


def compute_bands(
    session: Session,
    *,
    baseline_label: str = "baseline",
) -> tuple[list[SiteBand], list[str]]:
    """Compute stability bands for every scored site.

    Returns ``(bands, scenarios_used)`` so the caller can surface the
    scenario list without re-querying.
    """
    rows_by_profile = _load_nonbaseline_rows(session, baseline_label)
    if not rows_by_profile:
        return [], []

    scenarios = sorted(rows_by_profile.keys())
    top5_sets = {label: _top_sites(rows_by_profile[label], TOP_PCTS[0]) for label in scenarios}
    top10_sets = {label: _top_sites(rows_by_profile[label], TOP_PCTS[1]) for label in scenarios}

    all_sites: set[str] = set()
    scored_counts: dict[str, int] = defaultdict(int)
    for label, rows in rows_by_profile.items():
        sites_scored_here: set[str] = set()
        for r in rows:
            all_sites.add(r.site_id)
            sites_scored_here.add(r.site_id)
        for sid in sites_scored_here:
            scored_counts[sid] += 1

    names = _site_lookup(session)
    total = len(scenarios) or 1
    results: list[SiteBand] = []
    for sid in sorted(all_sites):
        hits5 = sum(1 for label in scenarios if sid in top5_sets[label])
        hits10 = sum(1 for label in scenarios if sid in top10_sets[label])
        rate5 = round(hits5 / total, 4)
        rate10 = round(hits10 / total, 4)
        name, country = names.get(sid, ("", "??"))
        results.append(
            SiteBand(
                site_id=sid,
                site_name=name,
                country=country,
                band=_assign_band(rate5, rate10),
                top5pct_hit_rate=rate5,
                top10pct_hit_rate=rate10,
                scenarios_total=total,
                scenarios_scored=scored_counts[sid],
            )
        )
    results.sort(key=lambda b: (b.band, -b.top5pct_hit_rate, -b.top10pct_hit_rate))
    return results, scenarios


def write_bands_csv(audit_dir: Path, bands: list[SiteBand]) -> Path:
    """Write the banding table and return the file path."""
    audit_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    path = audit_dir / f"{stamp}_site_bands.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=BAND_CSV_FIELDS)
        writer.writeheader()
        for b in bands:
            writer.writerow(
                {
                    "site_id": b.site_id,
                    "site_name": b.site_name,
                    "country": b.country,
                    "band": b.band,
                    "top5pct_hit_rate": b.top5pct_hit_rate,
                    "top10pct_hit_rate": b.top10pct_hit_rate,
                    "scenarios_total": b.scenarios_total,
                    "scenarios_scored": b.scenarios_scored,
                }
            )
    return path


def run_banding_stage(
    session: Session,
    *,
    audit_dir: Path,
    baseline_label: str = "baseline",
) -> BandingRunResult:
    """Compute bands, write the CSV, and return a summary."""
    bands, scenarios = compute_bands(session, baseline_label=baseline_label)
    csv_path = write_bands_csv(audit_dir, bands)
    counts: dict[str, int] = defaultdict(int)
    for b in bands:
        counts[b.band] += 1
    log.info(
        "banding_stage_complete",
        sites=len(bands),
        band_counts=dict(counts),
        csv_path=str(csv_path),
    )
    return BandingRunResult(
        csv_path=csv_path,
        sites_total=len(bands),
        band_counts=dict(counts),
        scenarios_used=scenarios,
    )
