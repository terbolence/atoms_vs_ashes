# man_hours: 0.5
"""Click CLI for :mod:`export.export_databases`.

Split out of the main module so the orchestrator stays under the repo's
300-line Python file-size cap. Only handles argument parsing, summary
file generation, and top-level side effects — actual export work lives
in :func:`export.export_databases.export_database`.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import click


def _write_summary(
    summary_path: Path,
    *,
    version: str,
    output_base: Path,
    clear_names: bool,
    results: dict[str, Path | None],
) -> None:
    with open(summary_path, "w") as f:
        f.write("Database Export Summary\n")
        f.write("======================\n\n")
        f.write(f"Version: {version}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"Export directory: {output_base}\n")
        f.write(f"Clear naming: {'Yes' if clear_names else 'No'}\n\n")
        if clear_names:
            f.write("Naming Convention:\n")
            f.write("Format: [PHASE]_[CATEGORY]_[CRITERION]_[MEASURE]_[UNIT]\n")
            f.write(
                "- PHASE: EXCL=Exclusionary, AVOID=Avoidance, "
                "RANK=Ranking, FILTER=Basic Filter\n"
            )
            f.write(
                "- CATEGORY: NH=Natural Hazard, HI=Human Hazard, "
                "RI=Radiological, EP=Emergency Planning, NS=Non-Safety\n"
            )
            f.write(
                "- MEASURE: VALUE=Raw data, QUALITY=Assessment quality, "
                "COMMENT=Detailed notes\n\n"
            )
        f.write("Export Results:\n")
        for db_name, result_path in results.items():
            if result_path and result_path.exists():
                size_mb = result_path.stat().st_size / (1024 * 1024)
                f.write(
                    f"✓ {db_name.upper()} database: {result_path} "
                    f"({size_mb:.1f} MB)\n"
                )
            else:
                f.write(f"✗ {db_name.upper()} database: failed\n")
        if clear_names and any(results.values()):
            f.write("\nNote: Excel files with clear naming include 'Column Mappings' sheet\n")
            f.write("showing the mapping between original and descriptive column names.\n")


@click.command()
@click.option("--version", "-v", default=None,
              help="Version string for the export folder (default: YYYYMMDD_HHMM)")
@click.option("--output-dir", "-o", type=click.Path(), default=None,
              help="Base output directory (default: export/exports_YYYYMMDD_HHMM)")
@click.option("--clear-names", "-c", is_flag=True, default=False,
              help="Use clear, descriptive column names for external stakeholders")
@click.option("--database", "-d",
              type=click.Choice(["both", "all", "api", "llm", "merged"]),
              default="both",
              help=(
                  "Which database(s) to export. `both` = api+llm (legacy default); "
                  "`all` = api+llm+merged; `api`/`llm`/`merged` = single DB."
              ))
def main(
    version: str | None, output_dir: str | None, clear_names: bool, database: str
) -> None:
    """Comprehensive database export orchestrator."""
    # Late import so module load stays cheap for anyone importing the
    # CLI for testing / help text.
    from export.export_databases import export_database, _repo_root

    if version is None:
        version = datetime.now().strftime("%Y%m%d_%H%M")
    if output_dir is None:
        root = _repo_root()
        suffix = "_clear" if clear_names else ""
        output_base = root / "export" / f"exports{suffix}_{version}"
    else:
        output_base = Path(output_dir)

    click.echo("Database Export Configuration")
    click.echo("============================")
    click.echo(f"Version: {version}")
    click.echo(f"Output directory: {output_base}")
    click.echo(f"Databases: {database}")
    click.echo(f"Clear naming: {'Yes' if clear_names else 'No'}")
    if clear_names:
        click.echo("Naming format: [PHASE]_[CATEGORY]_[CRITERION]_[MEASURE]_[UNIT]")
    click.echo()

    results: dict[str, Path | None] = {}
    suffix = "_clear" if clear_names else ""
    if database in ("both", "all", "api"):
        results["api"] = export_database(
            "api", output_base / "api" / f"atoms_vs_ashes_api{suffix}.xlsx",
            clear_names,
        )
    if database in ("both", "all", "llm"):
        results["llm"] = export_database(
            "llm", output_base / "llm" / f"atoms_vs_ashes_llm{suffix}.xlsx",
            clear_names,
        )
    if database in ("all", "merged"):
        results["merged"] = export_database(
            "merged",
            output_base / "merged" / f"atoms_vs_ashes_merged{suffix}.xlsx",
            clear_names,
        )

    summary_path = output_base / "export_summary.txt"
    _write_summary(
        summary_path,
        version=version,
        output_base=output_base,
        clear_names=clear_names,
        results=results,
    )
    click.echo("\nExport complete.")
    click.echo(f"Summary written to: {summary_path}")
    xlsx_files = list(output_base.rglob("*.xlsx"))
    if xlsx_files:
        click.echo("\nCreated files:")
        for xlsx_file in xlsx_files:
            size_mb = xlsx_file.stat().st_size / (1024 * 1024)
            rel_path = xlsx_file.relative_to(output_base)
            click.echo(f"  {rel_path} ({size_mb:.1f} MB)")
    successful = sum(1 for r in results.values() if r is not None)
    total = len(results)
    if successful == total:
        click.echo(f"\nAll {total} database(s) exported successfully.")
    else:
        click.echo(f"\n{successful}/{total} database(s) exported successfully.")
