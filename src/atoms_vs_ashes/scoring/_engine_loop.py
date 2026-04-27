# man_hours: 1.5
"""Inner per-site / per-composite loops for :mod:`engine` (≤ 300-line rule).

Extracted from :class:`atoms_vs_ashes.scoring.engine.ScoringEngine`
without behaviour changes — the orchestrator now owns only the
high-level run lifecycle (load scope, manage progress + cancellation
+ heartbeat, call into here, finalise audit).

Cancellation is checked **between sites** so a long pair-loop never
holds the user hostage; the heartbeat tick is also emitted between
sites so the GUI bar advances at a human-readable cadence rather
than per-criterion.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, TYPE_CHECKING

from atoms_vs_ashes.db.models import (
    RankingScore,
    ScreeningVerdict,
    Site,
    SmrDesign,
)
from atoms_vs_ashes.runtime.cancellation import CancellationToken
from atoms_vs_ashes.runtime.heartbeat import HeartbeatWriter
from atoms_vs_ashes.scoring._composite_components import (
    persist_composite_components,
)
from atoms_vs_ashes.scoring._progress import ProgressReporter
from atoms_vs_ashes.scoring.composite import (
    build_composite_row,
    compute_composite_for_site_smr,
)

if TYPE_CHECKING:
    from atoms_vs_ashes.scoring.engine import ScoringEngine, ScoringSummary


def score_sites(
    engine: "ScoringEngine",
    *,
    sites: list[Site],
    smrs: list[SmrDesign],
    run_id: str,
    summary: "ScoringSummary",
    reporter: ProgressReporter,
    cancellation: CancellationToken | None,
    heartbeat: HeartbeatWriter | None,
) -> tuple[
    dict[tuple, list[RankingScore]],
    dict[tuple, list[ScreeningVerdict]],
]:
    """Iterate sites × SMRs × criteria, persisting verdicts + ranking rows.

    The outer loop is the natural cancellation checkpoint: scope
    typically tops out at a few thousand sites, so checking once per
    site is both responsive (~1 Hz on a fast machine) and cheap.
    Heartbeat ticks are emitted with the same cadence; throttling
    inside :class:`HeartbeatWriter` keeps the JSONL file small.
    """
    rows_by_pair: dict[tuple, list[RankingScore]] = defaultdict(list)
    verdicts_by_pair: dict[tuple, list[ScreeningVerdict]] = defaultdict(list)
    per_site_units = max(1, len(smrs)) * max(
        1,
        len(
            next(iter(engine.smr_bundles.values()))
            if engine.smr_bundles
            else engine.bundle
        ),
    )
    total_units = len(sites) * per_site_units
    total_sites = len(sites)
    if heartbeat is not None:
        heartbeat.start_stage(
            "scoring", total=total_sites,
            message=f"sites={total_sites} smrs={len(smrs)}",
            unit="sites",
        )
    for idx, site in enumerate(sites, start=1):
        if cancellation is not None:
            cancellation.raise_if_cancelled()
        for smr in smrs:
            b = (
                engine.smr_bundles[smr.smr_key]
                if engine.smr_bundles
                else engine.bundle
            )
            site_ctxs, site_values = engine._precompute_site(site, bundle=b)
            pair = (site.site_id, smr.smr_key)
            for cid, criterion in b.items():
                verdicts, row = engine._process_criterion(
                    site=site, smr=smr, criterion=criterion,
                    ctx=site_ctxs[cid], result=site_values.get(cid),
                    run_id=run_id,
                )
                verdicts_by_pair[pair].extend(verdicts)
                summary.verdict_rows += len(verdicts)
                if row is not None:
                    rows_by_pair[pair].append(row)
                    summary.ranking_rows += 1
        reporter.advance(per_site_units)
        if heartbeat is not None:
            heartbeat.tick(
                "scoring",
                processed=idx,
                total=total_sites,
                message=f"site={site.country_code}-{(site.name or '')[:24]}",
                unit="sites",
            )
    return rows_by_pair, verdicts_by_pair


def build_composites(
    engine: "ScoringEngine",
    *,
    rows_by_pair: dict[tuple, list[RankingScore]],
    verdicts_by_pair: dict[tuple, list[ScreeningVerdict]],
    run_id: str,
    summary: "ScoringSummary",
    cancellation: CancellationToken | None = None,
    on_pair: Callable[[tuple, object], None] | None = None,
) -> None:
    """Build + persist composite rows for every (site, SMR) pair.

    Cancellation is checked at the start of each pair so partial
    composites are never half-written; the engine catches
    :class:`CancellationRequested` and marks the run as ``cancelled``
    with whatever rows have been committed (plan §10).
    """
    composite_results = []
    for pair, rows in rows_by_pair.items():
        if cancellation is not None:
            cancellation.raise_if_cancelled()
        crit_for_pair = (
            engine.smr_bundles[pair[1]]
            if engine.smr_bundles
            else engine.bundle
        )
        composite = compute_composite_for_site_smr(
            site_id=pair[0], smr_key=pair[1], ranking_rows=rows,
            verdicts=verdicts_by_pair.get(pair, []),
            weights=engine.weights, criteria=crit_for_pair,
        )
        engine.session.merge(build_composite_row(
            composite, run_id=run_id, weight_profile=engine.weight_profile,
        ))
        composite_results.append(composite)
        summary.composite_rows += 1
        if not composite.passed_exclusionary:
            summary.excluded_pairs += 1
        if on_pair is not None:
            on_pair(pair, composite)
    persist_composite_components(
        engine.session, composite_results,
        run_id=run_id, weight_profile=engine.weight_profile,
    )


def end_heartbeat(
    heartbeat: HeartbeatWriter | None,
    *,
    stage: str,
    processed: int,
    total: int,
    message: str,
    unit: str = "items",
) -> None:
    """Emit a final stage tick when ``heartbeat`` is configured.

    Centralised so the engine + sensitivity orchestrator share the
    same "100 % bar then go away" behaviour expected by the GUI.
    """
    if heartbeat is None:
        return
    heartbeat.end_stage(
        stage, processed=processed, total=total, message=message, unit=unit,
    )


__all__ = ["build_composites", "end_heartbeat", "score_sites"]
