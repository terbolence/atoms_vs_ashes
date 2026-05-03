# man_hours: 0.6
"""Chart writers for reusable site profile prototypes."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_site_charts(
    out_dir: Path,
    detail: dict[str, Any],
    *,
    file_prefix: str,
    site_name: str,
) -> dict[str, str]:
    criterion = f"{file_prefix}_criterion_scores.png"
    family = f"{file_prefix}_family_contributions.png"
    _criterion_scores(out_dir / criterion, detail, site_name)
    _family_contributions(out_dir / family, detail, site_name)
    return {"criterion": criterion, "family": family}


def _criterion_scores(path: Path, detail: dict[str, Any], site_name: str) -> None:
    import matplotlib.pyplot as plt

    rows = [
        row for row in detail.get("all_criterion_scores", [])
        if row.get("score_0_10") is not None
    ]
    rows = sorted(rows, key=lambda row: row["score_0_10"])
    if not rows:
        return
    labels = [row["criterion_id"] for row in rows]
    values = [float(row["score_0_10"]) for row in rows]
    colors = ["#cd5745" if v < 4 else "#e4da3a" if v < 7 else "#45cd85" for v in values]
    height = max(5.5, 0.28 * len(rows))
    fig, ax = plt.subplots(figsize=(8.0, height))
    ax.barh(labels, values, color=colors, edgecolor="#333333", linewidth=0.35)
    ax.set_xlim(0, 10)
    ax.set_xlabel("Criterion score (0-10)")
    ax.set_title(f"{site_name} criterion-score profile")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _family_contributions(path: Path, detail: dict[str, Any], site_name: str) -> None:
    import matplotlib.pyplot as plt

    rows = detail.get("family_contributions", [])
    if not rows:
        return
    labels = [str(row["family"]).upper() for row in rows]
    values = [float(row["weighted_contribution"]) for row in rows]
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    ax.bar(labels, values, color="#4c78a8", edgecolor="#333333", linewidth=0.4)
    ax.set_ylabel("Weighted contribution")
    ax.set_title(f"{site_name} family contribution snapshot")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


__all__ = ["write_site_charts"]
