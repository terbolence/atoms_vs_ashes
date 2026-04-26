# man_hours: 0.25
"""``score preview`` command — moved out of :mod:`_cli` for the
file-size budget. Pure CLI glue around
:func:`atoms_vs_ashes.criterion_spec.build_preview`.
"""

from __future__ import annotations

import json
from pathlib import Path

import click

from atoms_vs_ashes.criterion_spec import build_preview, load_template_bundle
from atoms_vs_ashes.runprofile import parse_run_profile


@click.command(
    "preview",
    help=(
        "Compile a RunProfile + scoring spec without touching the DB and "
        "print the resulting scoring matrix, normalised weights, and any "
        "diff vs. recommended. Implements §7's `score preview`."
    ),
)
@click.option(
    "--run-profile",
    "run_profile_path",
    type=click.Path(dir_okay=False, exists=True),
    required=True,
    help="Path to the RunProfile YAML to preview.",
)
@click.option(
    "--spec-dir",
    type=click.Path(file_okay=False, exists=True),
    default=None,
    help="Override RunProfile.spec_dir (defaults to the profile's value).",
)
def preview_command(run_profile_path: str, spec_dir: str | None) -> None:
    """Render the JSON preview bundle to stdout."""
    profile, _profile_sha = parse_run_profile(Path(run_profile_path))
    resolved_spec_dir = spec_dir or profile.spec_dir
    template_bundle = load_template_bundle(resolved_spec_dir)
    bundle = build_preview(template_bundle, profile, spec_dir=resolved_spec_dir)
    click.echo(json.dumps(bundle.to_dict(), indent=2, default=str))


__all__ = ["preview_command"]
