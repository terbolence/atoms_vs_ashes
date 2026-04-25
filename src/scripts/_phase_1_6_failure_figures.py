# man_hours: 1.0
"""Matplotlib charts for the Phase 1.6 failure analysis bundle.

All functions take a pre-computed :class:`FailureBreakdown` (or a
sub-list of stats) plus the output path; they create the parent
directory if needed and write a 150-DPI PNG.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from atoms_vs_ashes.scoring._failure_breakdown import (  # noqa: E402
    CountryStat,
    CriterionStat,
    FailureBreakdown,
    SmrStat,
)

BUCKET_COLOURS = {
    "survived": "#2ca02c",
    "hard_only": "#d62728",
    "floor_only": "#ff7f0e",
    "both": "#7f3f98",
}


def _short(name: str, max_len: int = 28) -> str:
    return name if len(name) <= max_len else name[: max_len - 1] + "…"


def _save(fig: plt.Figure, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_funnel(b: FailureBreakdown, out: Path) -> Path:
    labels = ["survived", "hard_only", "both", "floor_only"]
    counts = [b.survived, b.hard_only, b.both, b.floor_only]
    pretty = ["Survived", "Hard E-code only", "Hard + floor", "Floor only"]
    colours = [BUCKET_COLOURS[k] for k in labels]
    fig, ax = plt.subplots(figsize=(9, 4.0))
    left = 0
    wide_threshold = b.total_pairs * 0.10
    narrow_idx = 0
    for value, colour, label in zip(counts, colours, pretty):
        ax.barh(0, value, left=left, color=colour,
                edgecolor="white", label=label)
        if value > 0:
            if value >= wide_threshold:
                ax.text(left + value / 2, 0, f"{label}\n{value}",
                        ha="center", va="center", color="white",
                        fontsize=10)
            else:
                # Alternate narrow-segment annotations above/below to
                # avoid horizontal label collisions.
                above = (narrow_idx % 2) == 0
                y_text = 1.5 if above else -1.5
                ax.annotate(
                    f"{label}\n{value}",
                    xy=(left + value / 2, 0.5 if above else -0.5),
                    xytext=(left + value / 2, y_text),
                    ha="center",
                    va="bottom" if above else "top",
                    fontsize=9,
                    arrowprops={"arrowstyle": "-", "color": colour, "lw": 1},
                )
                narrow_idx += 1
        left += value
    ax.set_xlim(-b.total_pairs * 0.01, b.total_pairs * 1.01)
    ax.set_ylim(-2.6, 2.6)
    ax.set_yticks([])
    ax.set_xlabel(f"(site, SMR) pairs — universe = {b.total_pairs}")
    ax.set_title("Phase 1.6 screening funnel — survivors vs. failure mechanism")
    ax.spines[["left", "right", "top"]].set_visible(False)
    ax.legend(loc="lower center", fontsize=8, ncol=4, frameon=False,
              bbox_to_anchor=(0.5, -0.45))
    return _save(fig, out)


def plot_per_criterion(rows: Sequence[CriterionStat], out: Path) -> Path:
    if not rows:
        return out
    labels = [
        f"{r.criterion_id}\n{_short(r.criterion_name, 24)}" for r in rows
    ]
    intersection = np.array([r.intersection_pairs for r in rows])
    hard_only = np.array([r.hard_pairs for r in rows]) - intersection
    floor_only = np.array([r.floor_pairs for r in rows]) - intersection
    fig, ax = plt.subplots(figsize=(max(8.5, 1.2 * len(rows) + 4.5), 6.0))
    x = np.arange(len(rows))
    ax.bar(x, hard_only, color=BUCKET_COLOURS["hard_only"], label="Hard only")
    ax.bar(x, intersection, bottom=hard_only,
           color=BUCKET_COLOURS["both"], label="Hard ∧ floor")
    ax.bar(x, floor_only, bottom=hard_only + intersection,
           color=BUCKET_COLOURS["floor_only"], label="Floor only")
    top_value = max((r.union_pairs for r in rows), default=1)
    for i, r in enumerate(rows):
        ax.text(i, r.union_pairs + top_value * 0.01, str(r.union_pairs),
                ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("Failed (site, SMR) pairs")
    ax.set_title(
        "Failures by exclusionary criterion (hard E-code vs. safety floor)"
    )
    ax.legend(loc="upper right")
    ax.spines[["right", "top"]].set_visible(False)
    fig.subplots_adjust(bottom=0.22)
    return _save(fig, out)


def plot_per_country(rows: Sequence[CountryStat], out: Path) -> Path:
    if not rows:
        return out
    fig, ax = plt.subplots(figsize=(max(8.0, 0.45 * len(rows) + 4.0), 5.5))
    x = np.arange(len(rows))
    survived = np.array([r.survived for r in rows])
    hard_only = np.array([r.hard_only for r in rows])
    both = np.array([r.both for r in rows])
    floor_only = np.array([r.floor_only for r in rows])
    ax.bar(x, survived, color=BUCKET_COLOURS["survived"], label="Survived")
    ax.bar(x, hard_only, bottom=survived,
           color=BUCKET_COLOURS["hard_only"], label="Hard only")
    ax.bar(x, both, bottom=survived + hard_only,
           color=BUCKET_COLOURS["both"], label="Hard ∧ floor")
    ax.bar(x, floor_only, bottom=survived + hard_only + both,
           color=BUCKET_COLOURS["floor_only"], label="Floor only")
    top_value = max((r.n_pairs for r in rows), default=1)
    for i, r in enumerate(rows):
        ax.text(i, r.n_pairs + top_value * 0.01, str(r.n_pairs),
                ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([r.country_code for r in rows],
                       rotation=0, fontsize=9)
    ax.set_ylabel("(site, SMR) pairs")
    ax.set_title("Per-country outcomes (stacked: survived → hard → both → floor)")
    ax.legend(loc="upper right")
    ax.spines[["right", "top"]].set_visible(False)
    return _save(fig, out)


def plot_per_smr(rows: Sequence[SmrStat], out: Path) -> Path:
    if not rows:
        return out
    fig, ax = plt.subplots(figsize=(max(8.0, 0.7 * len(rows) + 4.0), 5.0))
    x = np.arange(len(rows))
    survived = np.array([r.survived for r in rows])
    hard_only = np.array([r.hard_only for r in rows])
    both = np.array([r.both for r in rows])
    floor_only = np.array([r.floor_only for r in rows])
    ax.bar(x, survived, color=BUCKET_COLOURS["survived"], label="Survived")
    ax.bar(x, hard_only, bottom=survived,
           color=BUCKET_COLOURS["hard_only"], label="Hard only")
    ax.bar(x, both, bottom=survived + hard_only,
           color=BUCKET_COLOURS["both"], label="Hard ∧ floor")
    ax.bar(x, floor_only, bottom=survived + hard_only + both,
           color=BUCKET_COLOURS["floor_only"], label="Floor only")
    ax.set_xticks(x)
    ax.set_xticklabels([r.smr_key for r in rows],
                       rotation=20, ha="right", fontsize=9)
    ax.set_ylabel("(site, SMR) pairs")
    ax.set_title("Per-SMR outcomes")
    ax.legend(loc="upper right")
    ax.spines[["right", "top"]].set_visible(False)
    return _save(fig, out)


def plot_multi_failure(b: FailureBreakdown, out: Path) -> Path:
    if not b.multi_failure_histogram:
        return out
    fig, ax = plt.subplots(figsize=(7, 4))
    items = sorted(b.multi_failure_histogram.items())
    xs = [k for k, _ in items]
    ys = [v for _, v in items]
    ax.bar(xs, ys, color="#4c72b0")
    for x_, y_ in zip(xs, ys):
        ax.text(x_, y_, str(y_), ha="center", va="bottom", fontsize=9)
    ax.set_xlabel("Distinct exclusionary criteria failed (per pair)")
    ax.set_ylabel("Failed (site, SMR) pairs")
    ax.set_title("Compound vs. single-criterion failures")
    ax.set_xticks(xs)
    ax.spines[["right", "top"]].set_visible(False)
    return _save(fig, out)


def render_all(
    breakdown: FailureBreakdown, figs_dir: Path
) -> dict[str, Path]:
    """Render all five charts; return ``{key: path}``."""
    return {
        "funnel": plot_funnel(breakdown, figs_dir / "failure_funnel.png"),
        "per_criterion": plot_per_criterion(
            breakdown.per_criterion, figs_dir / "failures_by_criterion.png"
        ),
        "per_country": plot_per_country(
            breakdown.per_country, figs_dir / "failures_by_country.png"
        ),
        "per_smr": plot_per_smr(
            breakdown.per_smr, figs_dir / "failures_by_smr.png"
        ),
        "multi_failure": plot_multi_failure(
            breakdown, figs_dir / "multi_failure_histogram.png"
        ),
    }


__all__ = [
    "BUCKET_COLOURS",
    "plot_funnel",
    "plot_per_criterion",
    "plot_per_country",
    "plot_per_smr",
    "plot_multi_failure",
    "render_all",
]
