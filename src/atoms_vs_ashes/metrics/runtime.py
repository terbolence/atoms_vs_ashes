# man_hours: 0.75
"""Session-aware adapter that loads the inputs needed by ``build_metrics_bundle``.

Keeps :mod:`atoms_vs_ashes.metrics.builder` DB-free (so it can be
unit-tested with hand-built objects) while giving the failure-pack
script and future GUI endpoints a single function that returns the
materialised :class:`MetricsBundle`.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.criterion_spec.loader import TemplateBundle
from atoms_vs_ashes.db.models import CompositeRanking, ScreeningVerdict, Site
from atoms_vs_ashes.metrics.builder import build_metrics_bundle
from atoms_vs_ashes.metrics.bundle import (
    MetricsBundle,
    NearMissPanel,
    SensitivityPanel,
)
from atoms_vs_ashes.metrics.margins import (
    aggregate_per_country_margins,
    collect_per_pair_failures,
)
from atoms_vs_ashes.metrics.near_miss import build_near_miss_panel
from atoms_vs_ashes.scoring._failure_breakdown import FailureBreakdown


def _load_site_names(session: Session) -> dict[str, str]:
    return {
        str(sid): name
        for sid, name in session.execute(select(Site.site_id, Site.name)).all()
    }


def _load_composites(
    session: Session,
    *,
    run_id: str | None,
    weight_profile: str = "baseline",
    smr_keys: Sequence[str] | None = None,
) -> list[CompositeRanking]:
    stmt = select(CompositeRanking).where(
        CompositeRanking.weight_profile == weight_profile
    )
    if run_id is not None:
        stmt = stmt.where(CompositeRanking.run_id == run_id)
    if smr_keys:
        stmt = stmt.where(CompositeRanking.smr_key.in_(list(smr_keys)))
    return list(session.execute(stmt).scalars().all())


def _country_pair_counts(breakdown: FailureBreakdown) -> dict[str, dict[str, int]]:
    return {
        c.country_code: {"n_total": c.n_pairs, "n_passed": c.survived}
        for c in breakdown.per_country
    }


def build_metrics_bundle_from_session(  # noqa: PLR0913 - GUI-facing API
    session: Session,
    *,
    run_id: str,
    breakdown: FailureBreakdown,
    country_by_site: dict[Any, str],
    composites_run_id: str | None = None,
    weight_profile: str = "baseline",
    smr_keys: Sequence[str] | None = None,
    qualification_mode: str = "normal",
    top_n_per_country: int = 10,
    sensitivity: SensitivityPanel | None = None,
    near_miss: NearMissPanel | None = None,
    provenance: dict | None = None,
    verdicts_by_pair: dict[tuple, list[ScreeningVerdict]] | None = None,
    template_bundle: TemplateBundle | None = None,
    fail_thresholds: dict[str, dict[str, Any]] | None = None,
    near_miss_gap_pct: float = 10.0,
) -> MetricsBundle:
    """Materialise a :class:`MetricsBundle` from DB state + a breakdown.

    When ``verdicts_by_pair`` and ``template_bundle`` are supplied,
    the per-pair failure margin / per-country eliminator panels are
    populated; otherwise they remain empty (the GUI shows the bundle
    with a "margins not yet computed" banner). ``fail_thresholds``
    follows the run-profile shape — ``{criterion_id: {code: value}}``.
    """
    site_names = _load_site_names(session)
    composites = _load_composites(
        session,
        run_id=composites_run_id,
        weight_profile=weight_profile,
        smr_keys=smr_keys,
    )
    country_by_site_str = {str(k): v for k, v in country_by_site.items()}

    failures: list = []
    margins: list = []
    if verdicts_by_pair is not None and template_bundle is not None:
        smr_filter = smr_keys[0] if smr_keys and len(smr_keys) == 1 else None
        failures = collect_per_pair_failures(
            verdicts_by_pair,
            template_bundle=template_bundle,
            fail_thresholds=fail_thresholds or {},
            country_by_site=country_by_site,
            site_names=site_names,
            smr_filter=smr_filter,
        )
        margins = aggregate_per_country_margins(
            failures,
            country_pair_counts=_country_pair_counts(breakdown),
        )

    if near_miss is None and failures:
        near_miss = build_near_miss_panel(
            failures, gap_threshold_pct=near_miss_gap_pct
        )

    return build_metrics_bundle(
        run_id=run_id,
        breakdown=breakdown,
        composites=composites,
        country_by_site=country_by_site_str,
        site_names=site_names,
        qualification_mode=qualification_mode,
        top_n_per_country=top_n_per_country,
        sensitivity=sensitivity,
        near_miss=near_miss,
        provenance=provenance,
        per_pair_failures=failures,
        per_country_margins=margins,
    )


__all__ = ["build_metrics_bundle_from_session"]
