# man_hours: 1.5
"""Criterion correlation heatmap for Phase 1.6 sensitivity audit.

Pulls baseline ranking rows from the merged DB, computes Pearson and
Spearman correlations across criteria, writes a CSV of every ordered
pair, renders two PNG heatmaps (Pearson, Spearman), and emits a
flagged-pairs Markdown snippet that the regional report can include.

Module-level entry points (called by ``_phase_1_6_extended_stages``):

- :func:`build_correlation_artefacts` — DB → CSV + PNG + flagged MD,
  returns a :class:`CorrelationArtefacts` bundle for the extended-stages
  result and the regional report.

Standalone CLI is also provided so reviewers can rerun against any
``baseline_label`` (e.g. ``baseline`` or ``w_swing``).
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless; must precede pyplot import
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from atoms_vs_ashes.db.analytics_writers import (  # noqa: E402
    persist_criterion_correlations,
)
from atoms_vs_ashes.db.engine import session_scope  # noqa: E402
from atoms_vs_ashes.db.models import RankingScore  # noqa: E402
from atoms_vs_ashes.logging import get_logger  # noqa: E402
from atoms_vs_ashes.scoring._criterion_correlation import (  # noqa: E402
    CorrelationReport,
    DEFAULT_THRESHOLD,
    compute_correlations,
    render_flagged_markdown,
)
from atoms_vs_ashes.scoring._suite_persist import (  # noqa: E402
    _resolve_baseline_run_id,  # type: ignore[attr-defined]
)
from atoms_vs_ashes.scoring.rubric import load_rubric_bundle  # noqa: E402

log = get_logger(__name__)

DB_PROFILES = {
    "api": "atoms_vs_ashes",
    "llm": "atoms_vs_ashes_llm",
    "merged": "atoms_vs_ashes_merged",
}
DEFAULT_RUBRIC_DIR = Path("config/scoring_rubrics")


@dataclass(frozen=True)
class CorrelationArtefacts:
    pairs_csv: Path
    pearson_png: Path
    spearman_png: Path
    flagged_md: Path
    n_pairs_observed: int
    n_flagged: int
    threshold: float


def _load_baseline_scores(
    session: Session, *, baseline_label: str
) -> list[RankingScore]:
    run_id = _resolve_baseline_run_id(
        session, weight_profile_base=baseline_label
    )
    stmt = select(RankingScore)
    if run_id:
        stmt = stmt.where(RankingScore.run_id == run_id)
    rows = list(session.execute(stmt).scalars().all())
    log.info(
        "correlation_rows_loaded",
        rows=len(rows),
        baseline_run_id=run_id,
    )
    return rows


def _plot_heatmap(
    matrix: pd.DataFrame,
    out_path: Path,
    *,
    title: str,
    cmap: str = "RdBu_r",
) -> Path:
    if matrix.empty:
        log.warning("correlation_heatmap_empty", path=str(out_path))
        return out_path
    n = matrix.shape[0]
    size = max(7.0, 0.32 * n)
    fig, ax = plt.subplots(figsize=(size, size))
    im = ax.imshow(matrix.to_numpy(), cmap=cmap, vmin=-1, vmax=1)
    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    ax.set_xticklabels(matrix.columns, rotation=90, fontsize=7)
    ax.set_yticklabels(matrix.index, fontsize=7)
    ax.set_title(title)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def _render_flagged_md(
    report: CorrelationReport,
    out_path: Path,
    *,
    criterion_names: dict[str, str],
    stamp: str,
    pairs_csv: Path,
    pearson_png: Path,
    spearman_png: Path,
) -> Path:
    body = render_flagged_markdown(report, criterion_names=criterion_names)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    text = (
        f"# Criterion correlation flag list\n\n"
        f"- Stamp: `{stamp}`\n"
        f"- Threshold: |ρ| ≥ {report.threshold:.2f}\n"
        f"- Pairs observed: {report.n_pairs}\n"
        f"- Flagged pairs: {len(report.flagged())}\n"
        f"- Source CSV: `{pairs_csv.as_posix()}`\n"
        f"- Pearson heatmap: `{pearson_png.as_posix()}`\n"
        f"- Spearman heatmap: `{spearman_png.as_posix()}`\n\n"
        "## Flagged criterion pairs\n\n"
        f"{body}\n"
    )
    out_path.write_text(text)
    return out_path


def build_correlation_artefacts(
    session: Session,
    *,
    audit_dir: Path,
    figures_dir: Path,
    flagged_md_path: Path,
    baseline_label: str = "baseline",
    threshold: float = DEFAULT_THRESHOLD,
    rubric_dir: Path = DEFAULT_RUBRIC_DIR,
    stamp: str | None = None,
    run_id: str | None = None,
) -> CorrelationArtefacts:
    """Compute correlation, write CSV/PNGs/MD, return artefact paths."""
    stamp = stamp or datetime.now(UTC).strftime("%Y%m%d")
    rows = _load_baseline_scores(session, baseline_label=baseline_label)
    bundle = load_rubric_bundle(rubric_dir)
    criterion_names = {cid: c.name for cid, c in bundle.items()}
    report = compute_correlations(rows, threshold=threshold)
    audit_dir.mkdir(parents=True, exist_ok=True)
    pairs_csv = audit_dir / f"{stamp}_criterion_correlation.csv"
    long_df = report.to_long_dataframe()
    if not long_df.empty:
        long_df.to_csv(pairs_csv, index=False)
        persist_criterion_correlations(
            session, run_id=run_id,
            rows=long_df.to_dict(orient="records"),
            threshold=threshold,
        )
    else:
        pairs_csv.write_text("criterion_a,criterion_b,pearson,spearman,max_abs,n_pairs,flagged\n")
    pearson_png = _plot_heatmap(
        report.matrix_pearson,
        figures_dir / "criterion_correlation_pearson.png",
        title=f"Criterion correlation — Pearson (n = {report.n_pairs})",
    )
    spearman_png = _plot_heatmap(
        report.matrix_spearman,
        figures_dir / "criterion_correlation_spearman.png",
        title=f"Criterion correlation — Spearman (n = {report.n_pairs})",
    )
    _render_flagged_md(
        report,
        flagged_md_path,
        criterion_names=criterion_names,
        stamp=stamp,
        pairs_csv=pairs_csv,
        pearson_png=pearson_png,
        spearman_png=spearman_png,
    )
    return CorrelationArtefacts(
        pairs_csv=pairs_csv,
        pearson_png=pearson_png,
        spearman_png=spearman_png,
        flagged_md=flagged_md_path,
        n_pairs_observed=report.n_pairs,
        n_flagged=len(report.flagged()),
        threshold=threshold,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db-profile",
        choices=sorted(DB_PROFILES),
        default="merged",
    )
    parser.add_argument("--baseline-label", default="baseline")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument(
        "--audit-dir",
        type=Path,
        default=Path("audit/post_processing/06_scoring"),
    )
    parser.add_argument(
        "--figures-dir",
        type=Path,
        default=Path(
            "audit/post_processing/06_scoring/figures/correlation"
        ),
    )
    parser.add_argument(
        "--flagged-md",
        type=Path,
        default=Path("report/methodology/criterion_correlation.md"),
    )
    parser.add_argument(
        "--stamp",
        default=datetime.now(UTC).strftime("%Y%m%d"),
    )
    args = parser.parse_args(argv)

    os.environ["POSTGRES_DB"] = DB_PROFILES[args.db_profile]

    with session_scope() as session:
        artefacts = build_correlation_artefacts(
            session,
            audit_dir=args.audit_dir,
            figures_dir=args.figures_dir,
            flagged_md_path=args.flagged_md,
            baseline_label=args.baseline_label,
            threshold=args.threshold,
            stamp=args.stamp,
        )
    print(f"Wrote {artefacts.pairs_csv}")
    print(f"Wrote {artefacts.pearson_png}")
    print(f"Wrote {artefacts.spearman_png}")
    print(f"Wrote {artefacts.flagged_md}")
    print(
        f"Pairs observed: {artefacts.n_pairs_observed}, "
        f"flagged (|ρ| ≥ {artefacts.threshold}): {artefacts.n_flagged}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
