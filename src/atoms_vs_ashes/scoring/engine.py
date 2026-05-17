# man_hours: 8.0
"""Scoring orchestrator — Phase 1.3 of the siting report plan.

The orchestrator owns the run lifecycle (load scope + bundle, open
the run handle, drive progress + heartbeat + cancellation, finalise
audit) and delegates the per-site / per-composite work to
:mod:`atoms_vs_ashes.scoring._engine_loop`. Idempotent thanks to
``merge()`` on the unique constraints (Phase 1.7 acceptance).
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.models import (
    RankingScore,
    ScreeningVerdict,
    Site,
    SmrDesign,
)
from atoms_vs_ashes.db.runs import DatasetMeta, complete_run
from atoms_vs_ashes.logging import get_logger, new_run_id
from atoms_vs_ashes.scoring._engine_loop import (
    build_composites,
    end_heartbeat,
    score_sites,
)
from atoms_vs_ashes.scoring._engine_provenance import (
    check_code_coverage,
    open_scoring_run,
    write_scoring_audit,
)
from atoms_vs_ashes.scoring._ranking_row import make_ranking_row
from atoms_vs_ashes.scoring.avoidance import evaluate_avoidance_for_site
from atoms_vs_ashes.scoring.bands import BandResult, evaluate_criterion_value
from atoms_vs_ashes.scoring.exclusionary import evaluate_exclusionary_for_site
from atoms_vs_ashes.scoring.merge_resolver import (
    MergedContext,
    build_context_for_site,
)
from atoms_vs_ashes.runtime.cancellation import (
    CancellationRequested,
    CancellationToken,
)
from atoms_vs_ashes.runtime.heartbeat import HeartbeatWriter
from atoms_vs_ashes.runtime.scope import RunScope
from atoms_vs_ashes.scoring._progress import ProgressReporter
from atoms_vs_ashes.scoring.rubric import Criterion, load_rubric_bundle, weight_normalisation
from atoms_vs_ashes.scoring.scoring_definition_snapshots import (
    persist_compiled_scoring_snapshot,
)

log = get_logger(__name__)


# Underlying NH criteria that feed the SP-F derived NH-14 (combined hazards).
# NH-13 is intentionally omitted: wildfire is a separate weighted criterion and
# does not interact with the other natural-hazard pairs the way seismic + flood
# do. See ``config/scoring_rubrics/nh_natural_hazards.yaml`` NH-14 block.
_NH14_UNDERLYING_IDS: tuple[str, ...] = (
    "NH-01", "NH-03", "NH-04", "NH-08", "NH-09", "NH-10", "NH-11",
)


def _inject_nh14_derived_metrics(
    nh14_values: dict, all_results: dict[str, BandResult]
) -> None:
    """Compute SP-F NH-14 derived metrics from resolved underlying NH scores.

    The metrics ignore underlying criteria that are ``unscored`` or have no
    matched band, so missing data never drags NH-14 down to a synthetic 5.0
    (Ovidiu feedback). If fewer than 5 underlying scores resolve, NH-14
    itself will land in the unscored tail (no band matches).
    """
    resolved: list[float] = []
    for cid in _NH14_UNDERLYING_IDS:
        result = all_results.get(cid)
        if result is None or result.matched_band is None:
            continue
        notes = result.notes or []
        if "unscored" in notes:
            continue
        resolved.append(float(result.score))
    nh14_values["nh_resolved_count"] = len(resolved)
    if resolved:
        nh14_values["nh_min_resolved_score"] = min(resolved)
        nh14_values["nh_count_below_5"] = sum(1 for s in resolved if s < 5)
        nh14_values["nh_count_below_7"] = sum(1 for s in resolved if s < 7)
    else:
        nh14_values.setdefault("nh_min_resolved_score", None)
        nh14_values.setdefault("nh_count_below_5", None)
        nh14_values.setdefault("nh_count_below_7", None)


@dataclass
class ScoringSummary:
    """Aggregate counts returned after a scoring run."""

    run_id: str
    weight_profile: str
    sites_processed: int = 0
    smr_designs: int = 0
    ranking_rows: int = 0
    verdict_rows: int = 0
    composite_rows: int = 0
    excluded_pairs: int = 0
    warnings: list[str] = field(default_factory=list)


class ScoringEngine:
    """Thin orchestrator used from the CLI or from tests."""

    def __init__(
        self,
        session: Session,
        settings: Settings | None = None,
        *,
        rubric_dir: str | None = None,
        weight_profile: str = "baseline",
        scope: RunScope | None = None,
        bundle: dict[str, Criterion] | None = None,
        smr_bundles: dict[str, dict[str, Criterion]] | None = None,
        weights: dict[str, float] | None = None,
        dataset_meta: DatasetMeta | None = None,
        threshold_overrides: dict | None = None,
        cancellation: CancellationToken | None = None,
        heartbeat: HeartbeatWriter | None = None,
        progress_enabled: bool = True,
    ) -> None:
        self.session = session
        self.settings = settings or Settings()
        self.rubric_dir = rubric_dir or "config/scoring_rubrics"
        self.weight_profile = weight_profile
        self.scope = scope or RunScope()
        self.smr_bundles = smr_bundles
        if smr_bundles:
            self.bundle = next(iter(smr_bundles.values()))
        elif bundle is not None:
            self.bundle = bundle
        else:
            self.bundle = load_rubric_bundle(self.rubric_dir)
        self.weights = weights if weights is not None else (
            weight_normalisation(self.bundle, profile=weight_profile)
        )
        self.dataset_meta = dataset_meta
        self.threshold_overrides = threshold_overrides or {}
        self.cancellation = cancellation
        self.heartbeat = heartbeat
        self.progress_enabled = progress_enabled

    # --- internal helpers ------------------------------------------------

    def _load_sites(self) -> list[Site]:
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
        stmt = self.scope.apply_to_sites(stmt)
        return list(self.session.execute(stmt).scalars().all())

    def _load_smr_designs(self) -> list[SmrDesign]:
        stmt = self.scope.apply_to_smrs(select(SmrDesign))
        return list(self.session.execute(stmt).scalars().all())

    def _precompute_site(
        self,
        site: Site,
        bundle: dict[str, Criterion] | None = None,
    ) -> tuple[dict[str, MergedContext], dict[str, BandResult]]:
        b = bundle if bundle is not None else self.bundle
        ctxs: dict[str, MergedContext] = {}
        values: dict[str, BandResult] = {}
        for criterion in b.values():
            if not criterion.participates_in_process:
                continue
            ctx = build_context_for_site(self.session, site, criterion)
            ctxs[criterion.criterion_id] = ctx
            if criterion.is_ranking or criterion.bands or criterion.sub_scores:
                values[criterion.criterion_id] = evaluate_criterion_value(
                    criterion, ctx.values, quality=ctx.quality
                )
        if "NH-14" in b and "NH-14" in ctxs:
            _inject_nh14_derived_metrics(ctxs["NH-14"].values, values)
            values["NH-14"] = evaluate_criterion_value(
                b["NH-14"],
                ctxs["NH-14"].values,
                quality=ctxs["NH-14"].quality,
            )
        return ctxs, values

    def _process_criterion(
        self,
        *,
        site: Site,
        smr: SmrDesign,
        criterion: Criterion,
        ctx: MergedContext,
        result: BandResult | None,
        run_id: str,
    ) -> tuple[list[ScreeningVerdict], RankingScore | None]:
        verdicts: list[ScreeningVerdict] = []
        verdicts.extend(
            evaluate_exclusionary_for_site(
                criterion,
                ctx.values,
                site_id=site.site_id,
                smr_key=smr.smr_key,
                run_id=run_id,
                confidence=ctx.confidence or "low",
                data_sources=ctx.data_sources,
                band_result=result,
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
        for v in verdicts:
            self.session.merge(v)

        row = None
        if result is not None:
            row = make_ranking_row(
                site_id=site.site_id,
                smr_key=smr.smr_key,
                criterion=criterion,
                ctx=ctx,
                result=result,
                weight_normalised=self.weights.get(criterion.criterion_id),
                run_id=run_id,
            )
            self.session.merge(row)
        return verdicts, row

    # --- public entry ----------------------------------------------------

    def run(self, *, run_id: str | None = None) -> ScoringSummary:
        run_id = run_id or new_run_id()
        summary = ScoringSummary(run_id=run_id, weight_profile=self.weight_profile)

        sites = self._load_sites()
        smrs = self._load_smr_designs()
        summary.sites_processed = len(sites)
        summary.smr_designs = len(smrs)
        if not sites or not smrs:
            summary.warnings.append("no_sites_or_smr_designs")
            return summary

        check_code_coverage(self.bundle, summary)
        run_handle = open_scoring_run(
            self.session,
            run_id=run_id,
            rubric_dir=self.rubric_dir,
            bundle=self.bundle,
            sites=sites,
            smrs=smrs,
            weight_profile=self.weight_profile,
            dataset_meta=self.dataset_meta,
        )
        persist_compiled_scoring_snapshot(
            self.session,
            run_id=run_id,
            bundles_by_smr=self.smr_bundles or {"__default__": self.bundle},
            threshold_overrides=self.threshold_overrides,
        )
        log.info(
            "scoring_run_start", run_id=run_id, sites=len(sites), smrs=len(smrs),
            criteria=len(self.bundle), weight_profile=self.weight_profile,
        )
        per_site_units = max(1, len(smrs)) * max(1, len(self.bundle))
        total_units = len(sites) * per_site_units
        total_sites = len(sites)
        try:
            with ProgressReporter(
                total=total_units,
                description=f"Scoring ({len(sites)} sites × {len(smrs)} SMRs)",
                enabled=self.progress_enabled,
            ) as reporter:
                rows_by_pair, verdicts_by_pair = score_sites(
                    self,
                    sites=sites, smrs=smrs, run_id=run_id,
                    summary=summary, reporter=reporter,
                    cancellation=self.cancellation,
                    heartbeat=self.heartbeat,
                )
            build_composites(
                self,
                rows_by_pair=rows_by_pair,
                verdicts_by_pair=verdicts_by_pair,
                run_id=run_id, summary=summary,
                cancellation=self.cancellation,
            )
            write_scoring_audit(self.session, summary)
            complete_run(self.session, run_handle, status="completed")
        except CancellationRequested as exc:
            # Tick the GUI with "cancelled" first, then re-raise so
            # session_scope rolls back every staged row.
            log.warning("scoring_run_cancelled", run_id=run_id, reason=exc.reason)
            end_heartbeat(
                self.heartbeat, stage="scoring", processed=0,
                total=total_sites, message="cancelled", unit="sites",
            )
            raise
        end_heartbeat(
            self.heartbeat, stage="scoring",
            processed=total_sites, total=total_sites,
            message="completed", unit="sites",
        )
        log.info(
            "scoring_run_complete", run_id=run_id,
            ranking_rows=summary.ranking_rows, verdict_rows=summary.verdict_rows,
            composite_rows=summary.composite_rows, excluded=summary.excluded_pairs,
        )
        return summary


def run_scoring(
    session: Session,
    *,
    rubric_dir: str | None = None,
    weight_profile: str = "baseline",
    run_id: str | None = None,
    settings: Settings | None = None,
    scope: RunScope | None = None,
    bundle: dict[str, Criterion] | None = None,
    smr_bundles: dict[str, dict[str, Criterion]] | None = None,
    weights: dict[str, float] | None = None,
    dataset_meta: DatasetMeta | None = None,
    threshold_overrides: dict | None = None,
    cancellation: CancellationToken | None = None,
    heartbeat: HeartbeatWriter | None = None,
    progress_enabled: bool = True,
) -> ScoringSummary:
    """Top-level helper wrapping :class:`ScoringEngine`."""
    engine = ScoringEngine(
        session, settings=settings, rubric_dir=rubric_dir,
        weight_profile=weight_profile, scope=scope, bundle=bundle,
        smr_bundles=smr_bundles, weights=weights, dataset_meta=dataset_meta,
        threshold_overrides=threshold_overrides,
        cancellation=cancellation, heartbeat=heartbeat,
        progress_enabled=progress_enabled,
    )
    return engine.run(run_id=run_id)
