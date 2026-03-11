"""CLI entry point — ``python -m atoms_vs_ashes`` or ``atoms-vs-ashes``."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.engine import check_connection, init_engine
from atoms_vs_ashes.logging import configure_logging, get_logger, new_run_id

log = get_logger(__name__)


def _resolve_root() -> Path:
    """Walk up from CWD to find the project root (contains pyproject.toml)."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    return cwd


@click.group()
@click.option("--config", "config_path", type=click.Path(exists=True), default=None,
              help="Path to YAML config file (defaults to config/default.yml).")
@click.option("--verbose", is_flag=True, default=False, help="Enable DEBUG logging.")
@click.option("--run-id", default=None, help="Explicit run ID (auto-generated if omitted).")
@click.pass_context
def main(ctx: click.Context, config_path: str | None, verbose: bool, run_id: str | None) -> None:
    """Atoms vs Ashes — SMR Siting Assessment CLI."""
    ctx.ensure_object(dict)
    rid = run_id or new_run_id()
    configure_logging(verbose=verbose, run_id=rid)
    settings = Settings(config_path)
    init_engine(settings)
    ctx.obj["settings"] = settings
    ctx.obj["run_id"] = rid
    ctx.obj["project_root"] = _resolve_root()


@main.command()
@click.pass_context
def ingest(ctx: click.Context) -> None:
    """Run data ingestion pipeline (sites + ownership)."""
    from atoms_vs_ashes.pipeline.runner import run_ingest

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]
    root: Path = ctx.obj["project_root"]

    if not check_connection(settings):
        click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
        sys.exit(1)

    summary = run_ingest(settings, run_id=rid, project_root=root)
    click.echo(json.dumps(summary, indent=2, default=str))


@main.command()
@click.pass_context
def validate(ctx: click.Context) -> None:
    """Run data quality validation checks."""
    from atoms_vs_ashes.pipeline.runner import run_validate

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    if not check_connection(settings):
        click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
        sys.exit(1)

    report = run_validate(settings, run_id=rid)
    click.echo(json.dumps(report, indent=2, default=str))


@main.command()
@click.pass_context
def run(ctx: click.Context) -> None:
    """Execute full pipeline (currently: ingest + validate)."""
    ctx.invoke(ingest)
    ctx.invoke(validate)


# Placeholders for later pipeline stages
@main.command()
@click.pass_context
def enrich(ctx: click.Context) -> None:
    """Run connector framework for all or selected sites. [NOT YET IMPLEMENTED]"""
    click.echo("enrich: not yet implemented")


@main.command()
@click.pass_context
def screen(ctx: click.Context) -> None:
    """Run exclusionary and avoidance screening. [NOT YET IMPLEMENTED]"""
    click.echo("screen: not yet implemented")


@main.command()
@click.pass_context
def score(ctx: click.Context) -> None:
    """Compute scores and rankings. [NOT YET IMPLEMENTED]"""
    click.echo("score: not yet implemented")


@main.command()
@click.pass_context
def report(ctx: click.Context) -> None:
    """Generate output artifacts. [NOT YET IMPLEMENTED]"""
    click.echo("report: not yet implemented")
