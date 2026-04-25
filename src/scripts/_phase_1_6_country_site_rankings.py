# man_hours: 1.5
"""Compute and persist ``country_site_rankings`` from baseline composites.

Rules:

- One row per ``(run_id, country_code, smr_key, site_id)`` where a
  baseline composite exists in the DB.
- ``national_rank`` is dense within each ``(country_code, smr_key)``
  group; ``regional_rank`` is dense within each ``smr_key`` group.
- ``acceptability_flag`` mirrors ``passed_exclusionary`` from the
  baseline composite (the IAEA-acceptable subset).
- ``band`` and ``p_rank_le_k`` are filled from per-SMR regional-pool
  band CSVs (the only banding scope generated for every SMR today).
- ``pairwise_winrate_top5`` is left as ``NULL`` until the pairwise
  comparison is wired in; the column is queryable but not yet filled.
"""

from __future__ import annotations

import csv as _csv
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.analytics_writers import persist_country_site_rankings
from atoms_vs_ashes.db.models import CompositeRanking, Site
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


def _load_baseline_pairs(
    session: Session, *, baseline_label: str
) -> list[dict[str, object]]:
    stmt = (
        select(
            CompositeRanking.site_id,
            CompositeRanking.smr_key,
            CompositeRanking.composite_score,
            CompositeRanking.composite_score_low,
            CompositeRanking.composite_score_high,
            CompositeRanking.passed_exclusionary,
            Site.country_code,
        )
        .join(Site, Site.site_id == CompositeRanking.site_id)
        .where(CompositeRanking.weight_profile == baseline_label)
    )
    rows: list[dict[str, object]] = []
    for r in session.execute(stmt).all():
        rows.append({
            "site_id": r.site_id,
            "smr_key": r.smr_key,
            "country_code": r.country_code,
            "composite_score": (
                float(r.composite_score) if r.composite_score is not None else None
            ),
            "composite_score_low": (
                float(r.composite_score_low)
                if r.composite_score_low is not None else None
            ),
            "composite_score_high": (
                float(r.composite_score_high)
                if r.composite_score_high is not None else None
            ),
            "acceptability_flag": bool(r.passed_exclusionary),
        })
    return rows


def _read_band_index(csv_path: Path | None) -> dict[str, tuple[str, float]]:
    """Return ``{site_id: (band, top10pct_hit_rate)}`` from a bands CSV."""
    if csv_path is None or not csv_path.exists():
        return {}
    out: dict[str, tuple[str, float]] = {}
    with csv_path.open("r", encoding="utf-8") as fh:
        for row in _csv.DictReader(fh):
            sid = row.get("site_id", "")
            band = row.get("band", "")
            try:
                p10 = float(row.get("top10pct_hit_rate") or 0)
            except ValueError:
                p10 = 0.0
            out[sid] = (band, round(p10, 3))
    return out


def _assign_dense_rank(
    rows: Iterable[dict[str, object]],
    *,
    group_key: tuple[str, ...],
    rank_field: str,
) -> None:
    grouped: dict[tuple, list[dict[str, object]]] = defaultdict(list)
    for r in rows:
        if r["composite_score"] is None:
            continue
        grouped[tuple(r[k] for k in group_key)].append(r)
    for items in grouped.values():
        items.sort(key=lambda r: r["composite_score"], reverse=True)
        for idx, item in enumerate(items, start=1):
            item[rank_field] = idx


def compute_country_site_rankings(
    session: Session,
    *,
    baseline_label: str,
    per_smr_bands: dict[str, Path] | None = None,
) -> list[dict[str, object]]:
    """Materialise the long-form ``country_site_rankings`` rows."""
    pairs = _load_baseline_pairs(session, baseline_label=baseline_label)
    band_indexes: dict[str, dict[str, tuple[str, float]]] = {
        smr: _read_band_index(path) for smr, path in (per_smr_bands or {}).items()
    }
    _assign_dense_rank(pairs, group_key=("country_code", "smr_key"),
                       rank_field="national_rank")
    _assign_dense_rank(pairs, group_key=("smr_key",),
                       rank_field="regional_rank")
    out: list[dict[str, object]] = []
    for r in pairs:
        if r["composite_score"] is None:
            continue
        band_idx = band_indexes.get(str(r["smr_key"]), {})
        band, p10 = band_idx.get(str(r["site_id"]), (None, None))
        out.append({
            "country_code": r["country_code"],
            "smr_key": r["smr_key"],
            "site_id": r["site_id"],
            "national_rank": r.get("national_rank"),
            "regional_rank": r.get("regional_rank"),
            "composite_score": r["composite_score"],
            "composite_score_low": r["composite_score_low"],
            "composite_score_high": r["composite_score_high"],
            "band": band,
            "p_rank_le_k": p10,
            "pairwise_winrate_top5": None,
            "acceptability_flag": r["acceptability_flag"],
        })
    return out


def persist_country_site_rankings_from_db(
    session: Session,
    *,
    run_id: str,
    baseline_label: str,
    per_smr_bands: dict[str, Path] | None = None,
) -> int:
    """Compute + persist; returns row count written."""
    rows = compute_country_site_rankings(
        session, baseline_label=baseline_label, per_smr_bands=per_smr_bands,
    )
    if not rows:
        return 0
    log.info(
        "country_site_rankings_persisting",
        run_id=run_id, rows=len(rows),
    )
    return persist_country_site_rankings(session, run_id=run_id, rows=rows)


__all__ = [
    "compute_country_site_rankings",
    "persist_country_site_rankings_from_db",
]
