# man_hours: 8.0
"""Scoring orchestrator — Phase 1.3 of the siting report plan.

For every site × SMR × criterion:

1. Build a merged context via :mod:`merge_resolver`.
2. Evaluate exclusionary + avoidance ``fail_conditions`` and persist
   ``screening_verdicts`` rows.
3. If the criterion is in the ranking phase, evaluate its bands /
   sub-scores (:mod:`bands`) and write a ``ranking_scores`` row.
4. After every SMR pass, compute the composite (:mod:`composite`) and
   write a ``composite_rankings`` row with the supplied
   ``weight_profile``.

The engine is idempotent thanks to ORM ``merge()`` on the existing
unique constraints (``uq_verdict_…``, ``uq_ranking_…``,
``uq_composite_…``). Re-running with the same rubric + data + run_id
reproduces all scores exactly (Phase 1.7 acceptance criterion).
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.models import (
    AuditLog,
    RankingScore,
    ScreeningVerdict,
    Site,
    SmrDesign,
)
from atoms_vs_ashes.db.runs import DatasetMeta, complete_run, start_run
from atoms_vs_ashes.logging import get_logger, new_run_id
from atoms_vs_ashes.scoring._codes import check_rubric_coverage
from atoms_vs_ashes.scoring._ranking_row import make_ranking_row
from atoms_vs_ashes.scoring.avoidance import evaluate_avoidance_for_site
from atoms_vs_ashes.scoring.bands import BandResult, evaluate_criterion_value
from atoms_vs_ashes.scoring.composite import (
    build_composite_row,
    compute_composite_for_site_smr,
)
from atoms_vs_ashes.scoring.exclusionary import evaluate_exclusionary_for_site
from atoms_vs_ashes.scoring.merge_resolver import (
    MergedContext,
    build_context_for_site,
)
from atoms_vs_ashes.scoring.rubric import Criterion, load_rubric_bundle, weight_normalisation

log = get_logger(__name__)


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
    ) -> None:
        self.session = session
        self.settings = settings or Settings()
        self.rubric_dir = rubric_dir or "config/scoring_rubrics"
        self.weight_profile = weight_profile
        self.bundle: dict[str, Criterion] = load_rubric_bundle(self.rubric_dir)
        self.weights: dict[str, float] = weight_normalisation(
            self.bundle, profile=weight_profile
        )

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
        return list(self.session.execute(stmt).scalars().all())

    def _load_smr_designs(self) -> list[SmrDesign]:
        return list(self.session.execute(select(SmrDesign)).scalars().all())

    def _precompute_site(
        self, site: Site
    ) -> tuple[dict[str, MergedContext], dict[str, BandResult]]:
        ctxs: dict[str, MergedContext] = {}
        values: dict[str, BandResult] = {}
        for criterion in self.bundle.values():
            ctx = build_context_for_site(self.session, site, criterion)
            ctxs[criterion.criterion_id] = ctx
            if criterion.is_ranking or criterion.bands or criterion.sub_scores:
                values[criterion.criterion_id] = evaluate_criterion_value(
                    criterion, ctx.values, quality=ctx.quality
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

        self._check_code_coverage(summary)
        run_handle = self._open_run(run_id, sites, smrs)
        log.info(
            "scoring_run_start", run_id=run_id, sites=len(sites),
            smrs=len(smrs), criteria=len(self.bundle),
            weight_profile=self.weight_profile,
        )

        rows_by_pair: dict[tuple, list[RankingScore]] = defaultdict(list)
        verdicts_by_pair: dict[tuple, list[ScreeningVerdict]] = defaultdict(list)

        for site in sites:
            site_ctxs, site_values = self._precompute_site(site)
            for smr in smrs:
                pair = (site.site_id, smr.smr_key)
                for cid, criterion in self.bundle.items():
                    verdicts, row = self._process_criterion(
                        site=site, smr=smr, criterion=criterion,
                        ctx=site_ctxs[cid], result=site_values.get(cid),
                        run_id=run_id,
                    )
                    verdicts_by_pair[pair].extend(verdicts)
                    summary.verdict_rows += len(verdicts)
                    if row is not None:
                        rows_by_pair[pair].append(row)
                        summary.ranking_rows += 1

        for pair, rows in rows_by_pair.items():
            composite = compute_composite_for_site_smr(
                site_id=pair[0], smr_key=pair[1], ranking_rows=rows,
                verdicts=verdicts_by_pair.get(pair, []),
                weights=self.weights, criteria=self.bundle,
            )
            self.session.merge(build_composite_row(
                composite, run_id=run_id, weight_profile=self.weight_profile,
            ))
            summary.composite_rows += 1
            if not composite.passed_exclusionary:
                summary.excluded_pairs += 1

        self._write_audit(summary)
        complete_run(self.session, run_handle, status="completed")
        log.info(
            "scoring_run_complete", run_id=run_id,
            ranking_rows=summary.ranking_rows, verdict_rows=summary.verdict_rows,
            composite_rows=summary.composite_rows, excluded=summary.excluded_pairs,
        )
        return summary

    def _open_run(self, run_id: str, sites, smrs):
        return start_run(
            self.session, run_kind="scoring", run_id=run_id,
            dataset_meta=DatasetMeta(
                rubric_file_path=self.rubric_dir,
                n_sites_total=len(sites), n_smrs=len(smrs),
                n_criteria_ranking=sum(
                    1 for c in self.bundle.values() if c.is_ranking
                ),
                weight_normalisation_profile=self.weight_profile,
            ),
        )

    def _check_code_coverage(self, summary: ScoringSummary) -> None:
        """Warn if the loaded rubric drifts from the E1-E9 / A1-A15 catalog."""
        rubric_codes = {
            fc.code
            for c in self.bundle.values()
            for fc in c.fail_conditions
            if fc.action in ("exclude", "avoidance_penalty")
        }
        missing, extra = check_rubric_coverage(rubric_codes)
        if missing:
            summary.warnings.append(
                f"catalog_codes_missing_from_rubric={sorted(missing)}"
            )
            log.warning("scoring_catalog_mismatch", missing=sorted(missing))
        if extra:
            summary.warnings.append(f"rubric_codes_not_in_catalog={sorted(extra)}")
            log.warning("scoring_catalog_mismatch", extra=sorted(extra))

    def _write_audit(self, summary: ScoringSummary) -> None:
        self.session.add(
            AuditLog(
                operation="scoring",
                table_name="ranking_scores",
                run_id=summary.run_id,
                message=(
                    f"profile={summary.weight_profile} "
                    f"sites={summary.sites_processed} smrs={summary.smr_designs} "
                    f"rows={summary.ranking_rows} verdicts={summary.verdict_rows} "
                    f"composites={summary.composite_rows} excluded={summary.excluded_pairs}"
                ),
            )
        )


def run_scoring(
    session: Session,
    *,
    rubric_dir: str | None = None,
    weight_profile: str = "baseline",
    run_id: str | None = None,
    settings: Settings | None = None,
) -> ScoringSummary:
    """Top-level helper wrapping :class:`ScoringEngine`."""
    engine = ScoringEngine(
        session,
        settings=settings,
        rubric_dir=rubric_dir,
        weight_profile=weight_profile,
    )
    return engine.run(run_id=run_id)
