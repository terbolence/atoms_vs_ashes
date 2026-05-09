# man_hours: 2.2
"""Click ``score`` group — entry point for scoring + sensitivity CLI.

``--mc-draws`` / ``--preset`` flow into :func:`run_mc_suite`'s
``iterations`` parameter; ``--cancel-flag`` and ``--heartbeat-path``
plug into the GUI-facing cancellation + heartbeat surface (plan §7).
The ``preview`` command lives in :mod:`._cli_preview` to respect the
per-file size budget.
"""

from __future__ import annotations

import json
from pathlib import Path

import click

from sqlalchemy import select

from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.runtime.cancellation import CancellationRequested
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.runtime import install_sigint_handler
from atoms_vs_ashes.scoring._cli_preview import preview_command
from atoms_vs_ashes.scoring._cli_run import (
    apply_profile_scope_to_sensitivity_cfg,
    emit_cancelled_payload,
    emit_summary_payload,
    execute_score_run,
)
from atoms_vs_ashes.scoring._cli_runtime import (
    arm_cancel_flag,
    make_cancellation_token,
    make_heartbeat_writer,
)
from atoms_vs_ashes.scoring.sensitivity import MC_DEFAULT_ITERATIONS, MC_PRESETS
from atoms_vs_ashes.scoring.suite import (
    DEFAULT_AUDIT_DIR,
    DEFAULT_RUBRIC_DIR,
    INCLUDE_CHOICES,
    SensitivitySuiteConfig,
    run_sensitivity_suite,
)

log = get_logger(__name__)


def _resolve_iterations(
    preset: str | None, mc_draws: int | None
) -> tuple[int, str | None]:
    """Resolve ``(iterations, preset_label)`` from the mutually-exclusive flags."""
    if preset is not None and mc_draws is not None:
        raise click.UsageError(
            "--preset and --mc-draws are mutually exclusive; pass one or neither."
        )
    if preset is not None:
        if preset not in MC_PRESETS:
            raise click.UsageError(
                f"Unknown preset '{preset}'. Valid: {sorted(MC_PRESETS)}."
            )
        return MC_PRESETS[preset], preset
    if mc_draws is not None:
        if mc_draws < 1:
            raise click.UsageError("--mc-draws must be >= 1.")
        return mc_draws, None
    return MC_DEFAULT_ITERATIONS, None


_HELP = (
    "Monte Carlo + weight / country sensitivity. "
    "Iteration count flows from this command all the way into the "
    "run_monte_carlo for-loop via run_sensitivity_suite → run_mc_suite. "
    "Presets (via MC_PRESETS): test → 1000, medium → 3000, production → 10000."
)


@click.group("score")
def score_group() -> None:
    """Compute scores, rankings, and run the sensitivity suite."""


@score_group.command("run", help="Run the 0-10 scoring engine over all sites x SMRs.")
@click.option(
    "--weight-profile",
    default="baseline",
    show_default=True,
    help="Weight perturbation profile (baseline | w_plus_20 | w_minus_20).",
)
@click.option(
    "--weight-basis",
    default=None,
    show_default=True,
    help=(
        "Weight basis source per criterion. None / 'baseline' uses the legacy "
        "weight_factor; 'epri', 's_and_l' etc. read criterion.weight_factors[basis]. "
        "Raises if requested basis is not populated on any criterion in the bundle."
    ),
)
@click.option(
    "--rubric-dir",
    type=click.Path(file_okay=False, exists=True),
    default=DEFAULT_RUBRIC_DIR,
    show_default=True,
    help="Directory with scoring rubric YAML files.",
)
@click.option(
    "--heartbeat-path", type=click.Path(dir_okay=False), default=None,
    help="JSONL file the engine appends progress ticks to (GUI live feed).",
)
@click.option(
    "--cancel-flag", type=click.Path(dir_okay=False), default=None,
    help="Sentinel file to poll; the engine cancels when the file appears.",
)
@click.option(
    "--profile",
    "profile_path",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="Run profile YAML: loads spec_dir, fail_thresholds, DB threshold_overrides, "
    "and compiles one rubric bundle per SMR design.",
)
@click.pass_context
def score_run(
    ctx: click.Context, weight_profile: str, weight_basis: str | None,
    rubric_dir: str,
    heartbeat_path: str | None, cancel_flag: str | None,
    profile_path: str | None,
) -> None:
    """Persist ranking_scores, composite_rankings and screening_verdicts."""
    run_id = (ctx.obj or {}).get("run_id")
    token = make_cancellation_token(cancel_flag)
    try:
        with (
            session_scope() as session,
            make_heartbeat_writer(heartbeat_path) as hb,
            install_sigint_handler(token),
        ):
            summary = execute_score_run(
                session=session,
                weight_profile=weight_profile,
                weight_basis=weight_basis,
                rubric_dir=rubric_dir,
                profile_path=profile_path,
                run_id=run_id,
                token=token,
                hb=hb,
            )
    except CancellationRequested as exc:
        emit_cancelled_payload(run_id, exc, kind="scoring")
        ctx.exit(0)
        return
    emit_summary_payload(summary)


@score_group.command("sensitivity", help=_HELP)
@click.option(
    "--preset", type=click.Choice(sorted(MC_PRESETS.keys())), default=None,
    help="Named iteration preset (test → 1000, medium → 3000, "
    "production → 10000). Mutually exclusive with --mc-draws.",
)
@click.option(
    "--mc-draws", type=int, default=None,
    help="Explicit Monte Carlo iteration count (int >= 1). "
    f"Defaults to {MC_DEFAULT_ITERATIONS} when neither flag is given.",
)
@click.option(
    "--include", "include", type=click.Choice(list(INCLUDE_CHOICES)),
    multiple=True, default=("weights", "mc", "country"), show_default=True,
    help="Which sensitivity stages to run. 'threshold' is accepted for "
    "forward-compat but not yet driven (see plan §8).",
)
@click.option(
    "--weight-profile-base", default="baseline", show_default=True,
    help="Weight profile to load baseline ranking_scores / composites for.",
)
@click.option("--seed", type=int, default=42, show_default=True)
@click.option(
    "--rubric-dir", type=click.Path(file_okay=False, exists=False),
    default=DEFAULT_RUBRIC_DIR, show_default=True,
    help="Directory with scoring rubric YAML files.",
)
@click.option(
    "--audit-dir", type=click.Path(file_okay=False),
    default=str(DEFAULT_AUDIT_DIR), show_default=True,
    help="Directory for the audit markdown output.",
)
@click.option(
    "--top-n-country", type=int, default=20, show_default=True,
    help="Top-N window for the country-balance check.",
)
@click.option(
    "--no-progress", is_flag=True, default=False,
    help="Disable the rich progress bar (forces structured-log fallback).",
)
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
    help="Run profile YAML; when set, profile.scope is applied so the "
    "suite uses the same in-scope subset as ``score run --profile``.",
)
@click.pass_context
def sensitivity(  # noqa: PLR0913 — CLI command surface is user-facing config
    ctx: click.Context,
    preset: str | None,
    mc_draws: int | None,
    include: tuple[str, ...],
    weight_profile_base: str,
    seed: int,
    rubric_dir: str,
    audit_dir: str,
    top_n_country: int,
    no_progress: bool,
    heartbeat_path: str | None,
    cancel_flag: str | None,
    profile_path: str | None,
) -> None:
    """Run the sensitivity suite against the currently-selected DB."""
    iterations, preset_label = _resolve_iterations(preset, mc_draws)

    include_set = set(include)
    cfg = SensitivitySuiteConfig(
        iterations=iterations, preset_label=preset_label,
        include_weights="weights" in include_set,
        include_mc="mc" in include_set,
        include_country="country" in include_set,
        include_threshold="threshold" in include_set,
        weight_profile_base=weight_profile_base, seed=seed,
        rubric_dir=rubric_dir, audit_dir=Path(audit_dir),
        progress_enabled=not no_progress, top_n_country=top_n_country,
    )

    run_id = (ctx.obj or {}).get("run_id") or "sensitivity"
    click.echo(json.dumps(
        {
            "message": "sensitivity_suite_starting", "run_id": run_id,
            "iterations": cfg.iterations, "preset": cfg.preset_label,
            "include": sorted(include_set),
            "weight_profile_base": cfg.weight_profile_base,
            "progress_enabled": cfg.progress_enabled,
            "profile": profile_path,
        },
        indent=2,
    ))

    token = make_cancellation_token(cancel_flag)
    try:
        with (
            session_scope() as session,
            make_heartbeat_writer(heartbeat_path) as hb,
            install_sigint_handler(token),
        ):
            if profile_path is not None:
                apply_profile_scope_to_sensitivity_cfg(
                    cfg, profile_path, session=session,
                    default_rubric_dir=DEFAULT_RUBRIC_DIR,
                )
            result = run_sensitivity_suite(
                session, cfg, run_id=run_id,
                cancellation=token, heartbeat=hb,
            )
    except CancellationRequested as exc:
        emit_cancelled_payload(run_id, exc, kind="sensitivity")
        ctx.exit(0)
        return

    click.echo(json.dumps(result.to_dict(), indent=2, default=str))


@score_group.command(
    "cancel",
    help=(
        "Cancel an in-flight scoring or sensitivity run by writing the "
        "sentinel file the running process polls. Pair with --cancel-flag "
        "on `score run` / `score sensitivity` (plan §7)."
    ),
)
@click.option(
    "--cancel-flag",
    "cancel_flag",
    type=click.Path(dir_okay=False),
    required=True,
    help="Path to the sentinel file the running process is watching.",
)
def score_cancel(cancel_flag: str) -> None:
    """Touch the sentinel so the running engine cancels at its next safe point."""
    path = arm_cancel_flag(cancel_flag)
    click.echo(json.dumps({"cancel_flag": str(path), "status": "armed"}, indent=2))


score_group.add_command(preview_command)
