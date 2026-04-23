# man_hours: 1.5
"""Figure generators for the Phase 1.6 sensitivity suite.

Reads the CSV artefacts (``*_oat_importance.csv``, ``*_site_bands.csv``)
and parses the consolidated audit markdown
(``*_phase1_6_sensitivity.md``) to emit four PNGs suitable for the
methodology report and expert-review packs.

Intentionally avoids any DB access: every number comes from files that
the sensitivity driver already writes. Requires matplotlib, shipped as
the optional ``report_plots`` extra (``pip install -e '.[report_plots]'``).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless; must precede pyplot import
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

TOP_OAT_N = 15
TOP_COUNTRIES_N = 12
BAND_ORDER: tuple[str, ...] = ("A", "B", "C", "D")
_PROFILE_ORDER_HINT: tuple[str, ...] = (
    "country_balanced",
    "w_EP_minus_20",
    "w_EP_plus_20",
    "w_HI_minus_20",
    "w_HI_plus_20",
    "w_NH_minus_20",
    "w_NH_plus_20",
    "w_NS_minus_20",
    "w_NS_plus_20",
    "w_RI_minus_20",
    "w_RI_plus_20",
    "threshold_minus_25",
    "threshold_plus_25",
    "mc_10000",
)


@dataclass(frozen=True)
class FigurePaths:
    """Absolute output paths of the four PNG artefacts."""

    oat_top15: Path
    jaccard_by_profile: Path
    band_counts: Path
    country_top10pct: Path


# ---------------------------------------------------------------------------
# Markdown table parser
# ---------------------------------------------------------------------------


def _extract_section(md: str, heading_substr: str) -> str:
    """Return the body between ``## <...heading_substr...>`` and the next ``## ``.

    Raises ``LookupError`` if the heading is not found; downstream callers
    surface the error rather than silently drawing empty charts.
    """
    lines = md.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if line.startswith("## ") and heading_substr.lower() in line.lower():
            start = idx + 1
            break
    if start is None:
        raise LookupError(f"heading containing {heading_substr!r} not found")
    end = len(lines)
    for idx in range(start, len(lines)):
        if lines[idx].startswith("## "):
            end = idx
            break
    return "\n".join(lines[start:end])


def _row_cells(row: str) -> list[str]:
    stripped = row.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def _find_table_block(section_body: str) -> tuple[list[str], list[list[str]]]:
    """Return (header cells, data rows) of the first pipe-table in a section.

    The Phase 1.6 audit sometimes has a header row with literal pipes
    (``Mean |Δ|``) that inflate the header cell count vs. the separator.
    We trust the **separator row** for column count and align data rows
    to that count; header is kept verbatim for captioning.
    """
    rows = [ln for ln in section_body.splitlines() if ln.strip().startswith("|")]
    if len(rows) < 3:
        raise LookupError("expected a markdown pipe table (header | sep | rows)")
    header_cells = _row_cells(rows[0])
    sep_cells = _row_cells(rows[1])
    if not all(set(c.replace(":", "").strip()) <= {"-", ""} for c in sep_cells):
        raise LookupError("second line is not a pipe-table separator")
    ncols = len(sep_cells)
    data: list[list[str]] = []
    for row in rows[2:]:
        cells = _row_cells(row)
        if len(cells) == ncols:
            data.append(cells)
    return header_cells, data


# ---------------------------------------------------------------------------
# Helpers: CSV loaders
# ---------------------------------------------------------------------------


def _load_oat(oat_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(oat_csv)
    df = df.sort_values("importance_score", ascending=False)
    return df.head(TOP_OAT_N)


def _load_bands(bands_csv: Path) -> pd.Series:
    df = pd.read_csv(bands_csv)
    counts = df["band"].value_counts()
    return pd.Series({b: int(counts.get(b, 0)) for b in BAND_ORDER})


# ---------------------------------------------------------------------------
# Helpers: audit-MD slices
# ---------------------------------------------------------------------------


def _profiles_and_jaccard(md_text: str) -> pd.DataFrame:
    body = _extract_section(md_text, "Top-N stability")
    _, data = _find_table_block(body)
    profiles: list[str] = []
    jaccard10: list[float] = []
    mean_drift: list[float] = []
    for cells in data:
        profile = cells[0].strip("` ")
        try:
            jaccard10.append(float(cells[5]))
            mean_drift.append(float(cells[6]))
        except (ValueError, IndexError):
            continue
        profiles.append(profile)
    df = pd.DataFrame(
        {
            "profile": profiles,
            "jaccard_top10pct": jaccard10,
            "mean_abs_dscore": mean_drift,
        }
    )
    ordering = {name: idx for idx, name in enumerate(_PROFILE_ORDER_HINT)}
    df["_ord"] = df["profile"].map(lambda p: ordering.get(p, 99))
    df = df.sort_values(["_ord", "profile"]).drop(columns="_ord").reset_index(drop=True)
    return df


def _country_counts(md_text: str) -> pd.Series:
    body = _extract_section(md_text, "Country balance")
    _, data = _find_table_block(body)
    entries: list[tuple[str, int]] = []
    for cells in data:
        country = cells[0].strip("` ")
        try:
            entries.append((country, int(cells[1])))
        except (ValueError, IndexError):
            continue
    entries.sort(key=lambda t: t[1], reverse=True)
    entries = entries[:TOP_COUNTRIES_N]
    return pd.Series({c: n for c, n in entries})


# ---------------------------------------------------------------------------
# Individual plots
# ---------------------------------------------------------------------------


def plot_oat_top15(oat_csv: Path, out_path: Path) -> Path:
    df = _load_oat(oat_csv)
    labels = [f"{cid}  {name}" for cid, name in zip(df["criterion_id"], df["criterion_name"])]
    fig, ax = plt.subplots(figsize=(9.5, 6.5))
    ax.barh(labels[::-1], df["importance_score"].to_numpy()[::-1])
    ax.set_xlabel("Importance score (mean |Δrank| / N pairs)")
    ax.set_title(f"OAT importance — top {len(df)} criteria")
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_band_counts(bands_csv: Path, out_path: Path) -> Path:
    counts = _load_bands(bands_csv)
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    bars = ax.bar(counts.index.tolist(), counts.to_numpy())
    for rect, value in zip(bars, counts.to_numpy()):
        ax.text(
            rect.get_x() + rect.get_width() / 2,
            rect.get_height(),
            f"{int(value)}",
            ha="center",
            va="bottom",
        )
    ax.set_xlabel("Stability band")
    ax.set_ylabel("Sites")
    ax.set_title(f"Site stability banding (N = {int(counts.sum())})")
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_jaccard_by_profile(audit_md: Path, out_path: Path) -> Path:
    md_text = audit_md.read_text(encoding="utf-8")
    df = _profiles_and_jaccard(md_text)
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    bars = ax.bar(df["profile"], df["jaccard_top10pct"])
    ax.axhline(0.85, linestyle="--", linewidth=1, color="grey", label="robust threshold (0.85)")
    ax.axhline(0.70, linestyle=":", linewidth=1, color="grey", label="MC threshold (0.70)")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Jaccard@10 %")
    ax.set_title("Top-10 % ranking stability vs. baseline")
    ax.tick_params(axis="x", labelrotation=45)
    for label in ax.get_xticklabels():
        label.set_ha("right")
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    ax.legend(loc="lower right", fontsize="small")
    for rect, value in zip(bars, df["jaccard_top10pct"].to_numpy()):
        ax.text(
            rect.get_x() + rect.get_width() / 2,
            rect.get_height() + 0.01,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_country_balance(audit_md: Path, out_path: Path) -> Path:
    md_text = audit_md.read_text(encoding="utf-8")
    counts = _country_counts(md_text)
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    countries = counts.index.tolist()
    values = counts.to_numpy()
    ax.barh(countries[::-1], values[::-1])
    ax.set_xlabel("Pairs in baseline top-10 %")
    ax.set_title("Country balance — baseline top-10 % slice")
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    for idx, value in enumerate(values[::-1]):
        ax.text(value, idx, f" {int(value)}", va="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def save_all_figures(
    out_dir: Path,
    *,
    oat_csv: Path,
    bands_csv: Path,
    audit_md: Path,
) -> FigurePaths:
    """Generate the four Phase 1.6 figures and return their paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = FigurePaths(
        oat_top15=out_dir / "oat_top15.png",
        jaccard_by_profile=out_dir / "jaccard_by_profile.png",
        band_counts=out_dir / "band_counts.png",
        country_top10pct=out_dir / "country_top10pct.png",
    )
    plot_oat_top15(oat_csv, paths.oat_top15)
    plot_jaccard_by_profile(audit_md, paths.jaccard_by_profile)
    plot_band_counts(bands_csv, paths.band_counts)
    plot_country_balance(audit_md, paths.country_top10pct)
    return paths
