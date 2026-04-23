# man_hours: 3.0
"""Threshold-sensitivity driver for the Phase 1.6 suite.

The sensitivity matrix in ``report/sites_evaluation/08_composite_and_sensitivity.md``
lists ``Threshold sensitivity — ± 25 % on numeric thresholds``. Shifting a
threshold by ±25 % is mathematically equivalent to shifting the *measured*
numeric value by the inverse factor, so this driver simply rebuilds every
per-criterion :class:`MergedContext`, rescales its numeric values via
:func:`scale_numeric_context`, and re-runs the same engine primitives that
produced the baseline composites (bands → E-codes → A-codes → composite).

Two directions are evaluated:

- ``threshold_minus_25`` — numeric context values scaled by ``0.75``
  (proxy for thresholds shifted up by ~33 %).
- ``threshold_plus_25``  — numeric context values scaled by ``1.25``
  (proxy for thresholds shifted down by ~20 %).

We keep all reconstructed rows in-memory so the underlying
``ranking_scores`` table is never touched — only the resulting
``composite_rankings`` row is persisted (one per pair per direction) with
``weight_profile`` set to the direction label, mirroring the existing
weight-sensitivity persistence pattern.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from atoms_vs_ashes.db.models import Site, SmrDesign
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring._ranking_row import make_ranking_row
from atoms_vs_ashes.scoring.avoidance import evaluate_avoidance_for_site
from atoms_vs_ashes.scoring.bands import evaluate_criterion_value
from atoms_vs_ashes.scoring.composite import CompositeResult, compute_composite_for_site_smr
from atoms_vs_ashes.scoring.exclusionary import evaluate_exclusionary_for_site
from atoms_vs_ashes.scoring.merge_resolver import build_context_for_site
from atoms_vs_ashes.scoring.rubric import Criterion
from atoms_vs_ashes.scoring.sensitivity import scale_numeric_context

log = get_logger(__name__)

THRESHOLD_DIRECTIONS: dict[str, float] = {
    "threshold_minus_25": 0.75,
    "threshold_plus_25": 1.25,
}


@dataclass
class ThresholdSensitivityResult:
    """Per-direction bucket of composite results."""

    direction: str
    factor: float
    composites: list[CompositeResult]


def _load_sites(session: Session) -> list[Site]:
    stmt = (
        select(Site)
        .options(
            selectinload(Site.natural_hazards),
            selectinload(Site.human_hazards),
            selectinload(Site.radiological),
            selectinload(Site.emergency_planning),
            selectinload(Site.infrastructure),
        )
        .order_by(Site.country_code, Site.name)
    )
    return list(session.execute(stmt).scalars().all())


def _load_smr_designs(session: Session) -> list[SmrDesign]:
    return list(session.execute(select(SmrDesign)).scalars().all())


def _evaluate_pair(
    *,
    site: Site,
    smr: SmrDesign,
    bundle: dict[str, Criterion],
    site_ctxs: dict[str, object],
    site_values: dict[str, object],
    weights: dict[str, float],
    run_id: str,
) -> CompositeResult:
    """Build an in-memory (rows, verdicts) bundle then compute the composite."""
    rows = []
    verdicts = []
    for cid, criterion in bundle.items():
        ctx = site_ctxs[cid]
        result = site_values.get(cid)
        verdicts.extend(
            evaluate_exclusionary_for_site(
                criterion,
                ctx.values,
                site_id=site.site_id,
                smr_key=smr.smr_key,
                run_id=run_id,
                confidence=ctx.confidence or "low",
                data_sources=ctx.data_sources,
            )
        )
        verdicts.extend(
            evaluate_avoidance_for_site(
                criterion,
                ctx.values,
                site_id=site.site_id,
                smr_key=smr.smr_key,
                run_id=run_id,
                confidence=ctx.confidence or "low",
                data_sources=ctx.data_sources,
            )
        )
        if result is not None:
            rows.append(
                make_ranking_row(
                    site_id=site.site_id,
                    smr_key=smr.smr_key,
                    criterion=criterion,
                    ctx=ctx,
                    result=result,
                    weight_normalised=weights.get(criterion.criterion_id),
                    run_id=run_id,
                )
            )
    return compute_composite_for_site_smr(
        site_id=site.site_id,
        smr_key=smr.smr_key,
        ranking_rows=rows,
        verdicts=verdicts,
        weights=weights,
        criteria=bundle,
    )


def _precompute_site_scaled(
    session: Session,
    site: Site,
    bundle: dict[str, Criterion],
    *,
    factor: float,
) -> tuple[dict[str, object], dict[str, object]]:
    """Build merged contexts and band results with numeric values scaled."""
    ctxs: dict[str, object] = {}
    values: dict[str, object] = {}
    for cid, criterion in bundle.items():
        ctx = build_context_for_site(session, site, criterion)
        scaled = replace(ctx, values=scale_numeric_context(ctx.values, factor))
        ctxs[cid] = scaled
        if criterion.is_ranking or criterion.bands or criterion.sub_scores:
            values[cid] = evaluate_criterion_value(
                criterion, scaled.values, quality=scaled.quality
            )
    return ctxs, values


def run_threshold_direction(
    session: Session,
    bundle: dict[str, Criterion],
    *,
    weights: dict[str, float],
    direction: str,
    factor: float,
    run_id: str,
    progress_cb=None,
) -> ThresholdSensitivityResult:
    """Run one direction (e.g. ``threshold_plus_25``) across every pair."""
    sites = _load_sites(session)
    smrs = _load_smr_designs(session)
    composites: list[CompositeResult] = []
    for site in sites:
        site_ctxs, site_values = _precompute_site_scaled(
            session, site, bundle, factor=factor
        )
        for smr in smrs:
            composites.append(
                _evaluate_pair(
                    site=site,
                    smr=smr,
                    bundle=bundle,
                    site_ctxs=site_ctxs,
                    site_values=site_values,
                    weights=weights,
                    run_id=run_id,
                )
            )
            if progress_cb is not None:
                progress_cb(1)
    log.info(
        "threshold_sensitivity_direction_complete",
        direction=direction,
        factor=factor,
        pairs=len(composites),
    )
    return ThresholdSensitivityResult(
        direction=direction, factor=factor, composites=composites
    )


def run_threshold_sensitivity(
    session: Session,
    bundle: dict[str, Criterion],
    *,
    weights: dict[str, float],
    run_id: str,
    directions: Iterable[tuple[str, float]] | None = None,
    progress_cb=None,
) -> dict[str, ThresholdSensitivityResult]:
    """Run ±25 % threshold sensitivity for every configured direction."""
    directions = directions or list(THRESHOLD_DIRECTIONS.items())
    out: dict[str, ThresholdSensitivityResult] = {}
    for direction, factor in directions:
        out[direction] = run_threshold_direction(
            session,
            bundle,
            weights=weights,
            direction=direction,
            factor=factor,
            run_id=run_id,
            progress_cb=progress_cb,
        )
    log.info(
        "threshold_sensitivity_complete",
        directions=list(out.keys()),
    )
    return out
