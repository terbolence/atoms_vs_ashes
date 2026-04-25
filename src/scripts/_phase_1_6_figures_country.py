# man_hours: 1.25
"""Figure generators for the country / scope-specific outputs.

Reads the per-scope bands CSVs written by :mod:`_suite_banding` (scope
can be global, NuScale-only, per-country, or per-country × NuScale) and
emits PNGs sized for the regional summary and per-country MDs. Every
chart is pure matplotlib + pandas — no DB access.

Requires the ``report_plots`` optional extra (matplotlib>=3.8).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless; must precede pyplot import
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from atoms_vs_ashes.scoring._band_rules import BAND_DISPLAY_ORDER  # noqa: E402

TOP_N_COUNTRY = 10


def _load_bands_df(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    for col in ("top5pct_hit_rate", "top10pct_hit_rate", "top30pct_hit_rate"):
        if col in df.columns:
            df[col] = df[col].astype(float)
    return df


def _band_rank(df: pd.DataFrame) -> pd.DataFrame:
    order_map = {b: i for i, b in enumerate(BAND_DISPLAY_ORDER)}
    df = df.copy()
    df["_band_rank"] = df["band"].map(order_map).fillna(99)
    df = df.sort_values(
        by=[
            "_band_rank",
            "top5pct_hit_rate",
            "top10pct_hit_rate",
            "top30pct_hit_rate",
        ],
        ascending=[True, False, False, False],
    )
    return df.drop(columns="_band_rank")


def plot_band_counts_ah(
    bands_csv: Path, out_path: Path, *, title: str
) -> Path:
    """Bar chart of A–H band counts for one scope (global or NuScale)."""
    df = _load_bands_df(bands_csv)
    counts = df["band"].value_counts()
    counts = pd.Series(
        {b: int(counts.get(b, 0)) for b in BAND_DISPLAY_ORDER}
    )
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    bars = ax.bar(counts.index.tolist(), counts.to_numpy())
    for rect, value in zip(bars, counts.to_numpy()):
        ax.text(
            rect.get_x() + rect.get_width() / 2,
            rect.get_height(),
            f"{int(value)}",
            ha="center",
            va="bottom",
        )
    ax.set_xlabel("Stability band (A = most robust)")
    ax.set_ylabel("Sites")
    ax.set_title(f"{title} (N = {int(counts.sum())})")
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_country_top_sites(
    bands_csv: Path, out_path: Path, *, country_display: str
) -> Path:
    """Horizontal bar chart of the within-country top sites.

    X-axis = top-10 % hit rate (how often the site is in the local
    top-10 % slice across scenarios). Y-axis = site name + band.
    If the country has fewer than ``TOP_N_COUNTRY`` sites, all are shown.
    """
    df = _load_bands_df(bands_csv)
    if df.empty:
        return _plot_empty(out_path, country_display)

    df = _band_rank(df).head(TOP_N_COUNTRY)
    labels = [
        f"{row['band']}  {row['site_name']}"
        for _, row in df.iterrows()
    ]
    values = df["top10pct_hit_rate"].to_numpy()

    fig, ax = plt.subplots(figsize=(9.0, 4.5))
    ax.barh(labels[::-1], values[::-1])
    ax.set_xlim(0, 1.05)
    ax.axvline(0.80, linestyle="--", linewidth=1, color="grey", label="Band B threshold (0.80)")
    ax.axvline(0.50, linestyle=":", linewidth=1, color="grey", label="Band C threshold (0.50)")
    ax.set_xlabel("Top-10 % hit rate (within-country)")
    ax.set_title(
        f"{country_display} — top {len(df)} sites by within-country stability"
    )
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    ax.legend(loc="lower right", fontsize="small")
    for idx, value in enumerate(values[::-1]):
        ax.text(
            value + 0.01,
            idx,
            f"{value:.2f}",
            va="center",
            fontsize=8,
        )
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def _plot_empty(out_path: Path, country_display: str) -> Path:
    fig, ax = plt.subplots(figsize=(6.0, 2.0))
    ax.text(
        0.5,
        0.5,
        f"{country_display} — no scored sites in this scope",
        ha="center",
        va="center",
    )
    ax.axis("off")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path
