# man_hours: 1.0
"""Phase 1.6 failure-mode analysis — DB → CSVs + PNG charts + methodology MD.

Answers the regulator question "**why did sites fail during scoring?**"
on top of the screening verdicts persisted by the floor-rescore run.

Outputs (all stamped):

- ``audit/post_processing/06_scoring/{stamp}_failure_summary.csv``
- ``audit/post_processing/06_scoring/{stamp}_failure_per_criterion.csv``
- ``audit/post_processing/06_scoring/{stamp}_failure_per_country.csv``
- ``audit/post_processing/06_scoring/{stamp}_failure_per_smr.csv``
- ``audit/post_processing/06_scoring/{stamp}_failure_per_pair.csv``
- ``report/output/sensitivity/{stamp}/figures/failure/*.png`` —
  funnel, per-criterion, per-country, per-SMR, multi-failure histogram.
- ``report/methodology/failure_analysis.md`` — narrative + tables +
  embedded figure references.

Run::

    .venv/bin/python -m scripts.generate_failure_analysis \\
        --db-profile merged --stamp 20260425
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models import ScreeningVerdict, Site
from atoms_vs_ashes.scoring._failure_breakdown import (
    FailureBreakdown,
    aggregate_failures,
)
from atoms_vs_ashes.scoring._suite_persist import (
    _resolve_baseline_run_id,  # type: ignore[attr-defined]
)
from atoms_vs_ashes.scoring.rubric import load_rubric_bundle
from scripts._phase_1_6_failure_csv import (
    write_per_country,
    write_per_criterion,
    write_per_pair,
    write_per_smr,
    write_summary,
)
from scripts._phase_1_6_failure_figures import render_all
from scripts._phase_1_6_failure_report import render_methodology

DB_PROFILES = {
    "api": "atoms_vs_ashes",
    "llm": "atoms_vs_ashes_llm",
    "merged": "atoms_vs_ashes_merged",
}
DEFAULT_RUBRIC_DIR = Path("config/scoring_rubrics")
DEFAULT_AUDIT_DIR = Path("audit/post_processing/06_scoring")
DEFAULT_REPORT_ROOT = Path("report/output/sensitivity")
DEFAULT_METHOD_PATH = Path("report/methodology/failure_analysis.md")


@dataclass(frozen=True)
class FailureArtefacts:
    summary_csv: Path
    per_criterion_csv: Path
    per_country_csv: Path
    per_smr_csv: Path
    per_pair_csv: Path
    figures_dir: Path
    method_md: Path
    breakdown: FailureBreakdown


def _load(
    session: Session, *, baseline_label: str
) -> tuple[dict[tuple, list[ScreeningVerdict]], dict, str | None]:
    run_id = _resolve_baseline_run_id(
        session, weight_profile_base=baseline_label
    )
    country_by_site = {
        sid: code
        for sid, code in session.execute(
            select(Site.site_id, Site.country_code)
        ).all()
    }
    stmt = select(ScreeningVerdict)
    if run_id:
        stmt = stmt.where(ScreeningVerdict.run_id == run_id)
    verdicts_by_pair: dict[tuple, list[ScreeningVerdict]] = {}
    for v in session.execute(stmt).scalars().all():
        verdicts_by_pair.setdefault((v.site_id, v.smr_key), []).append(v)
    return verdicts_by_pair, country_by_site, run_id


def build_failure_artefacts(
    session: Session,
    *,
    stamp: str,
    audit_dir: Path = DEFAULT_AUDIT_DIR,
    report_root: Path = DEFAULT_REPORT_ROOT,
    method_path: Path = DEFAULT_METHOD_PATH,
    rubric_dir: Path = DEFAULT_RUBRIC_DIR,
    baseline_label: str = "baseline",
) -> FailureArtefacts:
    """Compute breakdown, write CSVs / PNGs / MD, return a bundle."""
    bundle = load_rubric_bundle(rubric_dir)
    criterion_names = {cid: c.name for cid, c in bundle.items()}
    verdicts_by_pair, country_by_site, run_id = _load(
        session, baseline_label=baseline_label
    )
    breakdown = aggregate_failures(
        verdicts_by_pair,
        country_by_site=country_by_site,
        criterion_names=criterion_names,
    )

    audit_dir.mkdir(parents=True, exist_ok=True)
    summary_csv = audit_dir / f"{stamp}_failure_summary.csv"
    per_criterion_csv = audit_dir / f"{stamp}_failure_per_criterion.csv"
    per_country_csv = audit_dir / f"{stamp}_failure_per_country.csv"
    per_smr_csv = audit_dir / f"{stamp}_failure_per_smr.csv"
    per_pair_csv = audit_dir / f"{stamp}_failure_per_pair.csv"

    write_summary(breakdown, summary_csv, stamp=stamp, run_id=run_id)
    write_per_criterion(breakdown.per_criterion, per_criterion_csv)
    write_per_country(breakdown.per_country, per_country_csv)
    write_per_smr(breakdown.per_smr, per_smr_csv)
    write_per_pair(breakdown, per_pair_csv)

    figs_dir = report_root / stamp / "figures" / "failure"
    figure_paths = render_all(breakdown, figs_dir)

    audit_paths = {
        "summary": summary_csv,
        "per_criterion": per_criterion_csv,
        "per_country": per_country_csv,
        "per_smr": per_smr_csv,
        "per_pair": per_pair_csv,
    }
    method_md = render_methodology(
        breakdown,
        stamp=stamp,
        run_id=run_id,
        audit_paths=audit_paths,
        figure_paths=figure_paths,
        out_path=method_path,
    )

    return FailureArtefacts(
        summary_csv=summary_csv,
        per_criterion_csv=per_criterion_csv,
        per_country_csv=per_country_csv,
        per_smr_csv=per_smr_csv,
        per_pair_csv=per_pair_csv,
        figures_dir=figs_dir,
        method_md=method_md,
        breakdown=breakdown,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db-profile", choices=sorted(DB_PROFILES), default="merged"
    )
    parser.add_argument("--baseline-label", default="baseline")
    parser.add_argument(
        "--stamp", default=datetime.now(UTC).strftime("%Y%m%d")
    )
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument(
        "--report-root", type=Path, default=DEFAULT_REPORT_ROOT
    )
    parser.add_argument(
        "--method-path", type=Path, default=DEFAULT_METHOD_PATH
    )
    parser.add_argument("--rubric-dir", type=Path, default=DEFAULT_RUBRIC_DIR)
    args = parser.parse_args(argv)

    os.environ["POSTGRES_DB"] = DB_PROFILES[args.db_profile]

    with session_scope() as session:
        art = build_failure_artefacts(
            session,
            stamp=args.stamp,
            audit_dir=args.audit_dir,
            report_root=args.report_root,
            method_path=args.method_path,
            rubric_dir=args.rubric_dir,
            baseline_label=args.baseline_label,
        )
    print(f"Wrote {art.summary_csv}")
    print(f"Wrote {art.per_criterion_csv}")
    print(f"Wrote {art.per_country_csv}")
    print(f"Wrote {art.per_smr_csv}")
    print(f"Wrote {art.per_pair_csv}")
    print(f"Figures dir: {art.figures_dir}")
    print(f"Methodology MD: {art.method_md}")
    print(
        f"Summary: total={art.breakdown.total_pairs} "
        f"survived={art.breakdown.survived} "
        f"hard_only={art.breakdown.hard_only} "
        f"floor_only={art.breakdown.floor_only} "
        f"both={art.breakdown.both}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
