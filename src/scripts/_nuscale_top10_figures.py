# man_hours: 1.0
"""Figure factory for the NuScale top-10-per-country report.

Produces two PNGs per country directly from the data structures emitted
by :mod:`scripts._nuscale_top10_query`:

- ``<CC>_composite_top10.png`` — horizontal bar chart of composite
  scores with low/high uncertainty error bars.
- ``<CC>_family_heatmap.png`` — N×5 matrix of family-level scores
  (NH / HI / RI / EP / NS) per shortlisted site.

Backend is forced to ``Agg`` so the script can run head-less in CI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from scripts._nuscale_top10_query import FAMILIES


_FAMILY_LABELS: dict[str, str] = {
    "NH": "NH (Natural hazards)",
    "HI": "HI (Human-induced hazards)",
    "RI": "RI (Radiological / waste)",
    "EP": "EP (Emergency planning)",
    "NS": "NS (Non-safety / siting)",
}


def _short_label(name: str, max_chars: int = 24) -> str:
    if len(name) <= max_chars:
        return name
    return name[: max_chars - 1] + "…"


def render_composite_chart(
    *,
    country_code: str,
    country_name: str,
    rows: Sequence[dict[str, Any]],
    out_path: Path,
) -> Path:
    """Horizontal bar chart of composite ± UI for one country."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        fig, ax = plt.subplots(figsize=(6, 1.5))
        ax.text(0.5, 0.5, "No NuScale composites", ha="center", va="center")
        ax.axis("off")
        fig.savefig(out_path, dpi=120, bbox_inches="tight")
        plt.close(fig)
        return out_path

    labels = [_short_label(r["site_name"]) for r in rows]
    composites = [float(r.get("composite_score") or 0) for r in rows]
    lows = [
        float(r.get("composite_score_low") or v)
        for r, v in zip(rows, composites)
    ]
    highs = [
        float(r.get("composite_score_high") or v)
        for r, v in zip(rows, composites)
    ]
    err_low = [max(0.0, c - lo) for c, lo in zip(composites, lows)]
    err_high = [max(0.0, hi - c) for c, hi in zip(composites, highs)]

    fig, ax = plt.subplots(figsize=(8, max(2.0, 0.42 * len(rows) + 0.7)))
    y_pos = np.arange(len(rows))[::-1]
    ax.barh(
        y_pos, composites, color="#1f77b4", alpha=0.85,
        xerr=[err_low, err_high], capsize=3, ecolor="#444444",
    )
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Composite score (0–10) — error bars show the UI low/high")
    ax.set_xlim(0, 10)
    ax.set_title(
        f"{country_code} {country_name} — NuScale (VOYGR-6) composite shortlist"
    )
    for i, c in enumerate(composites):
        ax.text(
            c + 0.1, y_pos[i], f"{c:.2f}",
            va="center", ha="left", fontsize=9, color="#222",
        )
    ax.grid(axis="x", linestyle=":", alpha=0.4)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return out_path


def render_family_heatmap(
    *,
    country_code: str,
    country_name: str,
    rows: Sequence[dict[str, Any]],
    family_scores: dict[Any, dict[str, float]],
    out_path: Path,
) -> Path:
    """Family-level (NH/HI/RI/EP/NS) score heatmap per shortlisted site."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        fig, ax = plt.subplots(figsize=(6, 1.5))
        ax.text(0.5, 0.5, "No NuScale composites", ha="center", va="center")
        ax.axis("off")
        fig.savefig(out_path, dpi=120, bbox_inches="tight")
        plt.close(fig)
        return out_path

    labels = [_short_label(r["site_name"]) for r in rows]
    matrix = np.full((len(rows), len(FAMILIES)), np.nan, dtype=float)
    for i, r in enumerate(rows):
        scores = family_scores.get(r["site_id"], {})
        for j, fam in enumerate(FAMILIES):
            v = scores.get(fam)
            if v is not None:
                matrix[i, j] = v

    fig, ax = plt.subplots(figsize=(7, max(2.2, 0.42 * len(rows) + 1.0)))
    cmap = plt.get_cmap("RdYlGn")
    im = ax.imshow(matrix, cmap=cmap, vmin=0, vmax=10, aspect="auto")
    ax.set_xticks(range(len(FAMILIES)))
    ax.set_xticklabels([_FAMILY_LABELS[f] for f in FAMILIES], rotation=20, ha="right")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_title(
        f"{country_code} {country_name} — NuScale family scores (0–10)"
    )
    for i in range(len(rows)):
        for j in range(len(FAMILIES)):
            v = matrix[i, j]
            if not np.isnan(v):
                ax.text(
                    j, i, f"{v:.1f}",
                    ha="center", va="center",
                    color="black" if 3.5 <= v <= 7.0 else "white", fontsize=9,
                )
    cbar = fig.colorbar(im, ax=ax, shrink=0.85)
    cbar.set_label("Family score (0 = worst, 10 = best)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return out_path


def render_all_for_country(
    *,
    country_code: str,
    country_name: str,
    rows: Sequence[dict[str, Any]],
    family_scores: dict[Any, dict[str, float]],
    out_dir: Path,
) -> dict[str, Path]:
    """Render both per-country figures into ``out_dir``."""
    composite = render_composite_chart(
        country_code=country_code,
        country_name=country_name,
        rows=rows,
        out_path=out_dir / f"{country_code}_composite_top10.png",
    )
    heatmap = render_family_heatmap(
        country_code=country_code,
        country_name=country_name,
        rows=rows,
        family_scores=family_scores,
        out_path=out_dir / f"{country_code}_family_heatmap.png",
    )
    return {"composite": composite, "heatmap": heatmap}


__all__ = [
    "render_composite_chart",
    "render_family_heatmap",
    "render_all_for_country",
]
