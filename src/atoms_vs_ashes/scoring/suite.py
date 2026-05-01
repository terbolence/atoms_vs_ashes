# man_hours: 2.5
"""Sensitivity-suite orchestrator for ``ava score sensitivity``.

CLI ``--mc-draws N`` flows into :func:`run_sensitivity_suite` → MC loop.
Public API: :class:`SensitivitySuiteConfig`, :func:`run_sensitivity_suite`.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from atoms_vs_ashes.db.runs import complete_run, start_run
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.runtime.cancellation import (
    CancellationRequested,
    CancellationToken,
)
from atoms_vs_ashes.runtime.heartbeat import HeartbeatWriter
from atoms_vs_ashes.scoring._progress import ProgressReporter
from atoms_vs_ashes.scoring._suite_audit import write_audit_md
from atoms_vs_ashes.scoring._suite_config import (
    DEFAULT_AUDIT_DIR,
    DEFAULT_RUBRIC_DIR,
    INCLUDE_CHOICES,
    SensitivitySuiteConfig,
    SensitivitySuiteResult,
)
from atoms_vs_ashes.scoring._suite_sensitivity_helpers import (
    build_ranked_country_list,
)
from atoms_vs_ashes.scoring._suite_sensitivity_site_bands_persist import (
    persist_site_bands_for_sensitivity_run,
)
from atoms_vs_ashes.scoring._suite_persist import (
    _resolve_baseline_run_id,
    load_baseline_composites,
    load_pairs,
    persist_country_balanced,
    persist_mc_summaries,
    persist_threshold_results,
    persist_weight_results,
)
from atoms_vs_ashes.scoring._suite_threshold import (
    THRESHOLD_DIRECTIONS,
    run_threshold_sensitivity,
)
from atoms_vs_ashes.scoring.rubric import (
    Criterion,
    weight_normalisation,
)
from atoms_vs_ashes.scoring.scoring_definition_snapshots import (
    link_run_to_snapshot,
    load_bundle_for_run_snapshot,
)
from atoms_vs_ashes.scoring.sensitivity import (
    CountryBalanceReport,
    country_balance_test,
    run_mc_suite,
    run_weight_sensitivity,
)

log = get_logger(__name__)

__all__ = [
    "DEFAULT_AUDIT_DIR",
    "DEFAULT_RUBRIC_DIR",
    "INCLUDE_CHOICES",
    "SensitivitySuiteConfig",
    "SensitivitySuiteResult",
    "run_sensitivity_suite",
]


def run_sensitivity_suite(
    session: Session,
    cfg: SensitivitySuiteConfig,
    *,
    run_id: str,
    cancellation: CancellationToken | None = None,
    heartbeat: HeartbeatWriter | None = None,
) -> SensitivitySuiteResult:
    """Run the requested sensitivity subset and persist its rows.

    ``cfg.iterations`` flows to :func:`run_mc_suite`/:func:`run_monte_carlo`.
    ``cancellation`` is checked between stages so partial work survives.
    ``heartbeat`` (when set) emits start/tick/end events for the GUI.
    """
    # Resolve the baseline scoring ``run_id`` first and persist it as
    # ``runs.parent_run_id`` so the GUI Results page can route the
    # Coverage / Sites / Regional / Stability tabs back to the run that
    # owns the matching ``screening_verdicts``. Without this link the
    # tabs render ``status=hard-fail`` with ``n_failed_criteria=0``.
    baseline_parent_run_id = _resolve_baseline_run_id(
        session, weight_profile_base=cfg.weight_profile_base,
    )
    run_handle = start_run(
        session, run_kind="sensitivity", run_id=run_id,
        parent_run_id=baseline_parent_run_id,
    )
    bundle, inherited_snapshot_id = load_bundle_for_run_snapshot(
        session,
        parent_run_id=baseline_parent_run_id,
        weight_profile=cfg.weight_profile_base,
        rubric_dir=cfg.rubric_dir,
    )
    link_run_to_snapshot(
        session, run_id=run_id, snapshot_id=inherited_snapshot_id
    )
    weights = weight_normalisation(bundle, profile=cfg.weight_profile_base)

    rows_by_pair, verdicts_by_pair, country_by_pair = load_pairs(
        session,
        weight_profile_base=cfg.weight_profile_base,
        scope=cfg.scope,
    )
    baseline_rows = load_baseline_composites(
        session,
        weight_profile_base=cfg.weight_profile_base,
        scope=cfg.scope,
    )

    notes: list[str] = []
    mc_label = f"mc_{cfg.iterations}"
    weight_rows = 0
    mc_rows = 0
    country_rows = 0
    threshold_rows = 0
    country_report: CountryBalanceReport | None = None

    def _check_cancel() -> None:
        if cancellation is not None:
            cancellation.raise_if_cancelled()

    cancelled_reason: str | None = None
    try:
        if cfg.include_weights:
            _check_cancel()
            weight_results = run_weight_sensitivity(
                rows_by_pair, verdicts_by_pair,
                weights=weights, criteria=bundle,
            )
            weight_rows = persist_weight_results(
                session, weight_results, run_id=run_id
            )
        else:
            notes.append("weights_skipped")

        if cfg.include_mc:
            _check_cancel()
            if heartbeat is not None:
                heartbeat.start_stage(
                    "sensitivity:mc", total=len(rows_by_pair),
                    message=f"draws={cfg.iterations}",
                )
            with ProgressReporter(
                total=len(rows_by_pair),
                description=f"Monte Carlo ({cfg.iterations} draws)",
                enabled=cfg.progress_enabled,
            ) as reporter:
                def _mc_advance(n: int = 1) -> None:
                    reporter.advance(n)
                    if cancellation is not None and cancellation.is_cancelled:
                        raise CancellationRequested(cancellation.reason)
                    if heartbeat is not None:
                        heartbeat.tick(
                            "sensitivity:mc",
                            processed=reporter._done,
                            total=len(rows_by_pair),
                        )
                mc = run_mc_suite(
                    rows_by_pair, verdicts_by_pair,
                    weights=weights, criteria=bundle, iterations=cfg.iterations,
                    seed=cfg.seed, progress_cb=_mc_advance,
                    preset_label=cfg.preset_label,
                )
            mc_rows = persist_mc_summaries(
                session, mc, baseline_rows, run_id=run_id, label=mc_label
            )
            if heartbeat is not None:
                heartbeat.end_stage(
                    "sensitivity:mc", processed=len(rows_by_pair),
                    total=len(rows_by_pair), message="completed",
                )
        else:
            notes.append("mc_skipped")

        if cfg.include_country:
            _check_cancel()
            ranked = build_ranked_country_list(country_by_pair, baseline_rows)
            country_report = country_balance_test(ranked, top_n=cfg.top_n_country)
            country_rows = persist_country_balanced(
                session, baseline_rows, run_id=run_id,
                country_by_pair=country_by_pair,
            )
        else:
            notes.append("country_skipped")

        if cfg.include_threshold:
            _check_cancel()
            total = len(rows_by_pair) * len(THRESHOLD_DIRECTIONS)
            if heartbeat is not None:
                heartbeat.start_stage(
                    "sensitivity:threshold", total=total, message="global±25",
                )
            with ProgressReporter(
                total=total, description="Threshold ±25",
                enabled=cfg.progress_enabled,
            ) as reporter:
                def _t_advance(n: int = 1) -> None:
                    reporter.advance(n)
                    if cancellation is not None and cancellation.is_cancelled:
                        raise CancellationRequested(cancellation.reason)
                    if heartbeat is not None:
                        heartbeat.tick(
                            "sensitivity:threshold",
                            processed=reporter._done, total=total,
                        )
                threshold_results = run_threshold_sensitivity(
                    session, bundle, weights=weights, run_id=run_id,
                    progress_cb=_t_advance, scope=cfg.scope,
                )
            threshold_rows = persist_threshold_results(
                session, threshold_results, run_id=run_id,
                baseline_rows=baseline_rows,
            )
            if heartbeat is not None:
                heartbeat.end_stage(
                    "sensitivity:threshold", processed=total, total=total,
                    message="completed",
                )
    except CancellationRequested as exc:
        cancelled_reason = exc.reason or "requested"
        log.warning(
            "sensitivity_suite_cancelled", run_id=run_id, reason=cancelled_reason,
            weight_rows=weight_rows, mc_rows=mc_rows,
            country_rows=country_rows, threshold_rows=threshold_rows,
        )
        # Propagate so session_scope rolls back any partial sensitivity
        # rows that were merged before the user hit Cancel — there is no
        # "partial sensitivity result" the engine wants to persist.
        raise

    session.flush()
    site_band_summary = persist_site_bands_for_sensitivity_run(
        session,
        run_id=run_id,
        baseline_label=cfg.weight_profile_base,
        country_codes=tuple(country_by_pair.values()),
    )
    # Flip ``runs.status`` so the GUI run-verification panel can read
    # ``completed_at``; cancel/error paths let session_scope roll back.
    complete_run(session, run_handle, status="completed")

    result = SensitivitySuiteResult(
        run_id=run_id,
        pairs=len(rows_by_pair),
        iterations=cfg.iterations,
        preset_label=cfg.preset_label,
        weight_rows_persisted=weight_rows,
        mc_rows_persisted=mc_rows,
        country_balanced_rows_persisted=country_rows,
        threshold_rows_persisted=threshold_rows,
        country_report=(
            {
                "total_sites": country_report.total_sites,
                "top_n": country_report.top_n,
                "max_share": country_report.max_share,
                "flagged": country_report.flagged,
                "country_counts": country_report.country_counts,
            }
            if country_report is not None
            else None
        ),
        audit_path=Path(),
        mc_label=mc_label,
        notes=notes,
    )
    result.audit_path = write_audit_md(
        cfg, result, country_report, provenance_block=cfg.provenance_md,
    )
    log.info(
        "sensitivity_suite_complete",
        run_id=run_id,
        pairs=result.pairs,
        iterations=result.iterations,
        preset=result.preset_label,
        weight_rows=result.weight_rows_persisted,
        mc_rows=result.mc_rows_persisted,
        country_rows=result.country_balanced_rows_persisted,
        threshold_rows=result.threshold_rows_persisted,
        site_band_scopes=site_band_summary.rows_by_scope,
    )
    return result
