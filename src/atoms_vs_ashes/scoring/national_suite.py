# man_hours: 2.8
"""First-class national sensitivity suite.

This module owns the server-side national workflow used by the GUI and
CLI. It deliberately stays separate from the regional ``score
sensitivity`` suite: both workflows may reuse low-level scenario
generation, but national analytics persist to national tables and
country-scoped stability rows only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from atoms_vs_ashes.db.analytics_writers import persist_national_oat_importance
from atoms_vs_ashes.db.runs import complete_run, start_run
from atoms_vs_ashes.runtime.cancellation import (
    CancellationRequested,
    CancellationToken,
)
from atoms_vs_ashes.runtime.heartbeat import HeartbeatWriter
from atoms_vs_ashes.runtime.scope import RunScope
from atoms_vs_ashes.scoring._national_mc_rank import (
    persist_and_write_national_mc_rank,
    run_national_mc_rank_simulation,
)
from atoms_vs_ashes.scoring._national_ranking import DEFAULT_MIN_NATIONAL_PAIRS
from atoms_vs_ashes.scoring._national_sensitivity import (
    NationalProfileSensitivityResult,
    compute_national_profile_sensitivity,
)
from atoms_vs_ashes.scoring._suite_national_oat import (
    NationalOATRunResult,
    run_national_oat_stage,
)
from atoms_vs_ashes.scoring._suite_persist import (
    _resolve_baseline_run_id,
    load_baseline_composites,
    load_pairs,
    persist_mc_summaries,
    persist_weight_results,
)
from atoms_vs_ashes.scoring._suite_sensitivity_site_bands_persist import (
    SiteBandPersistSummary,
    persist_national_site_bands_for_sensitivity_run,
)
from atoms_vs_ashes.scoring.rubric import load_rubric_bundle, weight_normalisation
from atoms_vs_ashes.scoring.scoring_definition_snapshots import (
    link_run_to_snapshot,
    load_bundle_for_run_snapshot,
)
from atoms_vs_ashes.scoring.sensitivity import run_mc_suite, run_weight_sensitivity


@dataclass(frozen=True)
class NationalSensitivityConfig:
    """National sensitivity-run parameters mirrored by the CLI and GUI."""

    iterations: int = 10_000
    seed: int = 42
    weight_profile_base: str = "baseline"
    rubric_dir: str = "config/scoring_rubrics"
    audit_dir: Path = field(default_factory=lambda: Path("audit/post_processing/06_scoring"))
    report_dir: Path | None = None
    min_pairs: int = DEFAULT_MIN_NATIONAL_PAIRS
    smr_key: str | None = None
    progress_enabled: bool = True
    stamp: str | None = None


@dataclass(frozen=True)
class NationalSensitivityResult:
    """Machine-readable result from one national sensitivity run."""

    run_id: str
    smr_key: str | None
    iterations: int
    weight_rows_persisted: int
    mc_rows_persisted: int
    oat: NationalOATRunResult
    profile: NationalProfileSensitivityResult
    mc_rank_csv: Path
    mc_rank_rows: int
    site_band_summary: SiteBandPersistSummary
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "iterations": self.iterations,
            "smr_key": self.smr_key,
            "weight_rows_persisted": self.weight_rows_persisted,
            "mc_rows_persisted": self.mc_rows_persisted,
            "national_oat_csv": str(self.oat.csv_path),
            "national_oat_rows": self.oat.rows_total,
            "national_profile_rank_csv": str(self.profile.rank_csv),
            "national_profile_summary_csv": str(self.profile.summary_csv),
            "national_profile_rank_rows": self.profile.per_pair_rows,
            "national_profile_summary_rows": self.profile.summary_rows,
            "national_mc_rank_csv": str(self.mc_rank_csv),
            "national_mc_rank_rows": self.mc_rank_rows,
            "national_site_band_scopes": self.site_band_summary.rows_by_scope,
            "notes": self.notes,
        }


def _stamp(cfg: NationalSensitivityConfig) -> str:
    return cfg.stamp or datetime.now(timezone.utc).strftime("%Y%m%d")


def _check_cancel(cancellation: CancellationToken | None) -> None:
    if cancellation is not None:
        cancellation.raise_if_cancelled()


def _single_smr_scope(smr_key: str | None) -> RunScope | None:
    return RunScope(smr_keys=(smr_key,)) if smr_key else None


def run_national_sensitivity_suite(
    session: Session,
    cfg: NationalSensitivityConfig,
    *,
    run_id: str,
    cancellation: CancellationToken | None = None,
    heartbeat: HeartbeatWriter | None = None,
) -> NationalSensitivityResult:
    """Run national scenario generation, national rank analytics, and stability."""
    baseline_parent_run_id = _resolve_baseline_run_id(
        session, weight_profile_base=cfg.weight_profile_base,
    )
    run_handle = start_run(
        session, run_kind="national_sensitivity", run_id=run_id,
        parent_run_id=baseline_parent_run_id,
    )
    bundle, inherited_snapshot_id = load_bundle_for_run_snapshot(
        session,
        parent_run_id=baseline_parent_run_id,
        weight_profile=cfg.weight_profile_base,
        rubric_dir=cfg.rubric_dir,
    )
    link_run_to_snapshot(session, run_id=run_id, snapshot_id=inherited_snapshot_id)
    weights = weight_normalisation(bundle, profile=cfg.weight_profile_base)
    scope = _single_smr_scope(cfg.smr_key)
    rows_by_pair, verdicts_by_pair, country_by_pair = load_pairs(
        session, weight_profile_base=cfg.weight_profile_base, scope=scope,
    )
    baseline_rows = load_baseline_composites(
        session, weight_profile_base=cfg.weight_profile_base, scope=scope,
    )
    notes: list[str] = [f"smr_key={cfg.smr_key}"] if cfg.smr_key else []
    stamp = _stamp(cfg)

    try:
        _check_cancel(cancellation)
        weight_results = run_weight_sensitivity(
            rows_by_pair, verdicts_by_pair, weights=weights, criteria=bundle,
        )
        weight_rows = persist_weight_results(
            session, weight_results, run_id=run_id,
        )

        _check_cancel(cancellation)
        if heartbeat is not None:
            heartbeat.start_stage(
                "national_sensitivity:mc_summary",
                total=len(rows_by_pair),
                message=f"draws={cfg.iterations}",
            )
        mc_done = 0

        def _mc_progress(n: int = 1) -> None:
            nonlocal mc_done
            mc_done += n
            if cancellation is not None and cancellation.is_cancelled:
                raise CancellationRequested(cancellation.reason)
            if heartbeat is not None:
                heartbeat.tick(
                    "national_sensitivity:mc_summary",
                    processed=mc_done,
                    total=len(rows_by_pair),
                )

        mc = run_mc_suite(
            rows_by_pair, verdicts_by_pair,
            weights=weights, criteria=bundle, iterations=cfg.iterations,
            seed=cfg.seed, preset_label=None,
            progress_cb=_mc_progress,
        )
        mc_label = f"mc_{cfg.iterations}"
        mc_rows = persist_mc_summaries(
            session, mc, baseline_rows, run_id=run_id, label=mc_label,
        )
        if heartbeat is not None:
            heartbeat.end_stage(
                "national_sensitivity:mc_summary",
                processed=len(rows_by_pair),
                total=len(rows_by_pair),
                message="completed",
            )

        _check_cancel(cancellation)
        oat = run_national_oat_stage(
            session,
            weight_profile_base=cfg.weight_profile_base,
            rubric_dir=cfg.rubric_dir,
            audit_dir=cfg.audit_dir,
            progress_enabled=cfg.progress_enabled,
            run_id=run_id,
            min_pairs=cfg.min_pairs,
            stamp=stamp,
            scope=scope,
            db_writer=persist_national_oat_importance,
        )

        _check_cancel(cancellation)
        profile = compute_national_profile_sensitivity(
            session,
            sensitivity_run_id=run_id,
            baseline_label=cfg.weight_profile_base,
            scoring_run_id=baseline_parent_run_id,
            audit_dir=cfg.audit_dir,
            stamp=stamp,
            min_pairs=cfg.min_pairs,
            smr_key=cfg.smr_key,
            persist=True,
        )

        _check_cancel(cancellation)
        mc_rank_rows = run_national_mc_rank_simulation(
            rows_by_pair,
            verdicts_by_pair,
            country_by_pair,
            weights=weights,
            criteria=bundle,
            iterations=cfg.iterations,
            seed=cfg.seed,
            min_pairs=cfg.min_pairs,
        )
        mc_csv = persist_and_write_national_mc_rank(
            session, run_id=run_id, audit_dir=cfg.audit_dir,
            rows=mc_rank_rows, stamp=stamp,
        )

        session.flush()
        site_band_summary = persist_national_site_bands_for_sensitivity_run(
            session,
            run_id=run_id,
            baseline_label=cfg.weight_profile_base,
            country_codes=tuple(country_by_pair.values()),
        )
        if site_band_summary.total_rows:
            notes.append(
                "national_site_bands="
                + ",".join(
                    f"{scope}:{rows}"
                    for scope, rows in sorted(site_band_summary.rows_by_scope.items())
                )
            )
        complete_run(session, run_handle, status="completed")
    except CancellationRequested:
        complete_run(session, run_handle, status="cancelled")
        raise

    return NationalSensitivityResult(
        run_id=run_id,
        smr_key=cfg.smr_key,
        iterations=cfg.iterations,
        weight_rows_persisted=weight_rows,
        mc_rows_persisted=mc_rows,
        oat=oat,
        profile=profile,
        mc_rank_csv=mc_csv,
        mc_rank_rows=len(mc_rank_rows),
        site_band_summary=site_band_summary,
        notes=notes,
    )


__all__ = [
    "NationalSensitivityConfig",
    "NationalSensitivityResult",
    "run_national_sensitivity_suite",
]
