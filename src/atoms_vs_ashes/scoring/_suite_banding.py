# man_hours: 1.8
"""Site stability banding across non-baseline sensitivity scenarios.

Scope-parameterised: the same banding logic runs at global, per-SMR,
per-country, and per-country × per-SMR scopes via the ``smr_filter``
and ``country_filter`` parameters on :func:`compute_bands` and
:func:`run_banding_stage`. Within each scope, top-5 / 10 / 30 %
percentiles are computed on that scope's pool, so country bands
reflect within-country competitiveness rather than global rank.

Band assignment rules live in :mod:`_band_rules` so the regional and
national pipelines share a single source of truth.
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
from atoms_vs_ashes.scoring._band_rules import TOP_PCTS, assign_stability_band

log = get_logger(__name__)

BAND_CSV_FIELDS = (
    "site_id",
    "site_name",
    "country",
    "band",
    "top5pct_hit_rate",
    "top10pct_hit_rate",
    "top30pct_hit_rate",
    "scenarios_total",
    "scenarios_scored",
)


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
    top30pct_hit_rate: float
    scenarios_total: int
    scenarios_scored: int


@dataclass
class BandingRunResult:
    """Summary for the driver/audit."""

    csv_path: Path
    sites_total: int
    band_counts: dict[str, int]
    scenarios_used: list[str]
    smr_filter: str | None = None
    country_filter: str | None = None


def _load_nonbaseline_rows(
    session: Session,
    baseline_label: str,
    *,
    run_id: str | None = None,
    smr_filter: str | None = None,
    country_filter: str | None = None,
) -> dict[str, list[_Row]]:
    stmt = select(
        CompositeRanking.weight_profile,
        CompositeRanking.site_id,
        CompositeRanking.smr_key,
        CompositeRanking.composite_score,
    ).where(CompositeRanking.weight_profile != baseline_label)
    if run_id is not None:
        stmt = stmt.where(CompositeRanking.run_id == run_id)
    if smr_filter is not None:
        stmt = stmt.where(CompositeRanking.smr_key == smr_filter)
    if country_filter is not None:
        stmt = stmt.join(Site, Site.site_id == CompositeRanking.site_id).where(
            Site.country_code == country_filter
        )
    out: dict[str, list[_Row]] = defaultdict(list)
    for profile, site_id, smr_key, score in session.execute(stmt).all():
        if score is None:
            continue
        out[profile].append(_Row(str(site_id), smr_key, float(score)))
    return dict(out)


def _top_sites(rows: list[_Row], pct: float) -> set[str]:
    """Return distinct site_ids whose best pair falls in the top-``pct``."""
    if not rows:
        return set()
    rows_sorted = sorted(rows, key=lambda r: r.score, reverse=True)
    n = max(1, int(pct * len(rows_sorted)))
    return {r.site_id for r in rows_sorted[:n]}


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
    run_id: str | None = None,
    smr_filter: str | None = None,
    country_filter: str | None = None,
) -> tuple[list[SiteBand], list[str]]:
    """Compute stability bands for every scored site in the scope.

    Returns ``(bands, scenarios_used)`` so the caller can surface the
    scenario list without re-querying. ``smr_filter`` restricts rows
    to a single ``smr_key`` (None = pool across all SMRs); ``country_filter``
    restricts to an ISO2 country code (None = global pool).
    """
    rows_by_profile = _load_nonbaseline_rows(
        session,
        baseline_label,
        run_id=run_id,
        smr_filter=smr_filter,
        country_filter=country_filter,
    )
    if not rows_by_profile:
        return [], []

    scenarios = sorted(rows_by_profile.keys())
    top5 = {lbl: _top_sites(rows_by_profile[lbl], TOP_PCTS[0]) for lbl in scenarios}
    top10 = {lbl: _top_sites(rows_by_profile[lbl], TOP_PCTS[1]) for lbl in scenarios}
    top30 = {lbl: _top_sites(rows_by_profile[lbl], TOP_PCTS[2]) for lbl in scenarios}

    all_sites: set[str] = set()
    scored_counts: dict[str, int] = defaultdict(int)
    for label, rows in rows_by_profile.items():
        sites_here: set[str] = set()
        for r in rows:
            all_sites.add(r.site_id)
            sites_here.add(r.site_id)
        for sid in sites_here:
            scored_counts[sid] += 1

    names = _site_lookup(session)
    total = len(scenarios) or 1
    results: list[SiteBand] = []
    for sid in sorted(all_sites):
        hits5 = sum(1 for lbl in scenarios if sid in top5[lbl])
        hits10 = sum(1 for lbl in scenarios if sid in top10[lbl])
        hits30 = sum(1 for lbl in scenarios if sid in top30[lbl])
        rate5 = round(hits5 / total, 4)
        rate10 = round(hits10 / total, 4)
        rate30 = round(hits30 / total, 4)
        name, country = names.get(sid, ("", "??"))
        results.append(
            SiteBand(
                site_id=sid,
                site_name=name,
                country=country,
                band=assign_stability_band(rate5, rate10, rate30),
                top5pct_hit_rate=rate5,
                top10pct_hit_rate=rate10,
                top30pct_hit_rate=rate30,
                scenarios_total=total,
                scenarios_scored=scored_counts[sid],
            )
        )
    results.sort(
        key=lambda b: (
            b.band,
            -b.top5pct_hit_rate,
            -b.top10pct_hit_rate,
            -b.top30pct_hit_rate,
        )
    )
    return results, scenarios


def _csv_filename(
    stamp: str,
    *,
    smr_filter: str | None,
    country_filter: str | None,
) -> str:
    parts = [stamp, "site_bands"]
    if country_filter is not None:
        parts.append(country_filter)
    if smr_filter is not None:
        parts.append(smr_filter)
    return "_".join(parts) + ".csv"


def write_bands_csv(
    audit_dir: Path,
    bands: list[SiteBand],
    *,
    smr_filter: str | None = None,
    country_filter: str | None = None,
    stamp: str | None = None,
) -> Path:
    """Write the banding table and return the file path.

    ``stamp`` defaults to the current UTC date (``YYYYMMDD``); pass an
    explicit value to align artefact naming with an upstream run.
    """
    audit_dir.mkdir(parents=True, exist_ok=True)
    stamp_value = stamp or datetime.now(timezone.utc).strftime("%Y%m%d")
    path = audit_dir / _csv_filename(
        stamp_value, smr_filter=smr_filter, country_filter=country_filter
    )
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
                    "top30pct_hit_rate": b.top30pct_hit_rate,
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
    smr_filter: str | None = None,
    country_filter: str | None = None,
    stamp: str | None = None,
) -> BandingRunResult:
    """Compute bands for a scope, write the CSV, return a summary."""
    bands, scenarios = compute_bands(
        session,
        baseline_label=baseline_label,
        smr_filter=smr_filter,
        country_filter=country_filter,
    )
    csv_path = write_bands_csv(
        audit_dir,
        bands,
        smr_filter=smr_filter,
        country_filter=country_filter,
        stamp=stamp,
    )
    counts: dict[str, int] = defaultdict(int)
    for b in bands:
        counts[b.band] += 1
    log.info(
        "banding_stage_complete",
        sites=len(bands),
        band_counts=dict(counts),
        csv_path=str(csv_path),
        smr_filter=smr_filter,
        country_filter=country_filter,
    )
    return BandingRunResult(
        csv_path=csv_path,
        sites_total=len(bands),
        band_counts=dict(counts),
        scenarios_used=scenarios,
        smr_filter=smr_filter,
        country_filter=country_filter,
    )
