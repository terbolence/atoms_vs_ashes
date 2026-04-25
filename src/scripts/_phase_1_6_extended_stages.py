# man_hours: 1.5
"""Extended banding + national analysis orchestrator.

Runs scope-parameterised :mod:`_suite_banding` against every scope
the Phase 1.6 pipeline needs (global all-SMR, per-SMR, per-country,
per-country × NuScale), computes country summaries, and emits reports
and figures. Inputs come from existing ``composite_rankings`` rows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy.orm import Session

from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring._country_summary import (
    compute_country_summary,
    write_country_summary_csv,
)
from scripts._phase_1_6_figures_correlation import (
    CorrelationArtefacts,
    build_correlation_artefacts,
)
from scripts._phase_1_6_regional_report import write_regional_report
from scripts._phase_1_6_stage_helpers import (
    attach_band_counts,
    compute_country_bands,
    compute_regional_bands,
    countries_from_csv,
    make_country_figures,
    make_regional_figures,
    write_country_reports,
)

log = get_logger(__name__)

NUSCALE_KEY = "nuscale_voygr6"
SMR_KEYS: tuple[str, ...] = (
    "oklo_aurora",
    "xe_100",
    "bwrx_300",
    "holtec_smr300",
    "natrium_nominal",
    "nuscale_voygr6",
    "rolls_royce_smr",
    "natrium_peak",
)


@dataclass
class ExtendedStagesResult:
    regional_bands_csv: Path
    nuscale_bands_csv: Path
    per_smr_bands_csvs: dict[str, Path] = field(default_factory=dict)
    per_country_bands_csvs: dict[str, Path] = field(default_factory=dict)
    per_country_nuscale_bands_csvs: dict[str, Path] = field(default_factory=dict)
    country_summary_csv: Path | None = None
    country_summary_nuscale_csv: Path | None = None
    regional_report_md: Path | None = None
    country_report_mds: dict[str, Path] = field(default_factory=dict)
    figures: dict[str, Path] = field(default_factory=dict)
    correlation: CorrelationArtefacts | None = None


def run_extended_stages(
    session: Session,
    *,
    baseline_label: str,
    audit_dir: Path,
    report_dir: Path,
    stamp: str,
    generate_figures: bool = True,
) -> ExtendedStagesResult:
    """Run the full extended banding + country analysis pipeline."""
    regional, nuscale, per_smr = compute_regional_bands(
        session,
        baseline_label=baseline_label,
        audit_dir=audit_dir,
        nuscale_key=NUSCALE_KEY,
        smr_keys=SMR_KEYS,
        stamp=stamp,
    )
    countries = countries_from_csv(regional.csv_path)
    log.info(
        "extended_stages_regional_done",
        sites=regional.sites_total,
        countries=len(countries),
    )

    per_country_bands = compute_country_bands(
        session,
        baseline_label=baseline_label,
        audit_dir=audit_dir,
        countries=countries,
        smr_filter=None,
        stamp=stamp,
    )
    per_country_ns_bands = compute_country_bands(
        session,
        baseline_label=baseline_label,
        audit_dir=audit_dir,
        countries=countries,
        smr_filter=NUSCALE_KEY,
        stamp=stamp,
    )

    summary_rows = compute_country_summary(
        session, baseline_label=baseline_label
    )
    country_summary_csv = write_country_summary_csv(
        audit_dir,
        summary_rows,
        extra_columns=attach_band_counts(summary_rows, per_country_bands),
        stamp=stamp,
    )

    summary_rows_ns = compute_country_summary(
        session, baseline_label=baseline_label, smr_filter=NUSCALE_KEY
    )
    country_summary_ns_csv = write_country_summary_csv(
        audit_dir,
        summary_rows_ns,
        smr_filter=NUSCALE_KEY,
        extra_columns=attach_band_counts(summary_rows_ns, per_country_ns_bands),
        stamp=stamp,
    )

    figures: dict[str, Path] = {}
    per_country_figures: dict[str, Path] = {}
    correlation: CorrelationArtefacts | None = None
    if generate_figures:
        figures = make_regional_figures(
            regional.csv_path,
            nuscale.csv_path,
            report_dir / "figures",
        )
        per_country_figures = make_country_figures(
            per_country_bands, report_dir / "national" / "figures"
        )
        correlation = build_correlation_artefacts(
            session,
            audit_dir=audit_dir,
            figures_dir=report_dir / "figures" / "correlation",
            flagged_md_path=report_dir / "criterion_correlation.md",
            baseline_label=baseline_label,
            stamp=stamp,
        )

    regional_report = write_regional_report(
        out_dir=report_dir,
        stamp=stamp,
        bands_csv=regional.csv_path,
        nuscale_bands_csv=nuscale.csv_path,
        country_summary_csv=country_summary_csv,
        figures_rel={
            key: f"figures/{path.name}" for key, path in figures.items()
        },
    )

    country_reports = write_country_reports(
        report_dir / "national",
        stamp,
        per_country_bands,
        per_country_ns_bands,
        per_country_figures,
    )

    log.info(
        "extended_stages_complete",
        countries=len(countries),
        country_reports=len(country_reports),
        per_smr_scopes=len(per_smr),
    )

    figures_out: dict[str, Path] = {
        **figures,
        **{
            f"country_{k}": v for k, v in per_country_figures.items()
        },
    }
    if correlation is not None:
        figures_out["correlation_pearson"] = correlation.pearson_png
        figures_out["correlation_spearman"] = correlation.spearman_png

    return ExtendedStagesResult(
        regional_bands_csv=regional.csv_path,
        nuscale_bands_csv=nuscale.csv_path,
        per_smr_bands_csvs={k: v.csv_path for k, v in per_smr.items()},
        per_country_bands_csvs=per_country_bands,
        per_country_nuscale_bands_csvs=per_country_ns_bands,
        country_summary_csv=country_summary_csv,
        country_summary_nuscale_csv=country_summary_ns_csv,
        regional_report_md=regional_report,
        country_report_mds=country_reports,
        figures=figures_out,
        correlation=correlation,
    )
