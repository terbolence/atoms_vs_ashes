# man_hours: 2.5
"""Sensitivity-suite orchestrator used by ``ava score sensitivity``.

Public API re-exported at this module level (:class:`SensitivitySuiteConfig`,
:class:`SensitivitySuiteResult`, :func:`run_sensitivity_suite`). The
heavy lifting is split into sibling helpers so every file stays under
the 300-line rule:

- :mod:`._suite_config` — dataclasses + defaults.
- :mod:`._suite_persist` — DB loaders + row-builders.
- :mod:`._suite_audit` — markdown writer.

End-to-end data flow of ``iterations``::

    CLI --mc-draws N  (or --preset {test,medium,production})
        -> SensitivitySuiteConfig.iterations
        -> run_sensitivity_suite
        -> run_mc_suite(..., iterations=cfg.iterations, progress_cb=reporter.advance)
        -> run_monte_carlo(..., iterations=cfg.iterations)
        -> for _ in range(iterations):   # single hot loop
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring._progress import ProgressReporter
from atoms_vs_ashes.scoring._suite_audit import write_audit_md
from atoms_vs_ashes.scoring._suite_config import (
    DEFAULT_AUDIT_DIR,
    DEFAULT_RUBRIC_DIR,
    INCLUDE_CHOICES,
    SensitivitySuiteConfig,
    SensitivitySuiteResult,
)
from atoms_vs_ashes.scoring._suite_persist import (
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
    load_rubric_bundle,
    weight_normalisation,
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


def _build_ranked_country_list(
    country_by_pair: dict[tuple, str],
    baseline_rows,
) -> list[tuple[str, float]]:
    ranked: list[tuple[str, float]] = []
    for pair, base in baseline_rows.items():
        if base.composite_score is None:
            continue
        country = country_by_pair.get(pair, "??")
        ranked.append((country, float(base.composite_score)))
    ranked.sort(key=lambda kv: kv[1], reverse=True)
    return ranked


def run_sensitivity_suite(
    session: Session,
    cfg: SensitivitySuiteConfig,
    *,
    run_id: str,
) -> SensitivitySuiteResult:
    """Execute the requested sensitivity subset and persist its rows.

    ``cfg.iterations`` is forwarded verbatim to :func:`run_mc_suite` and
    from there to :func:`run_monte_carlo`, feeding the single
    ``for _ in range(iterations)`` loop. No other default lives on that
    hot path.
    """
    bundle: dict[str, Criterion] = load_rubric_bundle(cfg.rubric_dir)
    weights = weight_normalisation(bundle, profile=cfg.weight_profile_base)

    rows_by_pair, verdicts_by_pair, country_by_pair = load_pairs(
        session, weight_profile_base=cfg.weight_profile_base
    )
    baseline_rows = load_baseline_composites(
        session, weight_profile_base=cfg.weight_profile_base
    )

    notes: list[str] = []
    mc_label = f"mc_{cfg.iterations}"
    weight_rows = 0
    mc_rows = 0
    country_rows = 0
    country_report: CountryBalanceReport | None = None

    if cfg.include_weights:
        weight_results = run_weight_sensitivity(
            rows_by_pair,
            verdicts_by_pair,
            weights=weights,
            criteria=bundle,
        )
        weight_rows = persist_weight_results(session, weight_results, run_id=run_id)
    else:
        notes.append("weights_skipped")

    if cfg.include_mc:
        with ProgressReporter(
            total=len(rows_by_pair),
            description=f"Monte Carlo ({cfg.iterations} draws)",
            enabled=cfg.progress_enabled,
        ) as reporter:
            mc = run_mc_suite(
                rows_by_pair,
                verdicts_by_pair,
                weights=weights,
                iterations=cfg.iterations,
                seed=cfg.seed,
                progress_cb=reporter.advance,
                preset_label=cfg.preset_label,
            )
        mc_rows = persist_mc_summaries(
            session, mc, baseline_rows, run_id=run_id, label=mc_label
        )
    else:
        notes.append("mc_skipped")

    if cfg.include_country:
        ranked = _build_ranked_country_list(country_by_pair, baseline_rows)
        country_report = country_balance_test(ranked, top_n=cfg.top_n_country)
        country_rows = persist_country_balanced(
            session, baseline_rows, run_id=run_id, country_by_pair=country_by_pair,
        )
    else:
        notes.append("country_skipped")

    threshold_rows = 0
    if cfg.include_threshold:
        with ProgressReporter(
            total=len(rows_by_pair) * len(THRESHOLD_DIRECTIONS),
            description="Threshold ±25",
            enabled=cfg.progress_enabled,
        ) as reporter:
            threshold_results = run_threshold_sensitivity(
                session,
                bundle,
                weights=weights,
                run_id=run_id,
                progress_cb=reporter.advance,
            )
        threshold_rows = persist_threshold_results(
            session, threshold_results, run_id=run_id,
            baseline_rows=baseline_rows,
        )

    session.flush()

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
    result.audit_path = write_audit_md(cfg, result, country_report)
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
    )
    return result
