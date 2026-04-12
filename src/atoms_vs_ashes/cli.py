# man_hours: 6.0
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


_DB_PROFILES = {
    "api": "atoms_vs_ashes",
    "llm": "atoms_vs_ashes_llm",
}


@click.group()
@click.option("--config", "config_path", type=click.Path(exists=True), default=None,
              help="Path to YAML config file (defaults to config/default.yml).")
@click.option("--verbose", is_flag=True, default=False, help="Enable DEBUG logging.")
@click.option("--run-id", default=None, help="Explicit run ID (auto-generated if omitted).")
@click.option("--db-profile", type=click.Choice(["api", "llm"]), default="api",
              show_default=True,
              help="Database profile: 'api' (default) or 'llm'.")
@click.pass_context
def main(ctx: click.Context, config_path: str | None, verbose: bool,
         run_id: str | None, db_profile: str) -> None:
    """Atoms vs Ashes — SMR Siting Assessment CLI."""
    import os
    ctx.ensure_object(dict)
    rid = run_id or new_run_id()
    configure_logging(verbose=verbose, run_id=rid)

    os.environ["POSTGRES_DB"] = _DB_PROFILES[db_profile]

    settings = Settings(config_path)
    init_engine(settings)
    ctx.obj["settings"] = settings
    ctx.obj["run_id"] = rid
    ctx.obj["project_root"] = _resolve_root()
    ctx.obj["db_profile"] = db_profile
    log.info("Using database profile '%s' → %s", db_profile, settings.database.db)


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


@main.group()
@click.pass_context
def enrich(ctx: click.Context) -> None:
    """Run data-enrichment connectors for sites."""


@enrich.command("seismic-hazard")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate connectivity with one sample fetch, don't persist.")
@click.pass_context
def enrich_seismic_hazard(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    dry_run: bool,
) -> None:
    """Fetch seismic hazard data (S-01: EFEHR/GEM) for sites."""
    from atoms_vs_ashes.connectors.seismic_hazard import SeismicHazardConnector
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    if not check_connection(settings):
        click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
        sys.exit(1)

    with SeismicHazardConnector(settings) as connector:
        if dry_run:
            click.echo("Dry run — checking EFEHR connectivity…")
            ok = connector.health_check()
            click.echo(f"EFEHR health check: {'OK' if ok else 'FAILED'}")
            if ok:
                result = connector.fetch_all(lat=44.15, lon=23.12)
                click.echo(json.dumps(result.to_dict(), indent=2, default=str))
            return

        with session_scope() as session:
            ids = list(site_ids) if site_ids else None
            codes = list(country_codes) if country_codes else None

            if enrich_all_flag:
                batch = connector.enrich_all(session, rid)
            elif ids:
                batch = connector.enrich_batch(session, rid, site_ids=ids)
            elif codes:
                batch = connector.enrich_batch(session, rid, country_codes=codes)
            else:
                click.echo(
                    "ERROR: Specify --site-id, --country, or --all.", err=True
                )
                sys.exit(1)

        click.echo(batch.summary_line())
        click.echo(json.dumps(batch.to_dict(), indent=2, default=str))


@main.command()
@click.option(
    "--criteria", "criteria_ids", multiple=True,
    help="Run only specific criteria (e.g. --criteria BF-01). Omit for all.",
)
@click.pass_context
def screen(ctx: click.Context, criteria_ids: tuple[str, ...]) -> None:
    """Run screening checks (basic filters, exclusionary, avoidance)."""
    from atoms_vs_ashes.pipeline.runner import run_screening

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    if not check_connection(settings):
        click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
        sys.exit(1)

    cids = list(criteria_ids) if criteria_ids else None
    summary = run_screening(settings, run_id=rid, criteria=cids)
    click.echo(json.dumps(summary, indent=2, default=str))


@main.command()
@click.pass_context
def score(ctx: click.Context) -> None:
    """Compute scores and rankings. [NOT YET IMPLEMENTED]"""
    click.echo("score: not yet implemented")


@main.command()
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="export/atoms_vs_ashes_export.xlsx",
    show_default=True,
    help="Output path for the Excel file.",
)
@click.pass_context
def export(ctx: click.Context, output: str) -> None:
    """Export entire database to a structured Excel file."""
    from atoms_vs_ashes.db.engine import session_scope
    from atoms_vs_ashes.pipeline.export import export_to_xlsx

    settings: Settings = ctx.obj["settings"]

    if not check_connection(settings):
        click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
        sys.exit(1)

    with session_scope() as session:
        out = export_to_xlsx(session, output)

    click.echo(f"Exported to {out}")


@main.command()
@click.pass_context
def report(ctx: click.Context) -> None:
    """Generate output artifacts. [NOT YET IMPLEMENTED]"""
    click.echo("report: not yet implemented")


@main.command("llm-assess")
@click.option("--tier", type=click.Choice(["all", "exclusionary", "avoidance", "ranking"]),
              default="all", show_default=True,
              help="Which tier to run.")
@click.option("--sites", "site_csv", default=None,
              help="Comma-separated site UUIDs, or omit for all sites.")
@click.option("--country", "country_csv", default=None,
              help="Comma-separated country codes (e.g. RO,BG,PL).")
@click.option("--dry-run", is_flag=True, default=False,
              help="Show what would be assessed without calling the API.")
@click.option("--max-concurrent", type=int, default=None,
              help="Override concurrent request limit.")
@click.pass_context
def llm_assess(
    ctx: click.Context,
    tier: str,
    site_csv: str | None,
    country_csv: str | None,
    dry_run: bool,
    max_concurrent: int | None,
) -> None:
    """Run LLM-based siting assessment (writes to atoms_vs_ashes_llm DB)."""
    import asyncio
    import uuid as _uuid

    from atoms_vs_ashes.llm.config import LlmConfig
    from atoms_vs_ashes.llm.orchestrator import LlmOrchestrator

    settings: Settings = ctx.obj["settings"]
    rid: str = f"llm-{ctx.obj['run_id']}"

    if not check_connection(settings):
        click.echo("ERROR: Cannot connect to main database.", err=True)
        sys.exit(1)

    llm_cfg = LlmConfig.from_yaml(settings._yaml)
    if max_concurrent:
        llm_cfg = LlmConfig(
            **{k: v for k, v in llm_cfg.__dict__.items() if k != "max_concurrent"},
            max_concurrent=max_concurrent,
        )

    site_ids = None
    if site_csv:
        site_ids = [_uuid.UUID(s.strip()) for s in site_csv.split(",")]
    country_codes = None
    if country_csv:
        country_codes = [c.strip().upper() for c in country_csv.split(",")]

    orch = LlmOrchestrator(settings, llm_cfg, run_id=rid)
    summary = asyncio.run(
        orch.run(
            tier=tier,
            site_ids=site_ids,
            country_codes=country_codes,
            dry_run=dry_run,
        )
    )
    click.echo(json.dumps(summary.to_dict(), indent=2, default=str))
