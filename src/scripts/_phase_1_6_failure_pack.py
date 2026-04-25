# man_hours: 1.0
"""End-to-end pack renderer for the Phase 1.6 failure analysis.

Renders one *pack* (a CSV / PNG / MD bundle) for either the global
universe or a single SMR design. Lifted out of
``generate_failure_analysis`` so that orchestrator stays well under
the 300-line cap once the per-SMR loop and CLI surface are added.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models import ScreeningVerdict, SmrDesign
from atoms_vs_ashes.scoring._failure_breakdown import (
    FailureBreakdown,
    aggregate_failures,
)
from scripts._phase_1_6_failure_chart_styles import FigureContext
from scripts._phase_1_6_failure_csv import (
    write_per_country,
    write_per_criterion,
    write_per_pair,
    write_per_smr,
    write_summary,
)
from scripts._phase_1_6_failure_figures import render_all
from scripts._phase_1_6_failure_report import PerTechPack, render_methodology

VENDOR_FLAGS: dict[str, str] = {
    "nuscale": "nuscale_voygr6",
    "geh": "bwrx_300",
    "holtec": "holtec_smr300",
    "oklo": "oklo_aurora",
    "rollsroyce": "rolls_royce_smr",
    "xenergy": "xe_100",
    "terrapower-nominal": "natrium_nominal",
    "terrapower-peak": "natrium_peak",
}

ALL_SMR_KEYS: tuple[str, ...] = tuple(VENDOR_FLAGS.values())


@dataclass(frozen=True)
class SmrMeta:
    smr_key: str
    name: str
    capacity_mwe: float | None
    epz_radius_km: float | None
    cooling_type: str | None

    def banner(self) -> str:
        metric_bits: list[str] = []
        if self.capacity_mwe is not None:
            metric_bits.append(f"{self.capacity_mwe:.0f} MWe")
        if self.epz_radius_km is not None:
            metric_bits.append(f"EPZ ≈ {self.epz_radius_km:.1f} km")
        if self.cooling_type:
            metric_bits.append(self.cooling_type)
        if metric_bits:
            return f"{self.name} — " + ", ".join(metric_bits)
        return self.name


def load_smr_meta(session: Session) -> dict[str, SmrMeta]:
    out: dict[str, SmrMeta] = {}
    for d in session.query(SmrDesign).all():
        out[d.smr_key] = SmrMeta(
            smr_key=d.smr_key,
            name=d.name,
            capacity_mwe=float(d.capacity_mwe) if d.capacity_mwe else None,
            epz_radius_km=(float(d.epz_radius_km)
                           if d.epz_radius_km is not None else None),
            cooling_type=d.cooling_type,
        )
    return out


@dataclass(frozen=True)
class PackPaths:
    audit_dir: Path
    figs_dir: Path
    method_md: Path


def paths_for_global(
    *,
    audit_dir: Path,
    report_root: Path,
    method_path: Path,
    stamp: str,
) -> PackPaths:
    return PackPaths(
        audit_dir=audit_dir,
        figs_dir=report_root / stamp / "figures" / "failure",
        method_md=method_path,
    )


def paths_for_smr(
    *,
    smr_key: str,
    audit_dir: Path,
    report_root: Path,
    method_root: Path,
    stamp: str,
) -> PackPaths:
    return PackPaths(
        audit_dir=audit_dir / "per_smr" / smr_key,
        figs_dir=report_root / stamp / "figures" / "failure"
        / "per_smr" / smr_key,
        method_md=method_root / f"failure_analysis_{smr_key}.md",
    )


def build_per_tech_packs(
    *,
    smr_meta: Mapping[str, SmrMeta],
    method_root: Path,
    featured: str | None = "nuscale_voygr6",
) -> list[PerTechPack]:
    """All eight known SMR keys with their MD path and a 'featured' flag."""
    out: list[PerTechPack] = []
    for smr_key in ALL_SMR_KEYS:
        meta = smr_meta.get(smr_key)
        pretty = meta.name if meta else smr_key
        out.append(PerTechPack(
            smr_key=smr_key,
            pretty_name=pretty,
            method_md=method_root / f"failure_analysis_{smr_key}.md",
            featured=(smr_key == featured),
        ))
    return out


@dataclass(frozen=True)
class PackArtefacts:
    smr_key: str | None
    summary_csv: Path
    per_criterion_csv: Path
    per_country_csv: Path
    per_smr_csv: Path | None
    per_pair_csv: Path
    figures_dir: Path
    method_md: Path
    breakdown: FailureBreakdown


def render_pack(
    *,
    verdicts_by_pair: Mapping[tuple, Sequence[ScreeningVerdict]],
    country_by_site: Mapping[object, str],
    criterion_names: Mapping[str, str],
    paths: PackPaths,
    stamp: str,
    run_id: str | None,
    smr_key: str | None = None,
    smr_meta: Mapping[str, SmrMeta] | None = None,
    per_tech_packs: Sequence[PerTechPack] | None = None,
) -> PackArtefacts:
    """Render one CSV/PNG/MD pack (global if ``smr_key`` is None)."""
    smr_meta = smr_meta or {}
    breakdown = aggregate_failures(
        verdicts_by_pair,
        country_by_site=country_by_site,
        criterion_names=criterion_names,
        smr_filter=smr_key,
    )
    paths.audit_dir.mkdir(parents=True, exist_ok=True)
    summary_csv = paths.audit_dir / f"{stamp}_failure_summary.csv"
    per_criterion_csv = paths.audit_dir / f"{stamp}_failure_per_criterion.csv"
    per_country_csv = paths.audit_dir / f"{stamp}_failure_per_country.csv"
    per_pair_csv = paths.audit_dir / f"{stamp}_failure_per_pair.csv"
    write_summary(breakdown, summary_csv, stamp=stamp, run_id=run_id)
    write_per_criterion(breakdown.per_criterion, per_criterion_csv)
    write_per_country(breakdown.per_country, per_country_csv)
    write_per_pair(breakdown, per_pair_csv)
    per_smr_csv: Path | None = None
    if smr_key is None:
        per_smr_csv = paths.audit_dir / f"{stamp}_failure_per_smr.csv"
        write_per_smr(breakdown.per_smr, per_smr_csv)

    smr_pretty = {k: m.name for k, m in smr_meta.items()}
    smr_label = smr_meta[smr_key].name if (smr_key and smr_key in smr_meta) \
        else (smr_key if smr_key else None)
    smr_banner = (smr_meta[smr_key].banner()
                  if smr_key and smr_key in smr_meta else None)

    ctx = FigureContext(
        stamp=stamp, run_id=run_id,
        smr_pretty=smr_pretty, smr_label=smr_label,
    )
    figure_paths = render_all(
        breakdown, paths.figs_dir, ctx,
        include_per_smr_chart=(smr_key is None),
    )

    audit_paths: dict[str, Path] = {
        "summary": summary_csv,
        "per_criterion": per_criterion_csv,
        "per_country": per_country_csv,
        "per_pair": per_pair_csv,
    }
    if per_smr_csv is not None:
        audit_paths["per_smr"] = per_smr_csv

    method_md = render_methodology(
        breakdown,
        stamp=stamp, run_id=run_id,
        audit_paths=audit_paths,
        figure_paths=figure_paths,
        out_path=paths.method_md,
        smr_pretty=smr_pretty,
        smr_label=smr_label,
        smr_banner=smr_banner,
        per_tech_packs=per_tech_packs if smr_key is None else None,
    )
    return PackArtefacts(
        smr_key=smr_key,
        summary_csv=summary_csv,
        per_criterion_csv=per_criterion_csv,
        per_country_csv=per_country_csv,
        per_smr_csv=per_smr_csv,
        per_pair_csv=per_pair_csv,
        figures_dir=paths.figs_dir,
        method_md=method_md,
        breakdown=breakdown,
    )


__all__ = [
    "VENDOR_FLAGS",
    "ALL_SMR_KEYS",
    "SmrMeta",
    "PackPaths",
    "PackArtefacts",
    "load_smr_meta",
    "paths_for_global",
    "paths_for_smr",
    "build_per_tech_packs",
    "render_pack",
]
