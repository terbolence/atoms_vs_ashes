# man_hours: 1.5
"""Figures for national sensitivity ranking artefacts."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402


def _read(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def plot_national_rank_delta_heatmap(summary_csv: Path, out_path: Path) -> Path:
    """Heatmap of mean |Δnational rank| by country and profile."""
    df = _read(summary_csv)
    if df.empty:
        return _empty(out_path, "No national rank-delta rows")
    df = df[df["metric"].eq("profile_rank_delta") if "metric" in df else True]
    if df.empty:
        return _empty(out_path, "No profile-rank national sensitivity rows")
    pivot = df.pivot_table(
        index="country_code",
        columns="weight_profile",
        values="mean_abs_rank_delta",
        aggfunc="mean",
    ).fillna(0.0)
    fig, ax = plt.subplots(figsize=(max(8, 0.45 * len(pivot.columns)), 6))
    im = ax.imshow(pivot.to_numpy(), aspect="auto")
    ax.set_xticks(range(len(pivot.columns)), pivot.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(pivot.index)), pivot.index)
    ax.set_title("National sensitivity — mean |Δrank| by profile")
    ax.set_xlabel("Sensitivity profile")
    ax.set_ylabel("Country")
    fig.colorbar(im, ax=ax, label="Mean |Δnational rank|")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_national_oat_heatmap(oat_csv: Path, out_path: Path) -> Path:
    """Heatmap of top family-level national OAT rank movement by country."""
    df = _read(oat_csv)
    if df.empty:
        return _empty(out_path, "No national OAT rows")
    grouped = (
        df.groupby(["country_code", "family"], as_index=False)
        ["mean_abs_rank_change"].mean()
    )
    pivot = grouped.pivot_table(
        index="country_code",
        columns="family",
        values="mean_abs_rank_change",
        aggfunc="mean",
    ).fillna(0.0)
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(pivot.to_numpy(), aspect="auto")
    ax.set_xticks(range(len(pivot.columns)), pivot.columns)
    ax.set_yticks(range(len(pivot.index)), pivot.index)
    ax.set_title("National OAT — mean |Δrank| by family")
    ax.set_xlabel("Criterion family")
    ax.set_ylabel("Country")
    fig.colorbar(im, ax=ax, label="Mean |Δnational rank|")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_small_n_diagnostic(summary_csv: Path, out_path: Path) -> Path:
    """Bar chart of eligible pairs per country×SMR slice."""
    df = _read(summary_csv)
    if df.empty:
        return _empty(out_path, "No national summary rows")
    base = df.drop_duplicates(["country_code", "smr_key"])
    base = base.sort_values(["country_code", "smr_key"])
    labels = [f"{r.country_code}-{r.smr_key}" for r in base.itertuples()]
    values = base["n_pairs"].astype(int).to_list()
    fig, ax = plt.subplots(figsize=(max(8, 0.3 * len(labels)), 4.5))
    ax.bar(labels, values)
    ax.set_title("National sensitivity diagnostic — eligible pairs")
    ax.set_xlabel("Country-SMR slice")
    ax.set_ylabel("Scored pairs")
    ax.tick_params(axis="x", labelrotation=90)
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_country_rank_delta_bars(
    summary_csv: Path, figures_dir: Path,
) -> dict[str, Path]:
    """One country figure: mean |Δrank| by sensitivity profile."""
    df = _read(summary_csv)
    if df.empty:
        return {}
    out: dict[str, Path] = {}
    figures_dir.mkdir(parents=True, exist_ok=True)
    for country, sub in df.groupby("country_code"):
        sub = sub.sort_values("mean_abs_rank_delta", ascending=False)
        if sub.empty:
            continue
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.barh(
            sub["weight_profile"].astype(str)[::-1],
            sub["mean_abs_rank_delta"].fillna(0).astype(float)[::-1],
        )
        ax.set_title(f"{country} — national rank movement by profile")
        ax.set_xlabel("Mean |Δnational rank|")
        ax.grid(axis="x", linestyle=":", alpha=0.5)
        fig.tight_layout()
        path = figures_dir / f"{country}_national_rank_delta.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        out[str(country)] = path
    return out


def plot_mc_rank_probability(mc_csv: Path, out_path: Path) -> Path:
    """Global top-sites dot chart for MC national-rank probabilities."""
    df = _read(mc_csv)
    if df.empty:
        return _empty(out_path, "No national MC rank rows")
    df = df.sort_values(["p_rank_1", "p_rank_le_3"], ascending=False).head(20)
    labels = [f"{r.country_code}-{str(r.site_id)[:8]}" for r in df.itertuples()]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(df["p_rank_1"], labels, label="P(rank=1)")
    ax.scatter(df["p_rank_le_3"], labels, label="P(rank<=3)")
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("Probability")
    ax.set_title("National MC rank probabilities — top candidate pairs")
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    ax.legend(loc="lower right")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def build_national_sensitivity_figures(
    *,
    summary_csv: Path,
    oat_csv: Path,
    mc_csv: Path,
    figures_dir: Path,
) -> tuple[dict[str, Path], dict[str, Path]]:
    """Build global and per-country national sensitivity figures."""
    figures_dir.mkdir(parents=True, exist_ok=True)
    global_figures = {
        "national_rank_delta_heatmap": plot_national_rank_delta_heatmap(
            summary_csv, figures_dir / "national_rank_delta_heatmap.png",
        ),
        "national_oat_heatmap": plot_national_oat_heatmap(
            oat_csv, figures_dir / "national_oat_heatmap.png",
        ),
        "national_small_n_diagnostic": plot_small_n_diagnostic(
            summary_csv, figures_dir / "national_small_n_diagnostic.png",
        ),
        "national_mc_rank_probability": plot_mc_rank_probability(
            mc_csv, figures_dir / "national_mc_rank_probability.png",
        ),
    }
    per_country = plot_country_rank_delta_bars(summary_csv, figures_dir)
    return global_figures, per_country


def _empty(out_path: Path, message: str) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 2))
    ax.text(0.5, 0.5, message, ha="center", va="center")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


__all__ = ["build_national_sensitivity_figures"]
