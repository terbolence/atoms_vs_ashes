# man_hours: 1.5
"""Matplotlib charts for the Phase 1.6 failure analysis bundle.

Every plot function takes a :class:`FigureContext` (run stamp + SMR
pretty names + optional per-SMR label) plus the relevant slice of the
:class:`FailureBreakdown`. Charts are designed to be readable by an
executive audience with no rubric knowledge: legends are spelled out,
data labels carry both the count and the percentage, criterion ids
appear with a footer glossary, and country / SMR codes are translated
to vendor / country names where the chart has space.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from atoms_vs_ashes.scoring._failure_breakdown import (
    CountryStat,
    CriterionStat,
    FailureBreakdown,
    SmrStat,
)
from scripts._phase_1_6_failure_chart_styles import (
    BUCKET_COLOURS,
    BUCKET_LONG_LABELS,
    SMR_INVARIANCE_NOTE,
    FigureContext,
    add_data_source_footer,
    add_legend_caption,
    bucket_legend_handles,
    fmt_count_pct,
    fmt_pct,
    save,
    stacked_bar,
    wrap_label,
)


def plot_funnel(b: FailureBreakdown, out: Path, ctx: FigureContext) -> Path:
    order = ["survived", "hard_only", "both", "floor_only"]
    counts = {"survived": b.survived, "hard_only": b.hard_only,
              "both": b.both, "floor_only": b.floor_only}
    fig, ax = plt.subplots(figsize=(11, 4.6))
    left = 0
    wide_threshold = b.total_pairs * 0.10
    narrow_idx = 0
    for key in order:
        value = counts[key]
        colour = BUCKET_COLOURS[key]
        long_label = BUCKET_LONG_LABELS[key].split(" (")[0]
        ax.barh(0, value, left=left, color=colour, edgecolor="white")
        if value > 0:
            label = f"{long_label}\n{fmt_count_pct(value, b.total_pairs)}"
            if value >= wide_threshold:
                ax.text(left + value / 2, 0, label,
                        ha="center", va="center", color="white", fontsize=10)
            else:
                above = (narrow_idx % 2) == 0
                y_text = 1.7 if above else -1.7
                ax.annotate(
                    label,
                    xy=(left + value / 2, 0.5 if above else -0.5),
                    xytext=(left + value / 2, y_text),
                    ha="center", va="bottom" if above else "top",
                    fontsize=9,
                    arrowprops={"arrowstyle": "-", "color": colour, "lw": 1},
                )
                narrow_idx += 1
        left += value
    ax.set_xlim(-b.total_pairs * 0.01, b.total_pairs * 1.01)
    ax.set_ylim(-2.8, 2.8)
    ax.set_yticks([])
    ax.set_xlabel(
        f"Site x technology evaluations (universe = {b.total_pairs:,})")
    ax.set_title(
        "Site-screening funnel — which evaluations survive exclusionary checks?"
        + ctx.title_suffix())
    ax.spines[["left", "right", "top"]].set_visible(False)
    ax.legend(handles=bucket_legend_handles(),
              loc="lower center", fontsize=8, ncol=2,
              frameon=False, bbox_to_anchor=(0.5, -0.55))
    add_legend_caption(fig)
    add_data_source_footer(fig, ctx)
    return save(fig, out, bottom=0.30)


def plot_per_criterion(
    rows: Sequence[CriterionStat], out: Path, ctx: FigureContext,
    *, total_failed: int,
) -> Path:
    if not rows:
        return out
    labels = [
        f"{r.criterion_id}\n" + wrap_label(r.criterion_name, width=22)
        for r in rows
    ]
    intersection = np.array([r.intersection_pairs for r in rows])
    hard_only = np.array([r.hard_pairs for r in rows]) - intersection
    floor_only = np.array([r.floor_pairs for r in rows]) - intersection
    fig, ax = plt.subplots(figsize=(max(10.0, 1.8 * len(rows) + 4.5), 7.0))
    x = np.arange(len(rows))
    ax.bar(x, hard_only, color=BUCKET_COLOURS["hard_only"])
    ax.bar(x, intersection, bottom=hard_only, color=BUCKET_COLOURS["both"])
    ax.bar(x, floor_only, bottom=hard_only + intersection,
           color=BUCKET_COLOURS["floor_only"])
    top_value = max((r.union_pairs for r in rows), default=1)
    for i, r in enumerate(rows):
        pct = fmt_pct(r.union_pairs, total_failed)
        ax.text(i, r.union_pairs + top_value * 0.015,
                f"{r.union_pairs}\n{pct} of failed",
                ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=0, fontsize=8)
    ax.set_ylabel("Failed evaluations (site x technology)")
    ax.set_title(
        "Why screenings fail — by exclusionary criterion"
        + ctx.title_suffix()
        + f"  (total failed = {total_failed:,})")
    ax.legend(handles=bucket_legend_handles(include_survived=False),
              loc="upper right", fontsize=8)
    ax.spines[["right", "top"]].set_visible(False)
    ax.set_ylim(0, top_value * 1.2)
    add_legend_caption(fig)
    add_data_source_footer(fig, ctx)
    return save(fig, out, bottom=0.22)


def plot_per_country(
    rows: Sequence[CountryStat], out: Path, ctx: FigureContext
) -> Path:
    if not rows:
        return out
    fig, ax = plt.subplots(figsize=(max(10.0, 0.55 * len(rows) + 4.5), 6.5))
    x = np.arange(len(rows))
    survived = np.array([r.survived for r in rows])
    hard_only = np.array([r.hard_only for r in rows])
    both = np.array([r.both for r in rows])
    floor_only = np.array([r.floor_only for r in rows])
    stacked_bar(ax, x, survived, hard_only, both, floor_only)
    top_value = max((r.n_pairs for r in rows), default=1)
    for i, r in enumerate(rows):
        pct = fmt_pct(r.survived, r.n_pairs)
        ax.text(i, r.n_pairs + top_value * 0.01,
                f"{r.n_pairs}\nsurv {r.survived} ({pct})",
                ha="center", va="bottom", fontsize=7)
    tick_labels = [f"{r.country_code}\n{ctx.country_name(r.country_code)}"
                   for r in rows]
    ax.set_xticks(x)
    ax.set_xticklabels(tick_labels, rotation=0, fontsize=7)
    ax.set_ylabel("Site x technology evaluations")
    ax.set_title(
        "Per-country outcomes — survival vs. failure mode"
        + ctx.title_suffix())
    ax.legend(handles=bucket_legend_handles(),
              loc="upper right", fontsize=7)
    ax.spines[["right", "top"]].set_visible(False)
    ax.set_ylim(0, top_value * 1.18)
    add_legend_caption(fig)
    add_data_source_footer(fig, ctx)
    return save(fig, out, bottom=0.24)


def plot_per_smr(
    rows: Sequence[SmrStat], out: Path, ctx: FigureContext
) -> Path:
    if not rows:
        return out
    fig, ax = plt.subplots(figsize=(max(11.0, 1.4 * len(rows) + 4.0), 6.5))
    x = np.arange(len(rows))
    survived = np.array([r.survived for r in rows])
    hard_only = np.array([r.hard_only for r in rows])
    both = np.array([r.both for r in rows])
    floor_only = np.array([r.floor_only for r in rows])
    stacked_bar(ax, x, survived, hard_only, both, floor_only)
    tick_labels = [
        f"{ctx.smr_name(r.smr_key)}\n({r.smr_key})" for r in rows
    ]
    top_value = max((r.n_pairs for r in rows), default=1)
    for i, r in enumerate(rows):
        ax.text(i, r.n_pairs + top_value * 0.01,
                f"surv {r.survived} ({fmt_pct(r.survived, r.n_pairs)})",
                ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(tick_labels, rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("Site x technology evaluations")
    ax.set_title("Per-SMR outcomes — by vendor / design")
    ax.legend(handles=bucket_legend_handles(), loc="upper right", fontsize=7)
    ax.spines[["right", "top"]].set_visible(False)
    ax.set_ylim(0, top_value * 1.15)
    fig.text(0.5, 0.135, SMR_INVARIANCE_NOTE, ha="center", va="bottom",
             fontsize=7.5, color="#444", style="italic", wrap=True)
    add_legend_caption(fig)
    add_data_source_footer(fig, ctx)
    return save(fig, out, bottom=0.34)


def plot_multi_failure(
    b: FailureBreakdown, out: Path, ctx: FigureContext
) -> Path:
    if not b.multi_failure_histogram:
        return out
    fig, ax = plt.subplots(figsize=(9, 5.5))
    items = sorted(b.multi_failure_histogram.items())
    xs = [k for k, _ in items]
    ys = [v for _, v in items]
    ax.bar(xs, ys, color="#4c72b0")
    failed_total = b.failed_any
    for x_, y_ in zip(xs, ys):
        ax.text(x_, y_, f"{y_}\n{fmt_pct(y_, failed_total)} of failed",
                ha="center", va="bottom", fontsize=9)
    ax.set_xlabel(
        "Distinct exclusionary criteria triggered (per failed evaluation)")
    ax.set_ylabel("Failed evaluations (site x technology)")
    ax.set_title(
        "Compound vs. single-criterion failures" + ctx.title_suffix()
        + f"  (total failed = {failed_total:,})")
    ax.set_xticks(xs)
    ax.set_xticklabels(
        [f"{k} criterion" if k == 1 else f"{k} criteria" for k in xs],
        fontsize=9)
    ax.spines[["right", "top"]].set_visible(False)
    if ys:
        ax.set_ylim(0, max(ys) * 1.18)
    fig.text(
        0.5, 0.135,
        "Single-criterion failures may be recoverable with better "
        "data; multi-criterion failures cluster the truly unsuitable "
        "evaluations.",
        ha="center", va="bottom", fontsize=8, color="#444",
        style="italic", wrap=True)
    add_legend_caption(fig)
    add_data_source_footer(fig, ctx)
    return save(fig, out, bottom=0.30)


def render_all(
    breakdown: FailureBreakdown,
    figs_dir: Path,
    ctx: FigureContext,
    *,
    include_per_smr_chart: bool = True,
) -> dict[str, Path]:
    """Render every chart in the failure pack; return ``{key: path}``."""
    out: dict[str, Path] = {
        "funnel": plot_funnel(
            breakdown, figs_dir / "failure_funnel.png", ctx),
        "per_criterion": plot_per_criterion(
            breakdown.per_criterion,
            figs_dir / "failures_by_criterion.png",
            ctx, total_failed=breakdown.failed_any),
        "per_country": plot_per_country(
            breakdown.per_country,
            figs_dir / "failures_by_country.png", ctx),
        "multi_failure": plot_multi_failure(
            breakdown, figs_dir / "multi_failure_histogram.png", ctx),
    }
    if include_per_smr_chart:
        out["per_smr"] = plot_per_smr(
            breakdown.per_smr, figs_dir / "failures_by_smr.png", ctx)
    return out


__all__ = [
    "FigureContext",
    "plot_funnel",
    "plot_per_criterion",
    "plot_per_country",
    "plot_per_smr",
    "plot_multi_failure",
    "render_all",
]
