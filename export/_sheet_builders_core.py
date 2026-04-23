# man_hours: 1.0
"""Core Excel sheet builders (sites, ownership, verdicts, scoring).

These sheets are available on every DB profile (API, LLM, merged) and
cover the canonical scoring / screening artefacts produced by the
engine:

- ``Sites``, ``Ownership`` — structural DB views.
- ``Screening Verdicts`` — one row per E/A verdict from the engine.
- ``SMR Designs`` — the 8 SMR catalogue used by the ranking loop.
- ``Ranking Scores`` — 0-10 score per site × SMR × criterion.
- ``Composite Rankings`` — site × SMR composites with rank_position.

Phase-2/5 merged-DB sheets live in
:mod:`export._sheet_builders_merged`; this module keeps to the
non-merged surface so it can be imported against any DB profile.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session


def build_sites_df_safe(session: Session) -> pd.DataFrame:
    """Build sites DataFrame with safe column handling."""
    from atoms_vs_ashes.db.models import Site

    sites = session.execute(select(Site)).scalars().all()
    rows = []
    for site in sites:
        row = {}
        for col in Site.__table__.columns:
            if col.key == "alternative_names":
                val = getattr(site, col.key, None)
                row[col.key] = "; ".join(val) if val else None
            else:
                row[col.key] = getattr(site, col.key, None)
        ext = getattr(site, "extended_data", None) or {}
        for key, val in ext.items():
            row[f"ext_{key}"] = val
        rows.append(row)
    return pd.DataFrame(rows)


def build_standard_sites_df(session: Session) -> pd.DataFrame:
    """Build sites DataFrame using the pipeline export helper (fallback-safe)."""
    try:
        from atoms_vs_ashes.pipeline.export import _build_sites_df

        return _build_sites_df(session)
    except Exception:
        return build_sites_df_safe(session)


def build_ownership_df(session: Session) -> pd.DataFrame:
    """One row per :class:`SiteOwnership` entry, joined with site name."""
    from atoms_vs_ashes.db.models import Site, SiteOwnership

    stmt = (
        select(SiteOwnership, Site.name.label("site_name"), Site.country_name)
        .join(Site, SiteOwnership.site_id == Site.site_id)
    )
    results = session.execute(stmt).all()
    rows = []
    for own, site_name, country_name in results:
        row = {c.key: getattr(own, c.key) for c in SiteOwnership.__table__.columns}
        row["site_name"] = site_name
        row["country_name"] = country_name
        rows.append(row)
    return pd.DataFrame(rows)


def build_verdicts_df(session: Session) -> pd.DataFrame:
    """One row per :class:`ScreeningVerdict` entry, joined with site + SMR."""
    from atoms_vs_ashes.db.models import ScreeningVerdict, Site, SmrDesign

    stmt = (
        select(
            ScreeningVerdict,
            Site.name.label("site_name"),
            SmrDesign.name.label("smr_name"),
        )
        .join(Site, ScreeningVerdict.site_id == Site.site_id)
        .join(SmrDesign, ScreeningVerdict.smr_key == SmrDesign.smr_key)
    )
    results = session.execute(stmt).all()
    rows = []
    for v, site_name, smr_name in results:
        row = {c.key: getattr(v, c.key) for c in ScreeningVerdict.__table__.columns}
        row["site_name"] = site_name
        row["smr_name"] = smr_name
        rows.append(row)
    return pd.DataFrame(rows)


def build_smr_df(session: Session) -> pd.DataFrame:
    """One row per :class:`SmrDesign`."""
    from atoms_vs_ashes.db.models import SmrDesign

    objs = session.execute(select(SmrDesign)).scalars().all()
    return pd.DataFrame(
        [{c.key: getattr(obj, c.key) for c in SmrDesign.__table__.columns} for obj in objs]
    )


def build_ranking_scores_df(session: Session) -> pd.DataFrame:
    """Ranking Scores sheet — 0-10 scores per site × SMR × criterion.

    Joined with site + SMR + criterion metadata so downstream consumers
    (engineers, report authors) can read the sheet without re-joining.
    Ordered by site (country, name) then SMR, mirroring the engine's
    scoring loop so row-level diffs between runs are easy to spot.
    """
    from atoms_vs_ashes.db.models import (
        Criterion as CriterionRow,
        RankingScore,
        Site,
        SmrDesign,
    )

    stmt = (
        select(
            RankingScore,
            Site.name.label("site_name"),
            Site.country_code.label("site_country"),
            SmrDesign.name.label("smr_name"),
            CriterionRow.name.label("criterion_name"),
            CriterionRow.category.label("criterion_category"),
            CriterionRow.phase.label("criterion_phase"),
        )
        .join(Site, RankingScore.site_id == Site.site_id)
        .join(SmrDesign, RankingScore.smr_key == SmrDesign.smr_key)
        .outerjoin(
            CriterionRow, RankingScore.criterion_id == CriterionRow.criterion_id
        )
        .order_by(
            Site.country_code,
            Site.name,
            SmrDesign.smr_key,
            RankingScore.criterion_id,
        )
    )
    results = session.execute(stmt).all()
    rows: list[dict[str, Any]] = []
    for (
        r,
        site_name,
        site_country,
        smr_name,
        criterion_name,
        criterion_category,
        criterion_phase,
    ) in results:
        row = {c.key: getattr(r, c.key) for c in RankingScore.__table__.columns}
        row["site_name"] = site_name
        row["site_country"] = site_country
        row["smr_name"] = smr_name
        row["criterion_name"] = criterion_name
        row["criterion_category"] = criterion_category
        row["criterion_phase"] = criterion_phase
        rows.append(row)
    return pd.DataFrame(rows)


def build_composite_rankings_df(session: Session) -> pd.DataFrame:
    """Composite Rankings sheet — one row per site × SMR × weight profile.

    ``rank_position`` is computed per ``(weight_profile, smr_key)`` group
    on the fly so the sheet is self-contained even when the engine run
    did not persist ranks. The per-category score JSON is flattened into
    ``cat_<category>`` columns for at-a-glance comparison.
    """
    from atoms_vs_ashes.db.models import CompositeRanking, Site, SmrDesign

    stmt = (
        select(
            CompositeRanking,
            Site.name.label("site_name"),
            Site.country_code.label("site_country"),
            SmrDesign.name.label("smr_name"),
        )
        .join(Site, CompositeRanking.site_id == Site.site_id)
        .join(SmrDesign, CompositeRanking.smr_key == SmrDesign.smr_key)
        .order_by(
            CompositeRanking.weight_profile,
            SmrDesign.smr_key,
            CompositeRanking.composite_score.desc().nullslast(),
            Site.country_code,
            Site.name,
        )
    )
    results = session.execute(stmt).all()

    rows: list[dict[str, Any]] = []
    rank_counter: dict[tuple[str, str], int] = {}
    for c, site_name, site_country, smr_name in results:
        row = {
            col.key: getattr(c, col.key) for col in CompositeRanking.__table__.columns
        }
        key = (c.weight_profile, c.smr_key)
        rank_counter[key] = rank_counter.get(key, 0) + 1
        if row.get("rank_position") is None:
            row["rank_position"] = rank_counter[key]
        row["site_name"] = site_name
        row["site_country"] = site_country
        row["smr_name"] = smr_name

        per_cat = row.pop("per_category_scores", None) or {}
        if isinstance(per_cat, dict):
            for cat, val in per_cat.items():
                row[f"cat_{cat}"] = val
        rows.append(row)
    return pd.DataFrame(rows)
