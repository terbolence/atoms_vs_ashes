# man_hours: 1.0
"""Internal helpers for :mod:`_phase_1_6_extended_stages`.

Split out so the orchestrator stays under the 300-line Python file
limit. Every helper is a thin wrapper over :mod:`_suite_banding`,
:mod:`_country_summary` or the report / figure modules.
"""

from __future__ import annotations

import csv as _csv
from pathlib import Path

from sqlalchemy.orm import Session

from atoms_vs_ashes.scoring._country_summary import CountrySummaryRow
from atoms_vs_ashes.scoring._suite_banding import (
    BandingRunResult,
    run_banding_stage,
)
from scripts._phase_1_6_country_report import write_country_report
from scripts._phase_1_6_figures_country import (
    plot_band_counts_ah,
    plot_country_top_sites,
)
from scripts._phase_1_6_report_writer import country_display_name


def countries_from_csv(bands_csv: Path) -> list[str]:
    seen: set[str] = set()
    with bands_csv.open("r", encoding="utf-8") as fh:
        for row in _csv.DictReader(fh):
            code = (row.get("country") or "").strip()
            if code and code != "??":
                seen.add(code)
    return sorted(seen)


def band_counts_for_country(per_country_bands_csv: Path) -> dict[str, object]:
    counts: dict[str, int] = {"A": 0, "B": 0, "C": 0}
    with per_country_bands_csv.open("r", encoding="utf-8") as fh:
        for r in _csv.DictReader(fh):
            band = r["band"]
            if band in counts:
                counts[band] += 1
    return {
        "band_a_count": counts["A"],
        "band_b_count": counts["B"],
        "band_c_count": counts["C"],
    }


def attach_band_counts(
    rows: list[CountrySummaryRow],
    per_country_bands: dict[str, Path],
) -> dict[str, dict[str, object]]:
    out: dict[str, dict[str, object]] = {}
    for row in rows:
        csv_path = per_country_bands.get(row.country_code)
        if csv_path and csv_path.exists():
            out[row.country_code] = band_counts_for_country(csv_path)
    return out


def compute_regional_bands(
    session: Session,
    *,
    baseline_label: str,
    audit_dir: Path,
    nuscale_key: str,
    smr_keys: tuple[str, ...],
    stamp: str | None = None,
) -> tuple[BandingRunResult, BandingRunResult, dict[str, BandingRunResult]]:
    regional = run_banding_stage(
        session,
        audit_dir=audit_dir,
        baseline_label=baseline_label,
        stamp=stamp,
    )
    nuscale = run_banding_stage(
        session,
        audit_dir=audit_dir,
        baseline_label=baseline_label,
        smr_filter=nuscale_key,
        stamp=stamp,
    )
    per_smr: dict[str, BandingRunResult] = {}
    for smr_key in smr_keys:
        if smr_key == nuscale_key:
            per_smr[smr_key] = nuscale
            continue
        per_smr[smr_key] = run_banding_stage(
            session,
            audit_dir=audit_dir,
            baseline_label=baseline_label,
            smr_filter=smr_key,
            stamp=stamp,
        )
    return regional, nuscale, per_smr


def compute_country_bands(
    session: Session,
    *,
    baseline_label: str,
    audit_dir: Path,
    countries: list[str],
    smr_filter: str | None,
    stamp: str | None = None,
) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for code in countries:
        result = run_banding_stage(
            session,
            audit_dir=audit_dir,
            baseline_label=baseline_label,
            smr_filter=smr_filter,
            country_filter=code,
            stamp=stamp,
        )
        if result.sites_total > 0:
            out[code] = result.csv_path
            continue
        try:
            result.csv_path.unlink()
        except OSError:
            pass
    return out


def make_regional_figures(
    regional_csv: Path, nuscale_csv: Path, figures_dir: Path
) -> dict[str, Path]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    return {
        "band_counts_global": plot_band_counts_ah(
            regional_csv,
            figures_dir / "band_counts_ah_global.png",
            title="Regional stability banding — all SMRs",
        ),
        "band_counts_nuscale": plot_band_counts_ah(
            nuscale_csv,
            figures_dir / "band_counts_ah_nuscale.png",
            title="Regional stability banding — NuScale voygr6",
        ),
    }


def make_country_figures(
    per_country_bands: dict[str, Path], figures_dir: Path
) -> dict[str, Path]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    out: dict[str, Path] = {}
    for code, csv_path in per_country_bands.items():
        out[code] = plot_country_top_sites(
            csv_path,
            figures_dir / f"{code}_top_sites.png",
            country_display=country_display_name(code),
        )
    return out


def write_country_reports(
    national_dir: Path,
    stamp: str,
    per_country_bands: dict[str, Path],
    per_country_ns_bands: dict[str, Path],
    per_country_figures: dict[str, Path],
) -> dict[str, Path]:
    reports: dict[str, Path] = {}
    for code, bands_csv in per_country_bands.items():
        ns_csv = per_country_ns_bands.get(code, bands_csv)
        fig = per_country_figures.get(code)
        fig_rel = f"figures/{fig.name}" if fig else None
        reports[code] = write_country_report(
            out_dir=national_dir,
            stamp=stamp,
            country_code=code,
            bands_csv_all_smr=bands_csv,
            bands_csv_nuscale=ns_csv,
            figure_rel=fig_rel,
        )
    return reports
