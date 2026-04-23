# man_hours: 6.0
"""CLI entry point — ``python -m atoms_vs_ashes`` or ``atoms-vs-ashes``."""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

import click
from dotenv import load_dotenv

load_dotenv()

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
    "merged": "atoms_vs_ashes_merged",
}


@click.group()
@click.option("--config", "config_path", type=click.Path(exists=True), default=None,
              help="Path to YAML config file (defaults to config/default.yml).")
@click.option("--verbose", is_flag=True, default=False, help="Enable DEBUG logging.")
@click.option("--run-id", default=None, help="Explicit run ID (auto-generated if omitted).")
@click.option("--db-profile", type=click.Choice(["api", "llm", "merged"]), default="api",
              show_default=True,
              help="Database profile: 'api' (default), 'llm', or 'merged'.")
@click.pass_context
def main(ctx: click.Context, config_path: str | None, verbose: bool,
         run_id: str | None, db_profile: str) -> None:
    """Atoms vs Ashes — SMR Siting Assessment CLI."""
    import os
    ctx.ensure_object(dict)
    load_dotenv(_resolve_root() / ".env", override=False)
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
        connector.enable_audit_log(rid)

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


@enrich.command("site-area")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate OSM/CORINE connectivity, don't persist.")
@click.pass_context
def enrich_site_area(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    dry_run: bool,
) -> None:
    """Fetch site area data (FIX-03: OSM + CORINE fallback) for sites."""
    from atoms_vs_ashes.analysis.site_area import SiteAreaEnricher
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    if not check_connection(settings):
        click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
        sys.exit(1)

    with SiteAreaEnricher(settings) as enricher:
        if dry_run:
            click.echo("Dry run — checking OSM/CORINE connectivity…")
            health = enricher.health_check()
            click.echo(f"OSM health: {'OK' if health['osm'] else 'FAILED'}")
            click.echo(f"CORINE health: {'OK' if health['corine'] else 'FAILED'}")
            if health["osm"]:
                from atoms_vs_ashes.connectors.osm import OverpassClient
                osm = OverpassClient(settings)
                result = osm.fetch_site_area(lat=44.32, lon=28.05)
                click.echo(json.dumps(result.to_dict(), indent=2, default=str))
                osm.close()
            return

        with session_scope() as session:
            ids = list(site_ids) if site_ids else None
            codes = list(country_codes) if country_codes else None

            if enrich_all_flag:
                batch = enricher.enrich_all(session, rid)
            elif ids:
                batch = enricher.enrich_batch(session, rid, site_ids=ids)
            elif codes:
                batch = enricher.enrich_batch(session, rid, country_codes=codes)
            else:
                click.echo(
                    "ERROR: Specify --site-id, --country, or --all.", err=True
                )
                sys.exit(1)

        click.echo(batch.summary_line())
        click.echo(json.dumps(batch.to_dict(), indent=2, default=str))


@enrich.command("egdi-geology")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate EGDI WFS connectivity, don't persist.")
@click.pass_context
def enrich_egdi_geology(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    dry_run: bool,
) -> None:
    """Fetch geological data (S-02: EGDI WFS) for sites."""
    from atoms_vs_ashes.connectors.egdi_geology import EgdiGeologyConnector
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    if not dry_run and not check_connection(settings):
        click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
        sys.exit(1)

    with EgdiGeologyConnector(settings) as connector:
        if dry_run:
            click.echo("Dry run — checking EGDI WFS connectivity…")
            ok = connector.health_check()
            click.echo(f"EGDI WFS health check: {'OK' if ok else 'FAILED'}")
            if ok:
                result = connector.fetch_all(lat=44.15, lon=23.12, country_code="RO")
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


@enrich.command("soilgrids")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--requery-nulls", is_flag=True, default=False,
              help="Only re-query sites where soil_type is NULL.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate SoilGrids WCS connectivity, don't persist.")
@click.pass_context
def enrich_soilgrids(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    requery_nulls: bool,
    dry_run: bool,
) -> None:
    """Fetch soil properties (S-21: SoilGrids WCS) for sites."""
    from atoms_vs_ashes.connectors.soilgrids import SoilGridsConnector
    from atoms_vs_ashes.connectors.soilgrids.batch import enrich_batch
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    if not dry_run and not check_connection(settings):
        click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
        sys.exit(1)

    with SoilGridsConnector(settings) as connector:
        if dry_run:
            click.echo("Dry run — checking SoilGrids WCS connectivity…")
            ok = connector.health_check()
            click.echo(f"SoilGrids WCS health check: {'OK' if ok else 'FAILED'}")
            if ok:
                result = connector.fetch(lat=45.79, lon=25.59)
                click.echo(json.dumps(result.to_dict(), indent=2, default=str))
            return

        with session_scope() as session:
            ids = list(site_ids) if site_ids else None
            codes = list(country_codes) if country_codes else None

            if enrich_all_flag:
                batch = enrich_batch(connector, session, rid, requery_nulls=requery_nulls)
            elif ids:
                batch = enrich_batch(connector, session, rid, site_ids=ids)
            elif codes:
                batch = enrich_batch(connector, session, rid, country_codes=codes)
            else:
                click.echo(
                    "ERROR: Specify --site-id, --country, or --all.", err=True
                )
                sys.exit(1)

        click.echo(batch.summary_line())
        click.echo(json.dumps(batch.to_dict(), indent=2, default=str))


@enrich.command("bedrock")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--requery-nulls", is_flag=True, default=False,
              help="Only re-query sites where depth_to_bedrock_m is NULL.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate BDTICM raster connectivity, don't persist.")
@click.pass_context
def enrich_bedrock(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    requery_nulls: bool,
    dry_run: bool,
) -> None:
    """Fetch depth-to-bedrock (S-23: BDTICM 250 m raster) for sites."""
    from atoms_vs_ashes.connectors.bdticm_bedrock import BdticmBedrockConnector
    from atoms_vs_ashes.connectors.bdticm_bedrock.batch import enrich_batch
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    if not dry_run and not check_connection(settings):
        click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
        sys.exit(1)

    with BdticmBedrockConnector(settings) as connector:
        if dry_run:
            click.echo("Dry run — checking BDTICM raster connectivity…")
            ok = connector.health_check()
            click.echo(f"BDTICM raster health check: {'OK' if ok else 'FAILED'}")
            if ok:
                result = connector.fetch(lat=45.79, lon=25.59)
                click.echo(json.dumps(result.to_dict(), indent=2, default=str))
            return

        with session_scope() as session:
            ids = list(site_ids) if site_ids else None
            codes = list(country_codes) if country_codes else None

            if enrich_all_flag:
                batch = enrich_batch(connector, session, rid, requery_nulls=requery_nulls)
            elif ids:
                batch = enrich_batch(connector, session, rid, site_ids=ids)
            elif codes:
                batch = enrich_batch(connector, session, rid, country_codes=codes)
            else:
                click.echo(
                    "ERROR: Specify --site-id, --country, or --all.", err=True
                )
                sys.exit(1)

        click.echo(batch.summary_line())
        click.echo(json.dumps(batch.to_dict(), indent=2, default=str))


@enrich.command("onegeology")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Check endpoint health and fetch one sample site, don't persist.")
@click.option("--run-id", "run_id_override", default=None,
              help="Override run ID (use same run ID as S-02 EGDI for coordination).")
@click.pass_context
def enrich_onegeology(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    dry_run: bool,
    run_id_override: str | None,
) -> None:
    """Fetch national geological survey data (S-03: OneGeology WFS) for sites.

    Supplements S-02 EGDI for NH-02 (faults) and NH-05 (karst) where EGDI
    coverage is insufficient.  Should be run after S-02 EGDI for the same run-id.
    """
    from atoms_vs_ashes.connectors.onegeology import OneGeologyConnector
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = run_id_override or ctx.obj["run_id"]

    with OneGeologyConnector(settings) as connector:
        if dry_run:
            click.echo("Dry run — checking OneGeology national survey endpoints…")
            health = connector.health_check()
            click.echo(f"Endpoint health: {health}")
            click.echo("\nSample fetch: RO (Bucharest area, NH-02 + NH-05)…")
            result = connector.fetch_all(
                lat=44.43, lon=26.10, country_code="RO",
                s02_nh02_quality=None, s02_nh05_quality=None,
            )
            click.echo(json.dumps(result.to_dict(), indent=2, default=str))
            return

        if not check_connection(settings):
            click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
            sys.exit(1)

        with session_scope() as session:
            ids = [uuid_val for uuid_val in site_ids] if site_ids else None
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


@enrich.command("natura2000")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate WFS connectivity with one sample fetch, don't persist.")
@click.pass_context
def enrich_natura2000(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    dry_run: bool,
) -> None:
    """Fetch Natura 2000 proximity data (S-14: EEA WFS) for sites."""
    from atoms_vs_ashes.connectors.natura2000 import Natura2000Connector
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    if not dry_run and not check_connection(settings):
        click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
        sys.exit(1)

    with Natura2000Connector(settings) as connector:
        if dry_run:
            click.echo("Dry run — checking EEA Natura 2000 WFS connectivity…")
            ok = connector.health_check()
            click.echo(f"Natura 2000 WFS health check: {'OK' if ok else 'FAILED'}")
            if ok:
                result = connector.fetch(lat=44.43, lon=26.10, country_code="RO")
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


@enrich.command("wdpa")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--ingest", "ingest_flag", is_flag=True, default=False,
              help="Run country ingestion before enrichment.")
@click.option("--bulk", "bulk_flag", is_flag=True, default=False,
              help="Use bulk shapefile download (no API token required).")
@click.option("--dry-run", is_flag=True, default=False,
              help="Ingest 1 country and test enrichment, don't persist.")
@click.pass_context
def enrich_wdpa(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    ingest_flag: bool,
    bulk_flag: bool,
    dry_run: bool,
) -> None:
    """Fetch WDPA protected area proximity data (S-15) for sites."""
    from atoms_vs_ashes.connectors.wdpa import WdpaConnector
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    if not dry_run and not check_connection(settings):
        click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
        sys.exit(1)

    with WdpaConnector(settings) as connector:
        if dry_run:
            if bulk_flag:
                click.echo("Dry run (bulk) — downloading Montenegro (MNE) as sample…")
                index, summary = connector.ingest_country_from_bulk("MNE")
                click.echo(
                    f"  Fetched {summary.areas_fetched} areas, "
                    f"{summary.areas_after_filter} after filter, "
                    f"{summary.n_ramsar} Ramsar sites "
                    f"({summary.elapsed_s:.1f}s)"
                )
            else:
                click.echo("Dry run — checking WDPA API connectivity…")
                ok = connector.health_check()
                click.echo(f"WDPA API health check: {'OK' if ok else 'FAILED'}")
                if ok:
                    click.echo("Ingesting Ukraine (UKR) as sample…")
                    index, summary = connector.ingest_country("UKR")
                    click.echo(
                        f"  Fetched {summary.areas_fetched} areas, "
                        f"{summary.areas_after_filter} after filter, "
                        f"{summary.n_ramsar} Ramsar sites"
                    )
                else:
                    click.echo("No API token — trying bulk download fallback…")
                    index, summary = connector.ingest_country_from_bulk("MNE")
                    click.echo(
                        f"  Bulk: {summary.areas_fetched} areas, "
                        f"{summary.areas_after_filter} after filter "
                        f"({summary.elapsed_s:.1f}s)"
                    )

            result = connector.fetch(lat=42.28, lon=18.84, country_code="ME")
            click.echo(json.dumps(result.to_dict(), indent=2, default=str))
            return

        if ingest_flag or bulk_flag:
            if bulk_flag:
                click.echo("Ingesting all WDPA country data via bulk download…")
                ingestion = connector.ingest_all_countries_bulk()
            else:
                click.echo("Ingesting all WDPA country data via API…")
                ingestion = connector.ingest_all_countries()
            click.echo(
                f"Ingested {ingestion.total_areas_after_filter} PAs "
                f"across {ingestion.n_countries_with_data} countries "
                f"({ingestion.n_countries_failed} failed) "
                f"in {ingestion.elapsed_s:.0f}s"
            )

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


@enrich.command("ingest-wdpa")
@click.option("--country", "country_codes", multiple=True,
              help="Ingest specific countries (ISO3). Repeatable. Default: all 23.")
@click.option("--bulk", "bulk_flag", is_flag=True, default=False,
              help="Use bulk shapefile download instead of API (no token required).")
@click.option("--force", is_flag=True, default=False,
              help="Re-download even if cached data exists.")
@click.pass_context
def enrich_ingest_wdpa(
    ctx: click.Context,
    country_codes: tuple[str, ...],
    bulk_flag: bool,
    force: bool,
) -> None:
    """Download and cache WDPA protected area data for all in-scope countries."""
    from atoms_vs_ashes.connectors.wdpa import WdpaConnector

    settings: Settings = ctx.obj["settings"]

    with WdpaConnector(settings) as connector:
        if bulk_flag:
            if country_codes:
                for iso3 in country_codes:
                    click.echo(f"Downloading {iso3} shapefile…")
                    _, summary = connector.ingest_country_from_bulk(
                        iso3, force_download=force,
                    )
                    click.echo(
                        f"  {summary.areas_fetched} fetched → "
                        f"{summary.areas_after_filter} after filter "
                        f"({summary.elapsed_s:.1f}s)"
                    )
            else:
                click.echo("Downloading all 23 in-scope countries (bulk)…")
                result = connector.ingest_all_countries_bulk(force_download=force)
                click.echo(
                    f"Done: {result.total_areas_after_filter} PAs across "
                    f"{result.n_countries_with_data} countries, "
                    f"{result.n_countries_failed} failed "
                    f"({result.elapsed_s:.0f}s)"
                )
        else:
            ok = connector.health_check()
            if not ok:
                click.echo(
                    "WARNING: WDPA API health check failed. "
                    "Falling back to bulk shapefile download…",
                    err=True,
                )
                result = connector.ingest_all_countries_bulk(force_download=force)
                click.echo(
                    f"Done (bulk): {result.total_areas_after_filter} PAs across "
                    f"{result.n_countries_with_data} countries, "
                    f"{result.n_countries_failed} failed "
                    f"({result.elapsed_s:.0f}s)"
                )
                return

            if country_codes:
                for iso3 in country_codes:
                    click.echo(f"Ingesting {iso3}…")
                    _, summary = connector.ingest_country(iso3)
                    click.echo(
                        f"  {summary.areas_fetched} fetched → "
                        f"{summary.areas_after_filter} after filter "
                        f"({summary.elapsed_s:.1f}s)"
                    )
            else:
                click.echo("Ingesting all 23 in-scope countries…")
                result = connector.ingest_all_countries()
                click.echo(
                    f"Done: {result.total_areas_after_filter} PAs across "
                    f"{result.n_countries_with_data} countries, "
                    f"{result.n_countries_failed} failed "
                    f"({result.elapsed_s:.0f}s, {result.total_api_calls} API calls)"
                )


@enrich.command("download-ghsl-pop")
@click.option("--epoch", type=int, default=None,
              help="Population epoch year (default: 2020).")
@click.option("--tile", "tile_ids", multiple=True,
              help="Specific tile IDs to download (e.g. R4_C19). Omit for 1 km global file.")
@click.option("--force", is_flag=True, default=False,
              help="Re-download even if tiles already exist locally.")
@click.pass_context
def enrich_download_ghsl_pop(
    ctx: click.Context,
    epoch: int | None,
    tile_ids: tuple[str, ...],
    force: bool,
) -> None:
    """Download GHS-POP population grid tiles from JRC.

    Without --tile flags, downloads the 1 km global file (~300 MB).
    With --tile flags, downloads specific 100 m tiles (~100 MB each).
    """
    from atoms_vs_ashes.connectors.ghsl_pop import GhslPopConnector

    settings: Settings = ctx.obj["settings"]

    with GhslPopConnector(settings) as connector:
        if connector.raster_exists() and not force:
            tiles = connector.list_tiles(epoch)
            click.echo(f"GHSL tiles already cached at {connector.raster_dir} ({len(tiles)} files)")
            click.echo("Use --force to re-download.")
            return
        tids = list(tile_ids) if tile_ids else None
        click.echo(f"Downloading GHS-POP tiles to {connector.raster_dir} …")
        paths = connector.download(epoch=epoch, tile_ids=tids, force=force)
        for p in paths:
            click.echo(f"  Downloaded: {p}")
        click.echo(f"Download complete: {len(paths)} file(s)")


@enrich.command("ghsl-pop")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate raster connectivity, don't persist.")
@click.pass_context
def enrich_ghsl_pop(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    dry_run: bool,
) -> None:
    """Compute population density from GHSL GHS-POP (S-20) for sites."""
    from atoms_vs_ashes.connectors.ghsl_pop import GhslPopConnector
    from atoms_vs_ashes.connectors.ghsl_pop.batch import enrich_batch
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    with GhslPopConnector(settings) as connector:
        if dry_run:
            click.echo("Dry run — checking GHSL raster availability…")
            ok = connector.health_check()
            click.echo(f"GHSL health check: {'OK' if ok else 'FAILED'}")
            if ok:
                result = connector.fetch(lat=44.32, lon=28.05)
                click.echo(json.dumps(result.to_dict(), indent=2, default=str))
            return

        if not connector.raster_exists():
            click.echo(
                "ERROR: GHSL population raster not found. "
                "Run `atoms-vs-ashes enrich download-ghsl-pop` first.",
                err=True,
            )
            sys.exit(1)

        if not check_connection(settings):
            click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
            sys.exit(1)

        with session_scope() as session:
            ids = list(site_ids) if site_ids else None
            codes = list(country_codes) if country_codes else None

            if enrich_all_flag:
                batch = enrich_batch(connector, session, rid)
            elif ids:
                batch = enrich_batch(connector, session, rid, site_ids=ids)
            elif codes:
                batch = enrich_batch(connector, session, rid, country_codes=codes)
            else:
                click.echo(
                    "ERROR: Specify --site-id, --country, or --all.", err=True
                )
                sys.exit(1)

        click.echo(batch.summary_line())
        click.echo(json.dumps(batch.to_dict(), indent=2, default=str))


@enrich.command("download-eurostat-gisco")
@click.option("--force", is_flag=True, default=False,
              help="Re-download even if cached data exists.")
@click.pass_context
def enrich_download_eurostat_gisco(
    ctx: click.Context,
    force: bool,
) -> None:
    """Download Eurostat GISCO Urban Audit cities and population data.

    Downloads the Urban Audit Cities GeoJSON (~5 MB) from GISCO and
    city population data from the Eurostat statistics API (urb_cpop1).
    """
    from atoms_vs_ashes.connectors.eurostat_gisco import EurostatGiscoConnector

    settings: Settings = ctx.obj["settings"]

    with EurostatGiscoConnector(settings) as connector:
        if connector.data_loaded() and not force:
            click.echo(
                f"Eurostat GISCO data already cached at {connector.cache_dir}. "
                "Use --force to re-download."
            )
            return
        click.echo("Downloading Eurostat GISCO Urban Audit data…")
        count = connector.load_data(force=force)
        click.echo(f"Download complete: {count} cities loaded")


@enrich.command("eurostat-gisco")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate connectivity, don't persist.")
@click.pass_context
def enrich_eurostat_gisco(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    dry_run: bool,
) -> None:
    """Compute city proximity from Eurostat GISCO (S-16) for sites.

    Fills RI-05 (nearest city >50k, settlement hierarchy) using the
    Urban Audit 2021 city boundaries and Eurostat urb_cpop1 populations.
    """
    from atoms_vs_ashes.connectors.eurostat_gisco import EurostatGiscoConnector
    from atoms_vs_ashes.connectors.eurostat_gisco.batch import enrich_batch
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    with EurostatGiscoConnector(settings) as connector:
        if dry_run:
            click.echo("Dry run — checking Eurostat GISCO availability…")
            ok = connector.health_check()
            click.echo(f"GISCO health check: {'OK' if ok else 'FAILED'}")
            if ok:
                connector.load_data()
                result = connector.fetch(lat=44.32, lon=28.05)
                click.echo(json.dumps(result.to_dict(), indent=2, default=str))
            return

        connector.load_data()

        if not check_connection(settings):
            click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
            sys.exit(1)

        with session_scope() as session:
            ids = list(site_ids) if site_ids else None
            codes = list(country_codes) if country_codes else None

            if enrich_all_flag:
                batch = enrich_batch(connector, session, rid)
            elif ids:
                batch = enrich_batch(connector, session, rid, site_ids=ids)
            elif codes:
                batch = enrich_batch(connector, session, rid, country_codes=codes)
            else:
                click.echo(
                    "ERROR: Specify --site-id, --country, or --all.", err=True
                )
                sys.exit(1)

        click.echo(batch.summary_line())
        click.echo(json.dumps(batch.to_dict(), indent=2, default=str))


@enrich.command("ingest-eurostat-projections")
@click.option(
    "--year", default=2023, show_default=True,
    help="Statistics reference year for regional demographics/economics.",
)
@click.pass_context
def enrich_ingest_eurostat_projections(
    ctx: click.Context,
    year: int,
) -> None:
    """Ingest Eurostat EUROPOP2023/2019 projections and regional statistics.

    Phase A of the S-17 connector: downloads and caches national + regional
    population projections (EUROPOP2023/2019), demographic indicators,
    and regional socioeconomic statistics for all 12 EU in-scope countries.
    Also loads NSO supplement files from sources/nso_projections/.

    This is a prerequisite for 'enrich eurostat-projections'. Subsequent
    runs use the local cache (TTL: 365 days for projections, 90 for stats).
    """
    from atoms_vs_ashes.connectors.eurostat_projections import (
        EurostatProjectionsConnector,
    )

    settings: Settings = ctx.obj["settings"]

    with EurostatProjectionsConnector(settings) as connector:
        click.echo(f"Ingesting Eurostat projection data (reference year {year})…")
        result = connector.ingest_projections(reference_year=year)
        click.echo(
            f"Ingestion complete: {result.n_countries_with_projections} countries with "
            f"projections, {result.n_regions_with_data} NUTS3 regions, "
            f"{result.n_nso_supplements_loaded} NSO supplements "
            f"({result.elapsed_s:.1f} s)"
        )
        if result.errors:
            click.echo(f"Errors: {'; '.join(result.errors)}", err=True)


@enrich.command("eurostat-projections")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--ingest", "do_ingest", is_flag=True, default=False,
              help="Run Phase A (data ingestion) before enrichment.")
@click.option(
    "--year", default=2023, show_default=True,
    help="Statistics reference year (used only with --ingest).",
)
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate connectivity and query one country; do not persist.")
@click.pass_context
def enrich_eurostat_projections(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    do_ingest: bool,
    year: int,
    dry_run: bool,
) -> None:
    """Compute population projections and socioeconomic metrics (S-17).

    Fills RI-06 (population projections / receptor growth factor),
    NS-09 (socioeconomic impact), NS-10 (workforce), NS-12 (nuclear policy
    proxy) using Eurostat EUROPOP2023/2019 and curated NSO supplements.

    Run 'enrich ingest-eurostat-projections' first to populate the cache.
    Or use --ingest to run Phase A automatically before enriching.
    """
    from atoms_vs_ashes.connectors.eurostat_projections import (
        EurostatProjectionsConnector,
    )
    from atoms_vs_ashes.connectors.eurostat_projections.batch import enrich_batch
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    with EurostatProjectionsConnector(settings) as connector:
        if dry_run:
            click.echo("Dry run — checking Eurostat Statistics API availability…")
            ok = connector.health_check()
            click.echo(f"API health check: {'OK' if ok else 'FAILED'}")
            if ok:
                click.echo("Running ingestion (Phase A) for dry-run sample…")
                ingestion = connector.ingest_projections(reference_year=year)
                click.echo(
                    f"Loaded: {ingestion.n_countries_with_projections} countries, "
                    f"{ingestion.n_nso_supplements_loaded} NSO supplements"
                )
                result = connector.fetch(lat=44.15, lon=23.12, country_code="RO")
                click.echo(json.dumps(result.to_dict(), indent=2, default=str))
            return

        if do_ingest:
            click.echo(f"Phase A: ingesting projection data (year={year})…")
            ingestion = connector.ingest_projections(reference_year=year)
            click.echo(
                f"Ingestion done: {ingestion.n_countries_with_projections} countries, "
                f"{ingestion.n_nso_supplements_loaded} NSO supplements"
            )

        if not check_connection(settings):
            click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
            sys.exit(1)

        with session_scope() as session:
            ids = [uuid.UUID(str(s)) for s in site_ids] if site_ids else None
            codes = list(country_codes) if country_codes else None

            if enrich_all_flag:
                batch = enrich_batch(connector, session, rid)
            elif ids:
                batch = enrich_batch(connector, session, rid, site_ids=ids)
            elif codes:
                batch = enrich_batch(connector, session, rid, country_codes=codes)
            else:
                click.echo(
                    "ERROR: Specify --site-id, --country, or --all.", err=True
                )
                sys.exit(1)

        click.echo(batch.summary_line())
        click.echo(json.dumps(batch.to_dict(), indent=2, default=str))


@enrich.command("download-geonames-cities")
@click.option("--force", is_flag=True, default=False,
              help="Re-download / re-extract even if cache exists.")
@click.pass_context
def enrich_download_geonames_cities(
    ctx: click.Context,
    force: bool,
) -> None:
    """Download GeoNames cities5000.zip and extract TSV (global gazetteer).

    Used for RI-05 nearest city (population ≥ threshold) without the GeoNames API.
    """
    from atoms_vs_ashes.connectors.geonames_dump import GeonamesDumpConnector

    settings: Settings = ctx.obj["settings"]
    with GeonamesDumpConnector(settings) as connector:
        if connector.txt_path().is_file() and not force:
            click.echo(
                f"GeoNames dump already at {connector.txt_path()}. Use --force to refresh."
            )
            n = connector.load_cities()
            click.echo(f"Loaded {n} cities (population ≥ filter, class P).")
            return
        click.echo("Downloading GeoNames cities5000 …")
        connector.ensure_local_data(force=force)
        n = connector.load_cities(force=False)
        click.echo(f"Ready: {n} cities after filter.")


@enrich.command("geonames-ri05")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option(
    "--overwrite-ri05", is_flag=True, default=False,
    help="Write GeoNames into main RI-05 columns even when already filled (e.g. GISCO).",
)
@click.option("--dry-run", is_flag=True, default=False,
              help="Load dump and print one sample lookup; do not touch the database.")
@click.pass_context
def enrich_geonames_ri05(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    overwrite_ri05: bool,
    dry_run: bool,
) -> None:
    """Nearest city from GeoNames cities5000 dump for RI-05.

    Always merges ``ri05_nearest_50k_geonames`` into ``sites.extended_data``.
    Main ``site_radiological`` RI-05 columns are filled only when empty, unless
    ``--overwrite-ri05``.
    """
    from atoms_vs_ashes.connectors.geonames_dump import GeonamesDumpConnector
    from atoms_vs_ashes.connectors.geonames_dump.batch import enrich_batch
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    with GeonamesDumpConnector(settings) as connector:
        if not connector.txt_path().is_file():
            click.echo(
                "ERROR: GeoNames TSV missing. Run "
                "`atoms-vs-ashes enrich download-geonames-cities` first.",
                err=True,
            )
            sys.exit(1)

        connector.load_cities()

        if dry_run:
            from dataclasses import asdict

            click.echo("Dry run — sample nearest to (44.32, 28.05):")
            n = connector.nearest_for(44.32, 28.05)
            click.echo(json.dumps(asdict(n) if n else None, indent=2, default=str))
            return

        if not check_connection(settings):
            click.echo("ERROR: Cannot connect to database.", err=True)
            sys.exit(1)

        with session_scope() as session:
            ids = list(site_ids) if site_ids else None
            codes = list(country_codes) if country_codes else None
            if enrich_all_flag:
                batch = enrich_batch(
                    connector, session, rid, overwrite_ri05=overwrite_ri05,
                )
            elif ids:
                batch = enrich_batch(
                    connector, session, rid,
                    site_ids=ids, overwrite_ri05=overwrite_ri05,
                )
            elif codes:
                batch = enrich_batch(
                    connector, session, rid,
                    country_codes=codes, overwrite_ri05=overwrite_ri05,
                )
            else:
                click.echo(
                    "ERROR: Specify --site-id, --country, or --all.", err=True,
                )
                sys.exit(1)

        click.echo(batch.summary_line())
        click.echo(json.dumps(batch.to_dict(), indent=2, default=str))


@enrich.command("download-dem")
@click.option("--lat", type=float, default=None,
              help="Download tiles for a specific site latitude.")
@click.option("--lon", type=float, default=None,
              help="Download tiles for a specific site longitude.")
@click.option("--tile-id", "tile_ids", multiple=True,
              help="Specific tile IDs to download. Repeatable.")
@click.option("--force", is_flag=True, default=False,
              help="Re-download even if tiles already exist locally.")
@click.pass_context
def enrich_download_dem(
    ctx: click.Context,
    lat: float | None,
    lon: float | None,
    tile_ids: tuple[str, ...],
    force: bool,
) -> None:
    """Download Copernicus DEM GLO-30 COG tiles for local caching.

    Without --lat/--lon or --tile-id, prints usage instructions.
    With --lat and --lon, downloads all tiles covering the 5 km buffer.
    With --tile-id, downloads specific tiles by ID.
    """
    from atoms_vs_ashes.connectors.copernicus_dem import CopernicusDemConnector
    from atoms_vs_ashes.connectors.copernicus_dem.models import tile_id_for_point

    settings: Settings = ctx.obj["settings"]

    with CopernicusDemConnector(settings) as connector:
        if tile_ids:
            for tid in tile_ids:
                click.echo(f"Downloading tile {tid} …")
                path = connector.download_tile(tid, force=force)
                click.echo(f"  → {path}")
        elif lat is not None and lon is not None:
            click.echo(f"Downloading DEM tiles for ({lat}, {lon}) …")
            paths = connector.download_tiles_for_site(lat, lon, force=force)
            for p in paths:
                click.echo(f"  → {p}")
            click.echo(f"Download complete: {len(paths)} tile(s)")
        else:
            click.echo(
                "Specify --lat/--lon for a site, or --tile-id for specific tiles.\n"
                "Example: atoms-vs-ashes enrich download-dem --lat 45.27 --lon 27.96",
                err=True,
            )
            sys.exit(1)


@enrich.command("copernicus-dem")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate COG tile access, don't persist.")
@click.pass_context
def enrich_copernicus_dem(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    dry_run: bool,
) -> None:
    """Compute terrain metrics from Copernicus DEM GLO-30 (S-19) for sites."""
    from atoms_vs_ashes.connectors.copernicus_dem import CopernicusDemConnector
    from atoms_vs_ashes.connectors.copernicus_dem.batch import enrich_batch
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    with CopernicusDemConnector(settings) as connector:
        if dry_run:
            click.echo("Dry run — checking Copernicus DEM COG access…")
            ok = connector.health_check()
            click.echo(f"DEM health check: {'OK' if ok else 'FAILED'}")
            if ok:
                result = connector.fetch(lat=45.27, lon=27.96)
                click.echo(json.dumps(result.to_dict(), indent=2, default=str))
            return

        if not check_connection(settings):
            click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
            sys.exit(1)

        with session_scope() as session:
            ids = list(site_ids) if site_ids else None
            codes = list(country_codes) if country_codes else None

            if enrich_all_flag:
                batch = enrich_batch(connector, session, rid)
            elif ids:
                batch = enrich_batch(connector, session, rid, site_ids=ids)
            elif codes:
                batch = enrich_batch(connector, session, rid, country_codes=codes)
            else:
                click.echo(
                    "ERROR: Specify --site-id, --country, or --all.", err=True
                )
                sys.exit(1)

        click.echo(batch.summary_line())
        click.echo(json.dumps(batch.to_dict(), indent=2, default=str))


@enrich.command("download-liquefaction")
@click.option("--force", is_flag=True, default=False,
              help="Re-download even if the raster already exists locally.")
@click.pass_context
def enrich_download_liquefaction(ctx: click.Context, force: bool) -> None:
    """Download the Zhu global liquefaction susceptibility GeoTIFF (~442 MB)."""
    from atoms_vs_ashes.connectors.zhu_liquefaction import ZhuLiquefactionConnector

    settings: Settings = ctx.obj["settings"]

    with ZhuLiquefactionConnector(settings) as connector:
        if connector.raster_exists() and not force:
            click.echo(f"Raster already cached at {connector.raster_path}")
            click.echo("Use --force to re-download.")
            return
        click.echo(f"Downloading Zhu liquefaction GeoTIFF to {connector.raster_path} …")
        path = connector.download(force=force)
        click.echo(f"Download complete: {path}")


@enrich.command("liquefaction")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate raster connectivity, don't persist.")
@click.pass_context
def enrich_liquefaction(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    dry_run: bool,
) -> None:
    """Fetch liquefaction susceptibility (S-22: Zhu GeoTIFF) for sites."""
    from atoms_vs_ashes.connectors.zhu_liquefaction import ZhuLiquefactionConnector
    from atoms_vs_ashes.connectors.zhu_liquefaction.batch import enrich_batch
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    with ZhuLiquefactionConnector(settings) as connector:
        if dry_run:
            click.echo("Dry run — checking Zhu raster availability…")
            ok = connector.health_check()
            click.echo(f"Raster health check: {'OK' if ok else 'FAILED'}")
            if ok:
                result = connector.fetch(lat=44.32, lon=28.05)
                click.echo(json.dumps(result.to_dict(), indent=2, default=str))
            return

        if not connector.raster_exists():
            click.echo(
                "ERROR: Liquefaction raster not found. "
                "Run `atoms-vs-ashes enrich download-liquefaction` first.",
                err=True,
            )
            sys.exit(1)

        if not check_connection(settings):
            click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
            sys.exit(1)

        with session_scope() as session:
            ids = list(site_ids) if site_ids else None
            codes = list(country_codes) if country_codes else None

            if enrich_all_flag:
                batch = enrich_batch(connector, session, rid)
            elif ids:
                batch = enrich_batch(connector, session, rid, site_ids=ids)
            elif codes:
                batch = enrich_batch(connector, session, rid, country_codes=codes)
            else:
                click.echo(
                    "ERROR: Specify --site-id, --country, or --all.", err=True
                )
                sys.exit(1)

        click.echo(batch.summary_line())
        click.echo(json.dumps(batch.to_dict(), indent=2, default=str))


@enrich.command("download-efsm20")
@click.option("--force", is_flag=True, default=False,
              help="Re-download even if GeoJSON data already exists locally.")
@click.pass_context
def enrich_download_efsm20(ctx: click.Context, force: bool) -> None:
    """Download EFSM20 fault GeoJSON from seismofaults.eu/GeoServer (~50 MB)."""
    from atoms_vs_ashes.connectors.efsm20_faults import Efsm20FaultsConnector

    settings: Settings = ctx.obj["settings"]

    with Efsm20FaultsConnector(settings) as connector:
        if connector.data_exists() and not force:
            files = connector._find_geojson_files()
            click.echo(f"EFSM20 GeoJSON already cached in {connector.data_dir} ({len(files)} file(s))")
            click.echo("Use --force to re-download.")
            return
        click.echo(f"Downloading EFSM20 fault data to {connector.data_dir} …")
        files = connector.download(force=force)
        click.echo(f"Download complete: {len(files)} GeoJSON file(s)")
        for f in files:
            click.echo(f"  {f}")


@enrich.command("efsm20-faults")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate GeoJSON availability, don't persist.")
@click.pass_context
def enrich_efsm20_faults(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    dry_run: bool,
) -> None:
    """Fetch seismogenic fault proximity (S-18: EFSM20) for sites → NH-02."""
    from atoms_vs_ashes.connectors.efsm20_faults import Efsm20FaultsConnector
    from atoms_vs_ashes.connectors.efsm20_faults.batch import enrich_batch
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    with Efsm20FaultsConnector(settings) as connector:
        if dry_run:
            click.echo("Dry run — checking EFSM20 GeoJSON availability…")
            ok = connector.health_check()
            click.echo(f"EFSM20 health check: {'OK' if ok else 'FAILED'}")
            if ok:
                result = connector.fetch(lat=45.70, lon=26.50)
                click.echo(json.dumps(result.to_dict(), indent=2, default=str))
            return

        if not connector.data_exists():
            click.echo(
                "ERROR: EFSM20 GeoJSON data not found. "
                "Run `atoms-vs-ashes enrich download-efsm20` first.",
                err=True,
            )
            sys.exit(1)

        if not check_connection(settings):
            click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
            sys.exit(1)

        with session_scope() as session:
            ids = list(site_ids) if site_ids else None
            codes = list(country_codes) if country_codes else None

            if enrich_all_flag:
                batch = enrich_batch(connector, session, rid)
            elif ids:
                batch = enrich_batch(connector, session, rid, site_ids=ids)
            elif codes:
                batch = enrich_batch(connector, session, rid, country_codes=codes)
            else:
                click.echo(
                    "ERROR: Specify --site-id, --country, or --all.", err=True
                )
                sys.exit(1)

        click.echo(batch.summary_line())
        click.echo(json.dumps(batch.to_dict(), indent=2, default=str))


@enrich.command("download-karst")
@click.option("--force", is_flag=True, default=False,
              help="Re-download even if the shapefile already exists locally.")
@click.pass_context
def enrich_download_karst(ctx: click.Context, force: bool) -> None:
    """Download the WOKAM World Karst Aquifer Map shapefile (~21 MB)."""
    from atoms_vs_ashes.connectors.wokam_karst import WokamKarstConnector

    settings: Settings = ctx.obj["settings"]

    with WokamKarstConnector(settings) as connector:
        if connector.data_exists() and not force:
            click.echo(f"WOKAM shapefile already cached in {connector.data_dir}")
            click.echo("Use --force to re-download.")
            return
        click.echo(f"Downloading WOKAM karst shapefile to {connector.data_dir} …")
        path = connector.download(force=force)
        click.echo(f"Download complete: {path}")


@enrich.command("karst")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate shapefile connectivity, don't persist.")
@click.pass_context
def enrich_karst(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    dry_run: bool,
) -> None:
    """Fetch karst occurrence (S-25: WOKAM shapefile) for sites."""
    from atoms_vs_ashes.connectors.wokam_karst import WokamKarstConnector
    from atoms_vs_ashes.connectors.wokam_karst.batch import enrich_batch
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    with WokamKarstConnector(settings) as connector:
        if dry_run:
            click.echo("Dry run — checking WOKAM shapefile availability…")
            ok = connector.health_check()
            click.echo(f"Shapefile health check: {'OK' if ok else 'FAILED'}")
            if ok:
                result = connector.fetch(lat=44.43, lon=26.10)
                click.echo(json.dumps(result.to_dict(), indent=2, default=str))
            return

        if not connector.data_exists():
            click.echo(
                "ERROR: WOKAM shapefile not found. "
                "Run `atoms-vs-ashes enrich download-karst` first.",
                err=True,
            )
            sys.exit(1)

        if not check_connection(settings):
            click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
            sys.exit(1)

        with session_scope() as session:
            ids = list(site_ids) if site_ids else None
            codes = list(country_codes) if country_codes else None

            if enrich_all_flag:
                batch = enrich_batch(connector, session, rid)
            elif ids:
                batch = enrich_batch(connector, session, rid, site_ids=ids)
            elif codes:
                batch = enrich_batch(connector, session, rid, country_codes=codes)
            else:
                click.echo(
                    "ERROR: Specify --site-id, --country, or --all.", err=True
                )
                sys.exit(1)

        click.echo(batch.summary_line())
        click.echo(json.dumps(batch.to_dict(), indent=2, default=str))


@enrich.command("smithsonian-gvp")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate GVP WFS connectivity, don't persist.")
@click.pass_context
def enrich_smithsonian_gvp(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    dry_run: bool,
) -> None:
    """Fetch volcanic hazard data (S-07: Smithsonian GVP VOTW) for sites."""
    from atoms_vs_ashes.connectors.smithsonian_gvp import SmithsonianGvpConnector
    from atoms_vs_ashes.connectors.smithsonian_gvp.batch import enrich_batch
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    with SmithsonianGvpConnector(settings) as connector:
        if dry_run:
            click.echo("Dry run — checking GVP WFS connectivity…")
            ok = connector.health_check()
            click.echo(f"GVP WFS health check: {'OK' if ok else 'FAILED'}")
            if ok:
                result = connector.fetch(lat=44.43, lon=26.10)
                click.echo(json.dumps(result.to_dict(), indent=2, default=str))
            return

        if not check_connection(settings):
            click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
            sys.exit(1)

        with session_scope() as session:
            ids = list(site_ids) if site_ids else None
            codes = list(country_codes) if country_codes else None

            if enrich_all_flag:
                batch = enrich_batch(connector, session, rid)
            elif ids:
                batch = enrich_batch(connector, session, rid, site_ids=ids)
            elif codes:
                batch = enrich_batch(connector, session, rid, country_codes=codes)
            else:
                click.echo(
                    "ERROR: Specify --site-id, --country, or --all.", err=True
                )
                sys.exit(1)

        click.echo(batch.summary_line())
        click.echo(json.dumps(batch.to_dict(), indent=2, default=str))


@enrich.command("eu-flood-risk")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate JRC/EEA connectivity, don't persist.")
@click.option("--download-only", is_flag=True, default=False,
              help="Download GloFAS tiles and APSFR GeoPackage without enriching.")
@click.pass_context
def enrich_eu_flood_risk(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    dry_run: bool,
    download_only: bool,
) -> None:
    """Fetch flood risk data (S-08: JRC/GloFAS + EEA APSFR) for sites."""
    from atoms_vs_ashes.connectors.eu_flood_risk import EuFloodRiskConnector
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    with EuFloodRiskConnector(settings) as connector:
        if dry_run:
            click.echo("Dry run — checking JRC/EEA connectivity…")
            ok = connector.health_check()
            click.echo(f"JRC tile extents health check: {'OK' if ok else 'FAILED'}")
            if ok:
                result = connector.fetch(lat=44.43, lon=26.10, country_code="RO")
                click.echo(json.dumps(result.to_dict(), indent=2, default=str))
            return

        if download_only:
            click.echo("Download-only mode — caching GloFAS tiles…")
            connector._ensure_tile_index()
            click.echo(f"Tile index loaded: {len(connector._tile_index or [])} tiles")
            return

        if not check_connection(settings):
            click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
            sys.exit(1)

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


@enrich.command("ingest-gfms")
@click.option("--start-year", type=int, default=None,
              help="Override analysis start year (default from config: 2005).")
@click.option("--end-year", type=int, default=None,
              help="Override analysis end year (default from config: 2025).")
@click.option("--force", is_flag=True, default=False,
              help="Ignore statistics cache and re-download / recompute.")
@click.pass_context
def enrich_ingest_gfms(
    ctx: click.Context,
    start_year: int | None,
    end_year: int | None,
    force: bool,
) -> None:
    """Phase A: Download GFMS binary grids and compute flood statistics.

    Downloads ~1,040 files (~5-13 GB) for 20 years at weekly resolution
    from eagle2.umd.edu. Subsequent runs skip already-cached files.
    Results cached as compressed numpy in sources/gfms/stats/.

    IMPORTANT: This command makes real HTTP downloads from eagle2.umd.edu
    (University of Maryland research server). Requires explicit user consent
    per live-api-safety policy. Each file is ~13 MB; weekly sampling over
    20 years = ~1,040 files.
    """
    from atoms_vs_ashes.connectors.gfms import GfmsConnector

    settings: Settings = ctx.obj["settings"]

    with GfmsConnector(settings) as connector:
        if force and connector.stats_cached():
            connector._stats_path.unlink(missing_ok=True)
            click.echo("Cleared statistics cache — will re-download and recompute.")

        click.echo(
            f"Starting GFMS archive ingestion "
            f"({start_year or connector._analysis_start}–"
            f"{end_year or connector._analysis_end}, "
            f"{connector._temporal_sampling} sampling)…"
        )
        stats = connector.ingest_archive(start_year=start_year, end_year=end_year)
        click.echo(
            f"Ingestion complete: {stats.n_snapshots} snapshots processed, "
            f"{stats.n_years:.0f} years analysed, "
            f"max intensity {float(stats.max_intensity.max()):.0f} mm."
        )


@enrich.command("gfms")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--ingest", "ingest_flag", is_flag=True, default=False,
              help="Run Phase A archive ingestion before enrichment.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Check data server connectivity and list available files without downloading.")
@click.option("--run-id", "run_id_override", type=str, default=None,
              help="Resume a previous batch run (skips already-enriched sites).")
@click.pass_context
def enrich_gfms(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    ingest_flag: bool,
    dry_run: bool,
    run_id_override: str | None,
) -> None:
    """Phase B: Fetch GFMS flood frequency data (S-09) for sites.

    Samples pre-computed statistics from the local cache — no HTTP per site.
    Run `enrich ingest-gfms` first to build the statistics cache, or use
    --ingest to do both in one command.
    """
    from atoms_vs_ashes.connectors.gfms import GfmsConnector
    from atoms_vs_ashes.connectors.gfms.batch import enrich_batch
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = run_id_override or ctx.obj["run_id"]

    with GfmsConnector(settings) as connector:
        if dry_run:
            click.echo("Dry run — checking GFMS data server connectivity…")
            ok = connector.health_check()
            click.echo(f"eagle2.umd.edu health check: {'OK' if ok else 'FAILED'}")
            if connector.stats_cached():
                click.echo(f"Statistics cache: EXISTS at {connector._stats_path}")
                connector._ensure_stats_loaded()
                if connector._stats:
                    s = connector._stats
                    click.echo(
                        f"  Snapshots: {s.n_snapshots}, Years: {s.n_years:.0f}, "
                        f"Period: {s.start_year}–{s.end_year}"
                    )
                    sample = connector.fetch(lat=44.43, lon=26.10)
                    click.echo("Sample site (Bucharest area, 44.43N 26.10E):")
                    click.echo(json.dumps(sample.to_dict(), indent=2, default=str))
            else:
                click.echo(
                    "Statistics cache: MISSING. "
                    "Run `enrich ingest-gfms` to build it."
                )
            return

        if ingest_flag:
            click.echo("Running Phase A (archive ingestion)…")
            stats = connector.ingest_archive()
            click.echo(
                f"Ingestion complete: {stats.n_snapshots} snapshots, "
                f"{stats.n_years:.0f} years."
            )
        elif not connector.stats_cached():
            click.echo(
                "ERROR: GFMS statistics cache not found. "
                "Run `atoms-vs-ashes enrich ingest-gfms` first, "
                "or use --ingest to run both phases.",
                err=True,
            )
            sys.exit(1)

        if not check_connection(settings):
            click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
            sys.exit(1)

        with session_scope() as session:
            ids = list(site_ids) if site_ids else None
            codes = list(country_codes) if country_codes else None

            if enrich_all_flag:
                batch = connector.enrich_all(session, rid)
            elif ids:
                batch = enrich_batch(connector, session, rid, site_ids=ids)
            elif codes:
                batch = enrich_batch(connector, session, rid, country_codes=codes)
            else:
                click.echo(
                    "ERROR: Specify --site-id, --country, --all, or --dry-run.", err=True
                )
                sys.exit(1)

        click.echo(batch.summary_line())
        click.echo(json.dumps(batch.to_dict(), indent=2, default=str))


@enrich.command("ingest-era5")
@click.option("--dataset", "dataset",
              type=click.Choice(["monthly-means", "era5-land", "cmip6", "all"]),
              default="all",
              help="Which dataset to download (default: all).")
@click.option("--skip-cmip6", is_flag=True, default=False,
              help="Skip the CMIP6 projection download (optional, slower).")
@click.pass_context
def enrich_ingest_era5(
    ctx: click.Context,
    dataset: str,
    skip_cmip6: bool,
) -> None:
    """Tier 1: Download ERA5 NetCDF data from Copernicus CDS (S-04).

    Downloads ERA5 reanalysis monthly means (~1-5 GB) from the Copernicus
    Climate Data Store to sources/era5/. Must be run once before
    'enrich era5' (Tier 2) can process any sites.

    IMPORTANT: This command makes live HTTP requests to cds.climate.copernicus.eu.
    CDS uses an async request queue — downloads may take 10-60 minutes each.
    Requires a free CDS account and personal access token in ~/.cdsapirc
    or CDSAPI_KEY environment variable. Dataset licences must be accepted
    via the CDS web UI first.

    Subsequent runs skip fresh files (within cache_ttl_days = 90 days).
    """
    from atoms_vs_ashes.connectors.copernicus_era5 import CopernicusEra5Connector

    settings: Settings = ctx.obj["settings"]

    with CopernicusEra5Connector(settings) as connector:
        status = connector.check_local_data()
        click.echo("Current local data status:")
        for name, info in status.items():
            flag = "PRESENT" if info["present"] else "MISSING"
            stale = " (STALE)" if info.get("stale") and info["present"] else ""
            click.echo(
                f"  {name}: {flag}{stale}"
                + (f" — {info['size_mb']:.0f} MB, {info['age_days']:.0f} days old"
                   if info["present"] else "")
            )

        click.echo("")
        click.echo(f"Starting ERA5 download (dataset={dataset})…")
        click.echo(
            "NOTE: CDS queue times vary (minutes to hours). "
            "Progress is logged to the console."
        )

        try:
            if dataset == "monthly-means":
                path = connector.download_monthly_means()
                click.echo(f"Downloaded monthly means: {path}")
            elif dataset == "era5-land":
                path = connector.download_era5_land()
                click.echo(f"Downloaded ERA5-Land: {path}")
            elif dataset == "cmip6":
                path = connector.download_cmip6()
                click.echo(f"Downloaded CMIP6: {path}")
            else:
                downloaded = connector.download_all(skip_cmip6=skip_cmip6)
                click.echo("Download complete:")
                for name, path in downloaded.items():
                    size = path.stat().st_size / 1_048_576 if path.is_file() else 0
                    click.echo(f"  {name}: {path} ({size:.0f} MB)")
        except RuntimeError as exc:
            click.echo(f"ERROR: {exc}", err=True)
            import sys
            sys.exit(1)


@enrich.command("era5")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Check local data status and sample one site without persisting.")
@click.option("--check-data", is_flag=True, default=False,
              help="Show status of local ERA5 NetCDF files and exit.")
@click.option("--run-id", "run_id_override", type=str, default=None,
              help="Resume a previous batch run (skips already-enriched sites).")
@click.pass_context
def enrich_era5(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    dry_run: bool,
    check_data: bool,
    run_id_override: str | None,
) -> None:
    """Tier 2: Extract ERA5 climate data (S-04) for sites from local NetCDF files.

    Reads pre-downloaded ERA5 NetCDF files from sources/era5/ and computes
    per-site climate metrics (wind rose, GEV extremes, SPI drought, Pasquill
    stability, CMIP6 warming) with no CDS API calls. Local computation only.

    Run 'enrich ingest-era5' first to download ERA5 data. Enriches:
      NH-10 (wind extremes), NH-11 (precipitation/snow/drought),
      NH-12 (temperature extremes), RI-01 (atmospheric dispersion),
      NS-01 (seasonality proxy), EP-02 (seasonal constraints proxy).
    """
    from atoms_vs_ashes.connectors.copernicus_era5 import CopernicusEra5Connector
    from atoms_vs_ashes.connectors.copernicus_era5.batch import enrich_batch
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = run_id_override or ctx.obj["run_id"]

    with CopernicusEra5Connector(settings) as connector:
        if check_data or dry_run:
            status = connector.check_local_data()
            click.echo("ERA5 local data status:")
            for name, info in status.items():
                flag = "✓" if info["present"] and not info["stale"] else (
                    "STALE" if info["present"] else "MISSING"
                )
                click.echo(
                    f"  {name}: {flag}"
                    + (f" — {info['size_mb']:.0f} MB, "
                       f"{info['age_days']:.0f} days old (TTL={info['ttl_days']}d)"
                       if info["present"] else "")
                )

            if not connector.has_required_data():
                click.echo(
                    "\nERROR: Monthly means file missing. "
                    "Run 'atoms-vs-ashes enrich ingest-era5' first.",
                    err=True,
                )
                if check_data:
                    return
            elif dry_run:
                click.echo("\nDry run — opening datasets and extracting sample site…")
                try:
                    connector._open_datasets()
                    sample = connector.extract_all(lat=44.43, lon=26.10)
                    click.echo("Sample site (Bucharest area, 44.43°N 26.10°E):")
                    click.echo(json.dumps(sample.to_dict(), indent=2, default=str))
                    click.echo(
                        f"\nSummary: quality={sample.quality}, "
                        f"grid_dist={sample.grid_distance_km:.1f}km, "
                        f"max_temp={sample.temperature.max_temp_record_c:.1f}°C, "
                        f"prevailing={sample.wind.prevailing_direction_deg:.0f}°"
                    )
                except RuntimeError as exc:
                    click.echo(f"ERROR: {exc}", err=True)
            return

        if not connector.has_required_data():
            click.echo(
                "ERROR: ERA5 monthly means file not found. "
                "Run 'atoms-vs-ashes enrich ingest-era5' first to download ERA5 data.",
                err=True,
            )
            import sys
            sys.exit(1)

        if not check_connection(settings):
            click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
            import sys
            sys.exit(1)

        with session_scope() as session:
            ids = list(site_ids) if site_ids else None
            codes = list(country_codes) if country_codes else None

            if enrich_all_flag:
                batch = connector.enrich_all(session, rid)
            elif ids:
                batch = enrich_batch(connector, session, rid, site_ids=ids)
            elif codes:
                batch = enrich_batch(connector, session, rid, country_codes=codes)
            else:
                click.echo(
                    "ERROR: Specify --site-id, --country, --all, --dry-run, "
                    "or --check-data.",
                    err=True,
                )
                import sys
                sys.exit(1)

        click.echo(batch.summary_line())
        click.echo(json.dumps(batch.to_dict(), indent=2, default=str))


@enrich.command("copernicus-ems")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate CEMS API connectivity, don't persist.")
@click.option("--ingest", "ingest_flag", is_flag=True, default=False,
              help="Run catalogue ingestion before enrichment.")
@click.pass_context
def enrich_copernicus_ems(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    dry_run: bool,
    ingest_flag: bool,
) -> None:
    """Fetch flash flood data (S-10: Copernicus EMS RRM + Rapid Mapping) for sites."""
    from atoms_vs_ashes.connectors.copernicus_ems import CopernicusEmsConnector
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    with CopernicusEmsConnector(settings) as connector:
        if dry_run:
            click.echo("Dry run — checking Copernicus EMS API connectivity…")
            ok = connector.health_check()
            click.echo(f"CEMS RRM API health check: {'OK' if ok else 'FAILED'}")
            if ok:
                catalogue = connector.ingest_catalogue(rid)
                click.echo(json.dumps(catalogue.to_dict(), indent=2, default=str))
                result = connector.assess_site(lat=44.43, lon=26.10)
                click.echo(json.dumps(result.to_dict(), indent=2, default=str))
            return

        click.echo("Ingesting Copernicus EMS catalogue…")
        catalogue = connector.ingest_catalogue(rid)
        click.echo(
            f"Catalogue: {catalogue.n_rrm_fetched} RRM + "
            f"{catalogue.n_rapid_fetched} Rapid activations, "
            f"{catalogue.n_footprints_total} centroids"
        )

        if not (enrich_all_flag or site_ids or country_codes):
            if not ingest_flag:
                click.echo(
                    "ERROR: Specify --site-id, --country, --all, or --ingest.", err=True
                )
                sys.exit(1)
            click.echo("Catalogue ingestion complete (no site enrichment requested).")
            return

        if not check_connection(settings):
            click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
            sys.exit(1)

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


@enrich.command("download-eea-industrial")
@click.option("--force", is_flag=True, default=False,
              help="Re-download even if the CSV already exists locally.")
@click.pass_context
def enrich_download_eea_industrial(ctx: click.Context, force: bool) -> None:
    """Download the EEA E-PRTR facility dataset CSV (~5–10 MB)."""
    from atoms_vs_ashes.connectors.eea_industrial import EeaIndustrialConnector

    settings: Settings = ctx.obj["settings"]

    with EeaIndustrialConnector(settings) as connector:
        if connector.data_exists() and not force:
            click.echo(f"EEA facility CSV already cached at {connector.csv_path}")
            click.echo("Use --force to re-download.")
            return
        click.echo(f"Downloading EEA E-PRTR facility CSV to {connector.cache_dir} …")
        path = connector.download(force=force)
        click.echo(f"Download complete: {path}")


@enrich.command("eea-industrial")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate CSV availability, don't persist.")
@click.pass_context
def enrich_eea_industrial(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    dry_run: bool,
) -> None:
    """Fetch industrial facility proximity (S-37: EEA E-PRTR) for sites."""
    from atoms_vs_ashes.connectors.eea_industrial import EeaIndustrialConnector
    from atoms_vs_ashes.connectors.eea_industrial.batch import enrich_batch
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    with EeaIndustrialConnector(settings) as connector:
        if dry_run:
            click.echo("Dry run — checking EEA facility CSV availability…")
            ok = connector.health_check()
            click.echo(f"EEA facility CSV health check: {'OK' if ok else 'FAILED'}")
            if ok:
                result = connector.fetch(lat=44.43, lon=26.10, country_code="RO")
                click.echo(json.dumps(result.to_dict(), indent=2, default=str))
            return

        if not connector.data_exists():
            click.echo(
                "ERROR: EEA facility CSV not found. "
                "Run `atoms-vs-ashes enrich download-eea-industrial` first.",
                err=True,
            )
            sys.exit(1)

        if not check_connection(settings):
            click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
            sys.exit(1)

        with session_scope() as session:
            ids = list(site_ids) if site_ids else None
            codes = list(country_codes) if country_codes else None

            if enrich_all_flag:
                batch = enrich_batch(connector, session, rid)
            elif ids:
                batch = enrich_batch(connector, session, rid, site_ids=ids)
            elif codes:
                batch = enrich_batch(connector, session, rid, country_codes=codes)
            else:
                click.echo(
                    "ERROR: Specify --site-id, --country, or --all.", err=True
                )
                sys.exit(1)

        click.echo(batch.summary_line())
        click.echo(json.dumps(batch.to_dict(), indent=2, default=str))


@enrich.command("entso-e")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate ENTSO-E API token only; no zone ingest or DB writes.")
@click.option(
    "--year", "reference_year", type=int, default=None,
    help="Bidding-zone reference year (default: connectors.entso_e.reference_year in config).",
)
@click.pass_context
def enrich_entso_e(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    dry_run: bool,
    reference_year: int | None,
) -> None:
    """Fetch ENTSO-E zone grid capacity (S-13) for NS-02.

    Loads ``ENTSOE_SECURITY_TOKEN`` from the environment (e.g. ``.env`` via
    dotenv) when YAML ``security_token`` is unset.

    Zone ingestion runs first (uses on-disk cache when fresh), then each
    site is matched to its bidding zone and persisted to ``SiteInfrastructureV2``.
    """
    from atoms_vs_ashes.connectors.entso_e import EntsoEConnector
    from atoms_vs_ashes.connectors.entso_e.batch import enrich_batch
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    with EntsoEConnector(settings) as connector:
        connector.enable_audit_log(rid)
        if dry_run:
            click.echo("Dry run — checking ENTSO-E API token…")
            ok = connector.health_check()
            click.echo(f"ENTSO-E health check: {'OK' if ok else 'FAILED'}")
            return

        if not check_connection(settings):
            click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
            sys.exit(1)

        year = reference_year
        if year is None:
            year = int(
                settings._yaml.get("connectors", {})
                .get("entso_e", {})
                .get("reference_year", 2025),
            )
        click.echo(f"Loading bidding-zone assessments (year {year})…")
        zone_result = connector.ingest_zones(year=year)
        click.echo(
            f"Zones: {zone_result.n_zones_queried} queried, "
            f"{zone_result.n_zones_with_data} with data, "
            f"{zone_result.n_zones_no_data} no/insufficient data "
            f"({zone_result.elapsed_s:.1f}s)",
        )

        with session_scope() as session:
            ids = list(site_ids) if site_ids else None
            codes = list(country_codes) if country_codes else None

            if enrich_all_flag:
                batch = enrich_batch(connector, session, rid)
            elif ids:
                batch = enrich_batch(connector, session, rid, site_ids=ids)
            elif codes:
                batch = enrich_batch(connector, session, rid, country_codes=codes)
            else:
                click.echo(
                    "ERROR: Specify --site-id, --country, or --all.", err=True
                )
                sys.exit(1)

        click.echo(batch.summary_line())
        click.echo(json.dumps(batch.to_dict(), indent=2, default=str))


@enrich.command("earth-engine")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option(
    "--mode", "mode_override", type=click.Choice(["fallback", "standalone"]),
    default=None,
    help="Override connectors.earth_engine.mode for this run.",
)
@click.option(
    "--module", "module_flags", multiple=True,
    type=click.Choice(["terrain", "fire", "built_up"]),
    help="Limit to module(s). Repeatable. Default: all enabled in config.",
)
@click.option("--dry-run", is_flag=True, default=False,
              help="Initialize Earth Engine and run health_check only (no DB writes).")
@click.pass_context
def enrich_earth_engine(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    mode_override: str | None,
    module_flags: tuple[str, ...],
    dry_run: bool,
) -> None:
    """Google Earth Engine enrichment (S-06) — NH-04, NH-13, NS-04, NS-06, EP-03."""
    import json as _json

    from atoms_vs_ashes.connectors.earth_engine import EarthEngineConnector
    from atoms_vs_ashes.connectors.earth_engine.batch import enrich_batch
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]
    ee_cfg = settings._yaml.get("connectors", {}).get("earth_engine", {})
    delay_s = float(ee_cfg.get("inter_request_delay_s", 1.0))
    mods_cfg = ee_cfg.get("modules") or {}
    modules: dict[str, bool] = {
        "terrain": bool((mods_cfg.get("terrain") or {}).get("enabled", True)),
        "fire": bool((mods_cfg.get("fire") or {}).get("enabled", True)),
        "built_up": bool((mods_cfg.get("built_up") or {}).get("enabled", True)),
    }
    if module_flags:
        for k in modules:
            modules[k] = k in module_flags

    with EarthEngineConnector(settings, mode_override=mode_override) as connector:
        if not connector.enabled:
            click.echo(
                "Google Earth Engine is disabled (connectors.earth_engine.enabled: false). "
                "Terrain and related data use Copernicus DEM and other non-GEE connectors.",
                err=True,
            )
            click.echo(
                "To opt in after Google approval: set enabled: true, "
                "pip install 'atoms-vs-ashes[earth-engine]', configure GEE credentials, then re-run.",
                err=True,
            )
            sys.exit(0 if dry_run else 1)

        if dry_run:
            click.echo("Dry run — Earth Engine health check…")
            ok = connector.health_check()
            click.echo(f"Earth Engine health check: {'OK' if ok else 'FAILED'}")
            return

        if not check_connection(settings):
            click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
            sys.exit(1)

        with session_scope() as session:
            ids = list(site_ids) if site_ids else None
            codes = list(country_codes) if country_codes else None

            if enrich_all_flag:
                batch = enrich_batch(
                    connector, session, rid, settings=settings,
                    modules=modules, inter_request_delay_s=delay_s,
                )
            elif ids:
                batch = enrich_batch(
                    connector, session, rid, site_ids=ids, settings=settings,
                    modules=modules, inter_request_delay_s=delay_s,
                )
            elif codes:
                batch = enrich_batch(
                    connector, session, rid, country_codes=codes, settings=settings,
                    modules=modules, inter_request_delay_s=delay_s,
                )
            else:
                click.echo(
                    "ERROR: Specify --site-id, --country, or --all.", err=True,
                )
                sys.exit(1)

        click.echo(batch.summary_line())
        click.echo(_json.dumps(batch.to_dict(), indent=2, default=str))


@enrich.command("seveso")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate data file availability, don't persist.")
@click.option("--build-index", is_flag=True, default=False,
              help="Build/refresh the facility database without enriching sites.")
@click.pass_context
def enrich_seveso(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    dry_run: bool,
    build_index: bool,
) -> None:
    """Fetch SEVESO III facility proximity (S-12: E-PRTR + Minerva + national) for sites."""
    from atoms_vs_ashes.connectors.seveso import SevesoConnector
    from atoms_vs_ashes.connectors.seveso.batch import enrich_batch
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    with SevesoConnector(settings) as connector:
        if dry_run:
            click.echo("Dry run — checking SEVESO data file availability…")
            click.echo(f"  EEA E-PRTR CSV: {'found' if connector._eea.data_exists() else 'MISSING'}")
            click.echo(f"  Minerva CSV: {'found' if connector.minerva_exists() else 'MISSING'}")
            national = connector.national_files_available()
            click.echo(f"  National files: {national if national else 'none'}")
            ok = connector.health_check()
            click.echo(f"SEVESO health check: {'OK' if ok else 'FAILED'}")
            if ok:
                result = connector.fetch(lat=44.43, lon=26.10, country_code="RO")
                click.echo(json.dumps(result.to_dict(), indent=2, default=str))
            return

        if build_index:
            click.echo("Building SEVESO facility index…")
            stats = connector.build_facility_index()
            click.echo(json.dumps(stats.to_dict(), indent=2, default=str))
            if not (enrich_all_flag or site_ids or country_codes):
                return

        if not connector._eea.data_exists() and not connector.minerva_exists():
            click.echo(
                "ERROR: No SEVESO data files found. "
                "Download E-PRTR CSV (`enrich download-eea-industrial`) "
                "and/or place Minerva CSV at the configured path.",
                err=True,
            )
            sys.exit(1)

        if not check_connection(settings):
            click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
            sys.exit(1)

        with session_scope() as session:
            ids = list(site_ids) if site_ids else None
            codes = list(country_codes) if country_codes else None

            if enrich_all_flag:
                batch = enrich_batch(connector, session, rid)
            elif ids:
                batch = enrich_batch(connector, session, rid, site_ids=ids)
            elif codes:
                batch = enrich_batch(connector, session, rid, country_codes=codes)
            else:
                click.echo(
                    "ERROR: Specify --site-id, --country, --all, or --build-index.", err=True
                )
                sys.exit(1)

        click.echo(batch.summary_line())
        click.echo(json.dumps(batch.to_dict(), indent=2, default=str))


# ── S-29 HydroRIVERS (river network) ────────────────────────────────

@enrich.command("download-hydrorivers")
@click.option("--force", is_flag=True, default=False,
              help="Re-download even if shapefiles already exist locally.")
@click.option("--region", "regions", multiple=True, default=["eu", "as"],
              help="Regional shapefile(s) to download. Repeatable. Default: eu, as.")
@click.pass_context
def enrich_download_hydrorivers(ctx: click.Context, force: bool, regions: tuple[str, ...]) -> None:
    """Download HydroRIVERS v10 regional shapefiles (~150 MB each)."""
    from atoms_vs_ashes.connectors.hydrorivers import HydroRiversConnector

    settings: Settings = ctx.obj["settings"]

    with HydroRiversConnector(settings) as connector:
        if connector.data_exists() and not force:
            click.echo(f"HydroRIVERS data already cached in {connector.data_dir}")
            click.echo("Use --force to re-download.")
            return
        click.echo(f"Downloading HydroRIVERS to {connector.data_dir} …")
        paths = connector.download(force=force, regions=list(regions))
        click.echo(f"Download complete: {len(paths)} shapefile(s)")
        for p in paths:
            click.echo(f"  {p}")


@enrich.command("hydrorivers")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate data availability, don't persist.")
@click.pass_context
def enrich_hydrorivers(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    dry_run: bool,
) -> None:
    """Fetch nearest river (S-29: HydroRIVERS) for sites → NS-01 cooling water."""
    from atoms_vs_ashes.connectors.hydrorivers import HydroRiversConnector
    from atoms_vs_ashes.connectors.hydrorivers.batch import enrich_batch
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    with HydroRiversConnector(settings) as connector:
        if dry_run:
            click.echo("Dry run — checking HydroRIVERS data availability…")
            ok = connector.health_check()
            click.echo(f"Data health check: {'OK' if ok else 'FAILED'}")
            if ok:
                result = connector.fetch(lat=44.43, lon=26.10)
                click.echo(json.dumps(result.to_dict(), indent=2, default=str))
            return

        if not connector.data_exists():
            click.echo(
                "ERROR: HydroRIVERS data not found. "
                "Run `atoms-vs-ashes enrich download-hydrorivers` first.",
                err=True,
            )
            sys.exit(1)

        if not check_connection(settings):
            click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
            sys.exit(1)

        with session_scope() as session:
            ids = list(site_ids) if site_ids else None
            codes = list(country_codes) if country_codes else None

            if enrich_all_flag:
                batch = enrich_batch(connector, session, rid)
            elif ids:
                batch = enrich_batch(connector, session, rid, site_ids=ids)
            elif codes:
                batch = enrich_batch(connector, session, rid, country_codes=codes)
            else:
                click.echo(
                    "ERROR: Specify --site-id, --country, or --all.", err=True
                )
                sys.exit(1)

        click.echo(batch.summary_line())
        click.echo(json.dumps(batch.to_dict(), indent=2, default=str))


# ── S-33 WRI Aqueduct (water stress) ────────────────────────────────

@enrich.command("download-aqueduct")
@click.option("--force", is_flag=True, default=False,
              help="Re-download even if the data already exists locally.")
@click.pass_context
def enrich_download_aqueduct(ctx: click.Context, force: bool) -> None:
    """Download WRI Aqueduct 4.0 water stress dataset (~400 MB)."""
    from atoms_vs_ashes.connectors.wri_aqueduct import WriAqueductConnector

    settings: Settings = ctx.obj["settings"]

    with WriAqueductConnector(settings) as connector:
        if connector.data_exists() and not force:
            click.echo(f"WRI Aqueduct data already cached in {connector.data_dir}")
            click.echo("Use --force to re-download.")
            return
        click.echo(f"Downloading WRI Aqueduct data to {connector.data_dir} …")
        path = connector.download(force=force)
        click.echo(f"Download complete: {path}")


@enrich.command("water-stress")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate data availability, don't persist.")
@click.pass_context
def enrich_water_stress(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    dry_run: bool,
) -> None:
    """Fetch water stress (S-33: WRI Aqueduct 4.0) for sites → NS-01."""
    from atoms_vs_ashes.connectors.wri_aqueduct import WriAqueductConnector
    from atoms_vs_ashes.connectors.wri_aqueduct.batch import enrich_batch
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    with WriAqueductConnector(settings) as connector:
        if dry_run:
            click.echo("Dry run — checking WRI Aqueduct data availability…")
            ok = connector.health_check()
            click.echo(f"Data health check: {'OK' if ok else 'FAILED'}")
            if ok:
                result = connector.fetch(lat=44.43, lon=26.10)
                click.echo(json.dumps(result.to_dict(), indent=2, default=str))
            return

        if not connector.data_exists():
            click.echo(
                "ERROR: WRI Aqueduct data not found. "
                "Run `atoms-vs-ashes enrich download-aqueduct` first.",
                err=True,
            )
            sys.exit(1)

        if not check_connection(settings):
            click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
            sys.exit(1)

        with session_scope() as session:
            ids = list(site_ids) if site_ids else None
            codes = list(country_codes) if country_codes else None

            if enrich_all_flag:
                batch = enrich_batch(connector, session, rid)
            elif ids:
                batch = enrich_batch(connector, session, rid, site_ids=ids)
            elif codes:
                batch = enrich_batch(connector, session, rid, country_codes=codes)
            else:
                click.echo(
                    "ERROR: Specify --site-id, --country, or --all.", err=True
                )
                sys.exit(1)

        click.echo(batch.summary_line())
        click.echo(json.dumps(batch.to_dict(), indent=2, default=str))


# ── S-30 GloFAS discharge (CDS API) ─────────────────────────────────

@enrich.command("download-glofas")
@click.option("--force", is_flag=True, default=False,
              help="Re-download even if cached NetCDF files exist.")
@click.pass_context
def enrich_download_glofas(ctx: click.Context, force: bool) -> None:
    """Download GloFAS v4 discharge reanalysis data via CDS API.

    Requires a CDS API key configured in ~/.cdsapirc or CDS_API_KEY env var.
    """
    from atoms_vs_ashes.connectors.glofas_discharge import GlofasDischargeConnector

    settings: Settings = ctx.obj["settings"]

    with GlofasDischargeConnector(settings) as connector:
        if connector.data_exists() and not force:
            click.echo(f"GloFAS data already cached in {connector.cache_dir}")
            click.echo("Use --force to re-download.")
            return
        click.echo(f"Submitting CDS API request for GloFAS discharge data…")
        click.echo("This may take several minutes (CDS queue processing).")
        path = connector.download_region(force=force)
        click.echo(f"Download complete: {path}")


@enrich.command("glofas-discharge")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate CDS API credentials, don't persist.")
@click.pass_context
def enrich_glofas_discharge(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    dry_run: bool,
) -> None:
    """Fetch river discharge (S-30: GloFAS v4 reanalysis) for sites → NS-01."""
    from atoms_vs_ashes.connectors.glofas_discharge import GlofasDischargeConnector
    from atoms_vs_ashes.connectors.glofas_discharge.batch import enrich_batch
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    with GlofasDischargeConnector(settings) as connector:
        if dry_run:
            click.echo("Dry run — checking GloFAS/CDS API availability…")
            ok = connector.health_check()
            click.echo(f"CDS API health check: {'OK' if ok else 'FAILED'}")
            if ok and connector.data_exists():
                result = connector.fetch(lat=44.43, lon=26.10)
                click.echo(json.dumps(result.to_dict(), indent=2, default=str))
            return

        if not connector.data_exists():
            click.echo(
                "ERROR: GloFAS NetCDF data not found. "
                "Run `atoms-vs-ashes enrich download-glofas` first.",
                err=True,
            )
            sys.exit(1)

        if not check_connection(settings):
            click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
            sys.exit(1)

        with session_scope() as session:
            ids = list(site_ids) if site_ids else None
            codes = list(country_codes) if country_codes else None

            if enrich_all_flag:
                batch = enrich_batch(connector, session, rid)
            elif ids:
                batch = enrich_batch(connector, session, rid, site_ids=ids)
            elif codes:
                batch = enrich_batch(connector, session, rid, country_codes=codes)
            else:
                click.echo(
                    "ERROR: Specify --site-id, --country, or --all.", err=True
                )
                sys.exit(1)

        click.echo(batch.summary_line())
        click.echo(json.dumps(batch.to_dict(), indent=2, default=str))


@enrich.command("noaa-ncei")
@click.option("--site-id", "site_ids", multiple=True, type=click.UUID,
              help="Enrich specific site(s) by UUID. Repeatable.")
@click.option("--country", "country_codes", multiple=True,
              help="Enrich all sites in country (ISO 3166-1 alpha-2). Repeatable.")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate CDO API token and IBTrACS, don't persist.")
@click.option("--run-id", "run_id_override", default=None,
              help="Override the run ID (for resuming interrupted batches).")
@click.pass_context
def enrich_noaa_ncei(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    dry_run: bool,
    run_id_override: str | None,
) -> None:
    """Fetch meteorological hazard data (S-11: NOAA NCEI) for sites → NH-10/11/12."""
    from atoms_vs_ashes.connectors.noaa_ncei import NoaaNceiConnector
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = run_id_override or ctx.obj["run_id"]

    with NoaaNceiConnector(settings) as connector:
        if dry_run:
            click.echo("Dry run — checking NOAA NCEI connectivity…")
            ok = connector.health_check()
            click.echo(f"CDO API health check: {'OK' if ok else 'FAILED (token missing or invalid)'}")
            if not ok:
                click.echo(
                    "TIP: Set NOAA_CDO_TOKEN env var or "
                    "connectors.noaa_ncei.cdo_api_token in config/default.yml",
                    err=True,
                )
            click.echo("Loading IBTrACS tropical cyclone archive…")
            connector._ensure_ibtracs_loaded()
            ibtracs_count = len(connector._ibtracs_tracks or [])
            click.echo(f"IBTrACS loaded: {ibtracs_count} track points in Euro-Mediterranean region")
            if ok:
                click.echo("Fetching sample site (Bucharest area)…")
                result = connector.fetch_all(lat=44.43, lon=26.10)
                click.echo(json.dumps(result.to_dict(), indent=2, default=str))
            return

        if not check_connection(settings):
            click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
            sys.exit(1)

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


@main.command("enrich-transport")
@click.option("--site-id", "site_ids", multiple=True,
              help="One or more site UUIDs. Omit for all sites.")
@click.option("--country", "country_codes", multiple=True,
              help="Filter by country code(s) (e.g. --country RO --country BG).")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Validate Overpass connectivity, don't persist.")
@click.pass_context
def enrich_transport(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    dry_run: bool,
) -> None:
    """Fetch OSM transport access (P11: highway, rail, waterway) for sites."""
    from atoms_vs_ashes.connectors.osm import OverpassClient
    from atoms_vs_ashes.connectors.osm.batch import enrich_batch
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    with OverpassClient(settings) as client:
        if dry_run:
            click.echo("Dry run — checking Overpass API connectivity…")
            ok = client.health_check()
            click.echo(f"Overpass health check: {'OK' if ok else 'FAILED'}")
            if ok:
                from atoms_vs_ashes.connectors.osm.batch import _fetch_transport
                result = _fetch_transport(client, 45.27, 27.96, country_code="RO")
                click.echo(json.dumps(result.to_dict(), indent=2, default=str))
            return

        if not check_connection(settings):
            click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
            sys.exit(1)

        with session_scope() as session:
            ids = list(site_ids) if site_ids else None
            codes = list(country_codes) if country_codes else None

            if enrich_all_flag:
                batch = enrich_batch(client, session, rid)
            elif ids:
                import uuid as _uuid
                uuids = [_uuid.UUID(s) for s in ids]
                batch = enrich_batch(client, session, rid, site_ids=uuids)
            elif codes:
                batch = enrich_batch(client, session, rid, country_codes=codes)
            else:
                click.echo(
                    "ERROR: Specify --site-id, --country, or --all.", err=True
                )
                sys.exit(1)

        click.echo(batch.summary_line())
        click.echo(json.dumps(batch.to_dict(), indent=2, default=str))


@main.command("enrich-ep-composite")
@click.option("--site-id", "site_ids", multiple=True,
              help="One or more site UUIDs. Omit for all sites.")
@click.option("--country", "country_codes", multiple=True,
              help="Filter by country code(s) (e.g. --country RO --country BG).")
@click.option("--all", "enrich_all_flag", is_flag=True, default=False,
              help="Enrich every site in the database.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Print what would be computed, don't persist.")
@click.pass_context
def enrich_ep_composite(
    ctx: click.Context,
    site_ids: tuple[str, ...],
    country_codes: tuple[str, ...],
    enrich_all_flag: bool,
    dry_run: bool,
) -> None:
    """DRV-02: Compute EP composite score from existing enrichment data.

    Combines OSM road density, GHSL population, Copernicus DEM terrain,
    and OSM waterway data into an EP-01 composite feasibility score.
    Also populates EP-02 (road metrics), EP-03 (geography), and EP-04
    (special populations) columns.

    Requires prior enrichment: ghsl-pop, copernicus-dem, and will call
    Overpass for road density / waterways / amenities within the EPZ.
    """
    from atoms_vs_ashes.analysis.emergency_plan import EmergencyPlanCheck
    from atoms_vs_ashes.db.engine import session_scope

    settings: Settings = ctx.obj["settings"]
    rid: str = ctx.obj["run_id"]

    if not check_connection(settings):
        click.echo("ERROR: Cannot connect to database. Is PostgreSQL running?", err=True)
        sys.exit(1)

    if not (enrich_all_flag or site_ids or country_codes):
        click.echo("ERROR: Specify --site-id, --country, or --all.", err=True)
        sys.exit(1)

    if dry_run:
        from sqlalchemy import select as sa_select

        from atoms_vs_ashes.db.models import Site, SiteNaturalHazards, SiteRadiological

        with session_scope() as session:
            q = sa_select(Site)
            if site_ids:
                q = q.filter(Site.site_id.in_(list(site_ids)))
            if country_codes:
                q = q.filter(Site.country_code.in_(list(country_codes)))
            sites = session.execute(q).scalars().all()

            click.echo(f"DRV-02 EP Composite — dry run for {len(sites)} site(s):")
            for s in sites:
                nh = session.get(SiteNaturalHazards, s.site_id)
                ri = session.get(SiteRadiological, s.site_id)
                has_dem = nh is not None and nh.slope_angle_deg is not None
                has_ghsl = ri is not None and ri.pop_total_5km is not None
                click.echo(
                    f"  {s.name} ({s.country_code}): "
                    f"DEM={'yes' if has_dem else 'MISSING'}, "
                    f"GHSL={'yes' if has_ghsl else 'MISSING'}"
                )
        return

    with session_scope() as session:
        check = EmergencyPlanCheck()
        summary = check.run(session, settings, rid)
        session.commit()

    click.echo(
        f"EP composite complete: "
        f"{summary.total} verdicts "
        f"({summary.passed} pass, {summary.failed} fail, "
        f"{summary.inconclusive} inconclusive)"
    )


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


from atoms_vs_ashes.scoring._cli import score_group as _score_group

main.add_command(_score_group)


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
@click.option("--skip-second-pass", is_flag=True, default=False,
              help="Skip the second-pass prompt entirely.")
@click.option("--auto-second-pass", is_flag=True, default=False,
              help="Automatically run second pass without asking.")
@click.option("--force-rerun", is_flag=True, default=False,
              help="Bypass DB dedup checks and re-run all criteria.")
@click.option("--all-at-once", is_flag=True, default=False,
              help="Use legacy all-at-once mode instead of sequential elimination for exclusionary tier.")
@click.option("--no-defer", is_flag=True, default=False,
              help="Force LLM assessment for criteria that would normally be deferred due to missing enrichment data.")
@click.pass_context
def llm_assess(
    ctx: click.Context,
    tier: str,
    site_csv: str | None,
    country_csv: str | None,
    dry_run: bool,
    max_concurrent: int | None,
    skip_second_pass: bool,
    auto_second_pass: bool,
    force_rerun: bool,
    all_at_once: bool,
    no_defer: bool,
) -> None:
    """Run LLM-based siting assessment (writes to atoms_vs_ashes_llm DB).

    For the exclusionary tier, the default mode is **sequential elimination**:
    criteria are assessed one at a time in priority order across all sites.
    Sites that fail are eliminated and receive 'not_assessed' for remaining
    criteria, saving API calls.  Use --all-at-once to revert to the legacy
    parallel mode.

    After the first pass, exclusionary criteria that returned
    verdict=inconclusive or confidence=low are identified as second-pass
    candidates.  You will be prompted to re-run them with Opus 4.6 for
    deeper reasoning (use --skip-second-pass or --auto-second-pass to
    control this non-interactively).
    """
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

    if force_rerun and not dry_run:
        click.echo("WARNING: --force-rerun will bypass DB dedup and re-run all criteria.")
        if not click.confirm("Proceed with force re-run?", default=False):
            click.echo("Aborted.")
            return

    use_sequential = (tier == "exclusionary") and not all_at_once

    if use_sequential:
        click.echo("=" * 60)
        click.echo("SEQUENTIAL ELIMINATION — exclusionary criteria in priority order")
        click.echo("=" * 60)

        summary = asyncio.run(
            orch.run_sequential_elimination(
                site_ids=site_ids,
                country_codes=country_codes,
                dry_run=dry_run,
                force_rerun=force_rerun,
                no_defer=no_defer,
            )
        )
        click.echo(json.dumps(summary.to_dict(), indent=2, default=str))

        if summary.excluded_sites:
            click.echo("")
            click.echo(f"ELIMINATED SITES ({len(summary.excluded_sites)}):")
            for e in summary.excluded_sites:
                click.echo(f"  {e.site_name}: failed {e.excluded_by_prompt_key} (phase {e.phase_number})")

        if summary.deferred_phases:
            click.echo("")
            click.echo(f"DEFERRED CRITERIA ({len(summary.deferred_phases)}):")
            for d in summary.deferred_phases:
                click.echo(
                    f"  {d['criterion']} ({d['criterion_id']}): {d['sites_deferred']} sites "
                    f"— {d['reason']}"
                )
                click.echo(f"    Required: {', '.join(d['required_sources'])}")

        if summary.api_calls_saved > 0:
            click.echo(f"\nAPI calls saved by elimination/deferral/algorithmic: {summary.api_calls_saved}")

        click.echo(f"Run quality grade: {summary.quality_grade}% medium+ confidence")

        if dry_run or skip_second_pass:
            return

        candidates = summary.second_pass_candidates
        if not candidates:
            click.echo("\nNo second-pass candidates — all exclusionary assessments resolved.")
            return

    else:
        click.echo("=" * 60)
        click.echo("FIRST PASS — Sonnet 4 (Tier 1 + thinking) / Haiku 3.5 (Tier 3)")
        click.echo("=" * 60)

        summary = asyncio.run(
            orch.run(
                tier=tier,
                site_ids=site_ids,
                country_codes=country_codes,
                dry_run=dry_run,
                force_rerun=force_rerun,
            )
        )
        click.echo(json.dumps(summary.to_dict(), indent=2, default=str))

        if dry_run or skip_second_pass:
            return

        candidates = summary.second_pass_candidates
        if not candidates:
            click.echo("\nNo second-pass candidates — all exclusionary assessments resolved.")
            return

    # --- Display second-pass candidates ---
    click.echo("")
    click.echo("=" * 60)
    click.echo(f"SECOND-PASS CANDIDATES: {len(candidates)} exclusionary assessment(s)")
    click.echo("=" * 60)
    click.echo(
        f"These Tier 1 assessments returned inconclusive/low-confidence "
        f"and can be re-evaluated with {llm_cfg.model_tier1_upgrade} "
        f"(deeper reasoning, higher cost)."
    )
    click.echo("")

    by_site: dict[str, list] = {}
    for c in candidates:
        by_site.setdefault(c.site_name, []).append(c)
    for site_name, site_cands in sorted(by_site.items()):
        click.echo(f"  {site_name}:")
        for c in site_cands:
            click.echo(f"    {c.prompt_key} ({c.criterion_id}): {c.reason}")

    est_calls = len(candidates)
    click.echo(f"\nEstimated second-pass API calls: {est_calls}")
    click.echo(
        f"Model: {llm_cfg.model_tier1_upgrade} "
        f"(thinking budget: {llm_cfg.tier1_upgrade_thinking_budget:,} tokens)"
    )

    if auto_second_pass:
        run_it = True
        click.echo("\n--auto-second-pass enabled, proceeding.")
    else:
        run_it = click.confirm(
            "\nRun second pass with Opus?",
            default=False,
        )

    if not run_it:
        click.echo("Second pass skipped.")
        return

    click.echo("")
    click.echo("=" * 60)
    click.echo("SECOND PASS — Opus 4.6 (extended thinking)")
    click.echo("=" * 60)

    second_summary = asyncio.run(orch.run_second_pass(candidates))
    click.echo(json.dumps(second_summary.to_dict(), indent=2, default=str))

    click.echo(
        f"\nSecond pass complete: {second_summary.succeeded} succeeded, "
        f"{second_summary.failed} failed out of {est_calls} candidates."
    )
