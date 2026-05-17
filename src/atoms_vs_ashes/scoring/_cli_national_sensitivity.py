# man_hours: 1.55
"""Click command for first-class national sensitivity runs."""

from __future__ import annotations

import json
from pathlib import Path

import click

from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.runprofile.loader import load_run_profile
from atoms_vs_ashes.runtime import install_sigint_handler
from atoms_vs_ashes.runtime.cancellation import CancellationRequested
from atoms_vs_ashes.scoring._cli_run import emit_cancelled_payload
from atoms_vs_ashes.scoring._cli_runtime import (
    make_cancellation_token,
    make_heartbeat_writer,
)
from atoms_vs_ashes.scoring.national_suite import (
    NationalSensitivityConfig,
    run_national_sensitivity_suite,
)
from atoms_vs_ashes.scoring.suite import DEFAULT_AUDIT_DIR, DEFAULT_RUBRIC_DIR


def _one_smr_from_profile(profile) -> str:
    keys = list(profile.scope.smr_keys)
    if len(keys) != 1:
        raise click.UsageError(
            "`score national-sensitivity --profile` currently requires the "
            "profile to contain exactly one scope.smr_keys entry, or pass "
            "`--smr-key` explicitly."
        )
    return str(keys[0])


def _apply_profile(
    cfg: NationalSensitivityConfig, profile_path: str, *, session,
) -> NationalSensitivityConfig:
    """Apply profile rubric defaults without mixing regional scope semantics."""
    loaded = load_run_profile(profile_path, session=session)
    smr_key = cfg.smr_key or _one_smr_from_profile(loaded.profile)
    if cfg.rubric_dir == DEFAULT_RUBRIC_DIR:
        return NationalSensitivityConfig(
            iterations=cfg.iterations,
            seed=cfg.seed,
            weight_profile_base=cfg.weight_profile_base,
            rubric_dir=loaded.profile.spec_dir,
            audit_dir=cfg.audit_dir,
            report_dir=cfg.report_dir,
            min_pairs=cfg.min_pairs,
            smr_key=smr_key,
            progress_enabled=cfg.progress_enabled,
            stamp=cfg.stamp,
        )
    return NationalSensitivityConfig(
        iterations=cfg.iterations,
        seed=cfg.seed,
        weight_profile_base=cfg.weight_profile_base,
        rubric_dir=cfg.rubric_dir,
        audit_dir=cfg.audit_dir,
        report_dir=cfg.report_dir,
        min_pairs=cfg.min_pairs,
        smr_key=smr_key,
        progress_enabled=cfg.progress_enabled,
        stamp=cfg.stamp,
    )


@click.command("national-sensitivity")
@click.option(
    "--mc-rank-draws", type=int, default=10_000, show_default=True,
    help="Monte Carlo draws for national-rank probability simulation.",
)
@click.option(
    "--min-pairs", type=int, default=3, show_default=True,
    help="Minimum pairs in a country x SMR slice before metrics are non-small-n.",
)
@click.option(
    "--smr-key", default=None,
    help="Restrict national sensitivity to one SMR design key.",
)
@click.option("--seed", type=int, default=42, show_default=True)
@click.option(
    "--weight-profile-base", default="baseline", show_default=True,
    help="Baseline weight profile for ranking score/composite reads.",
)
@click.option(
    "--rubric-dir", type=click.Path(file_okay=False, exists=False),
    default=DEFAULT_RUBRIC_DIR, show_default=True,
)
@click.option(
    "--audit-dir", type=click.Path(file_okay=False),
    default=str(DEFAULT_AUDIT_DIR), show_default=True,
)
@click.option(
    "--report-dir", type=click.Path(file_okay=False), default=None,
    help="Optional report-output directory for national artefacts.",
)
@click.option(
    "--stamp", default=None,
    help="Override the YYYYMMDD output stamp (default: today UTC).",
)
@click.option("--no-progress", is_flag=True, default=False)
@click.option(
    "--heartbeat-path", type=click.Path(dir_okay=False), default=None,
    help="JSONL file the suite appends progress ticks to (GUI live feed).",
)
@click.option(
    "--cancel-flag", type=click.Path(dir_okay=False), default=None,
    help="Sentinel file to poll; the suite cancels when the file appears.",
)
@click.option(
    "--profile", "profile_path",
    type=click.Path(exists=True, dir_okay=False), default=None,
    help="Run profile YAML; when set, profile.spec_dir supplies rubric defaults.",
)
@click.pass_context
def national_sensitivity_command(
    ctx: click.Context,
    mc_rank_draws: int,
    min_pairs: int,
    smr_key: str | None,
    seed: int,
    weight_profile_base: str,
    rubric_dir: str,
    audit_dir: str,
    report_dir: str | None,
    stamp: str | None,
    no_progress: bool,
    heartbeat_path: str | None,
    cancel_flag: str | None,
    profile_path: str | None,
) -> None:
    """Run national sensitivity without invoking regional result writers."""
    if mc_rank_draws < 1:
        raise click.UsageError("--mc-rank-draws must be >= 1.")
    if min_pairs < 1:
        raise click.UsageError("--min-pairs must be >= 1.")
    run_id = (ctx.obj or {}).get("run_id") or "national_sensitivity"
    cfg = NationalSensitivityConfig(
        iterations=mc_rank_draws,
        seed=seed,
        weight_profile_base=weight_profile_base,
        rubric_dir=rubric_dir,
        audit_dir=Path(audit_dir),
        report_dir=Path(report_dir) if report_dir else None,
        min_pairs=min_pairs,
        smr_key=smr_key,
        progress_enabled=not no_progress,
        stamp=stamp,
    )
    click.echo(json.dumps({
        "message": "national_sensitivity_starting",
        "run_id": run_id,
        "iterations": mc_rank_draws,
        "min_pairs": min_pairs,
        "smr_key": smr_key,
        "weight_profile_base": weight_profile_base,
        "profile": profile_path,
    }, indent=2))
    token = make_cancellation_token(cancel_flag)
    try:
        with (
            session_scope() as session,
            make_heartbeat_writer(heartbeat_path) as hb,
            install_sigint_handler(token),
        ):
            if profile_path is not None:
                cfg = _apply_profile(cfg, profile_path, session=session)
            result = run_national_sensitivity_suite(
                session, cfg, run_id=run_id, cancellation=token, heartbeat=hb,
            )
    except CancellationRequested as exc:
        emit_cancelled_payload(run_id, exc, kind="national_sensitivity")
        ctx.exit(0)
        return
    click.echo(json.dumps(result.to_dict(), indent=2, default=str))


__all__ = ["national_sensitivity_command"]
