"""Click CLI entry point for AVA Client.

Provides the ``ava-client run`` command with coordinate-based site
selection, skip flags, output directory override, and quick-test mode
using three built-in power plant sites.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from ava_client.config import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_OUTPUT_DIR,
    TEST_SITES,
    VALID_SKIP_CHOICES,
)


@click.group()
@click.version_option(package_name="atoms-vs-ashes")
def main() -> None:
    """AVA Client — data acquisition & analysis runner."""


@main.command()
@click.option("--config", "config_path", type=click.Path(exists=True),
              default=str(DEFAULT_CONFIG_PATH), show_default=True,
              help="Path to YAML config file.")
@click.option("--coords", multiple=True,
              help="Ad-hoc site as LAT,LON[:NAME] (repeatable). Bypasses DB.")
@click.option("--test-sites", is_flag=True, default=False,
              help="Use 3 built-in test sites (Rovinari, Belchatow, Tusimice).")
@click.option("--verbose", "-v", is_flag=True, default=False,
              help="Enable DEBUG-level logging.")
@click.option("--run-id", default=None, help="Explicit run ID for traceability.")
@click.option("--output-dir", type=click.Path(), default=str(DEFAULT_OUTPUT_DIR),
              show_default=True, help="Directory for snapshot files.")
@click.option("--skip", multiple=True, type=click.Choice(VALID_SKIP_CHOICES, case_sensitive=False),
              help="Skip specific phases (repeatable).")
@click.option("--max-sites", type=int, default=0, show_default=True,
              help="Limit number of sites processed (0 = all).")
@click.option("--dry-run", is_flag=True, default=False,
              help="Run health checks only, no data fetching.")
@click.option("--no-snapshots", is_flag=True, default=False,
              help="Disable snapshot file writing.")
def run(
    config_path: str,
    coords: tuple[str, ...],
    test_sites: bool,
    verbose: bool,
    run_id: str | None,
    output_dir: str,
    skip: tuple[str, ...],
    max_sites: int,
    dry_run: bool,
    no_snapshots: bool,
) -> None:
    """Run full data acquisition and analysis pipeline."""
    from atoms_vs_ashes.config import Settings
    from atoms_vs_ashes.logging import configure_logging, new_run_id

    if run_id is None:
        run_id = new_run_id()

    configure_logging(verbose=verbose, run_id=run_id)

    settings = Settings(config_path)

    # Resolve sites
    if test_sites:
        sites = list(TEST_SITES)
    elif coords:
        from ava_client.resolver import resolve_from_coords
        sites = resolve_from_coords(list(coords))
    else:
        click.echo("Error: provide --coords or --test-sites.", err=True)
        raise SystemExit(2)

    if max_sites > 0:
        sites = sites[:max_sites]

    if not sites:
        click.echo("Error: no sites resolved.", err=True)
        raise SystemExit(4)

    from ava_client.runner import run as run_pipeline

    exit_code = run_pipeline(
        sites=sites,
        settings=settings,
        run_id=run_id,
        skip=set(skip),
        output_dir=Path(output_dir),
        write_snapshots=not no_snapshots,
        dry_run=dry_run,
    )
    raise SystemExit(exit_code)


@main.command("show-config")
@click.option("--config", "config_path", type=click.Path(exists=True),
              default=str(DEFAULT_CONFIG_PATH), show_default=True)
def show_config(config_path: str) -> None:
    """Dump resolved configuration."""
    import yaml
    from atoms_vs_ashes.config import Settings

    settings = Settings(config_path)
    click.echo(yaml.dump(settings.raw(), default_flow_style=False, allow_unicode=True))


@main.command("health")
@click.option("--config", "config_path", type=click.Path(exists=True),
              default=str(DEFAULT_CONFIG_PATH), show_default=True)
@click.option("--skip", multiple=True, type=click.Choice(VALID_SKIP_CHOICES, case_sensitive=False))
def health_cmd(config_path: str, skip: tuple[str, ...]) -> None:
    """Run health checks only."""
    from atoms_vs_ashes.config import Settings
    from atoms_vs_ashes.logging import configure_logging, new_run_id

    run_id = new_run_id()
    configure_logging(run_id=run_id)
    settings = Settings(config_path)

    from ava_client import display
    from ava_client.phases.health import run_health_checks

    display.print_phase_title(1, 1, "Health Checks")
    run_health_checks(settings, set(skip), DEFAULT_OUTPUT_DIR, run_id, write_snapshots=False)
