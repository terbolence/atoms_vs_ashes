# man_hours: 1.0
"""GUI subprocess launcher for national sensitivity runs."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

from atoms_vs_ashes.db.profiles import DEFAULT_PROFILE
from atoms_vs_ashes.gui._runner import (
    RunHandle,
    _load_active_profile,
    _merged_runtime_profile,
    _new_run_id,
    _start_command,
    cleanup_stale_runtime_profiles,
    export_active_profile_to_yaml,
)
from atoms_vs_ashes.runprofile.schema import RunProfile


def _one_smr_from_profile(profile: RunProfile) -> str:
    keys = list(profile.scope.smr_keys)
    if len(keys) != 1:
        raise ValueError(
            "National sensitivity is single-SMR for now. Select exactly one "
            "SMR technology on Sites & SMR Setup and save the active profile."
        )
    return str(keys[0])


def start_national_sensitivity_run(
    *,
    weight_profile: str | None = None,
    profile: RunProfile | None = None,
    mc_rank_draws: int | None = None,
    min_pairs: int = 3,
    smr_key: str | None = None,
    seed: int | None = None,
    audit_dir: str | None = None,
    no_progress: bool = True,
    keep_run_ids: Iterable[str] = (),
) -> RunHandle:
    """Launch the separate ``score national-sensitivity`` workflow."""
    run_id = _new_run_id("nat-sens")
    active = _merged_runtime_profile(
        profile if profile is not None else _load_active_profile()
    )
    seed_val = seed if seed is not None else int(active.sensitivity.mc_seed)
    draws = (
        mc_rank_draws if mc_rank_draws is not None
        else int(active.sensitivity.mc_iterations)
    )
    yaml_path = export_active_profile_to_yaml(
        run_id, profile=active, mc_iterations=draws, mc_seed=seed_val,
    )
    cleanup_stale_runtime_profiles(keep_run_ids={run_id, *keep_run_ids})
    weight = weight_profile or active.weight_profile
    audit = audit_dir or active.output.audit_dir
    selected_smr = smr_key or _one_smr_from_profile(active)
    cmd = [
        sys.executable, "-m", "atoms_vs_ashes",
        "--db-profile", DEFAULT_PROFILE,
        "--run-id", run_id, "score", "national-sensitivity",
        "--weight-profile-base", weight,
        "--rubric-dir", str(Path(active.spec_dir)),
        "--audit-dir", audit, "--seed", str(seed_val),
        "--mc-rank-draws", str(draws),
        "--min-pairs", str(min_pairs),
        "--profile", str(yaml_path.resolve()),
    ]
    cmd += ["--smr-key", selected_smr]
    if no_progress:
        cmd += ["--no-progress"]
    return _start_command(run_id, cmd, profile_path=yaml_path)


__all__ = ["start_national_sensitivity_run"]
