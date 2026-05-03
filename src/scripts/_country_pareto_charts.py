# man_hours: 0.7
"""Static Pareto charts for the country profile.

Produces two horizontal-bar PNGs from the country bundle:

- Avoidance Pareto - which avoidance-phase criteria are most common
  among sites that pass the exclusionary screen. Embedded in the
  ``Interpretation for Site Selection`` section so executives see at a
  glance which constraints unlock the next slice of sites.
- Exclusionary Failure Pareto - which exclusionary criteria most
  often remove a site from consideration in this country. Embedded in
  the ``Exclusionary Failure Pareto`` section.

Layout intentionally mirrors the GUI's Altair Pareto in
``src/atoms_vs_ashes/gui/_results_render_exclusion_diag.py`` for
consistency between interactive and static review.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_avoidance_pareto_png(
    bundle: dict[str, Any], path: Path, *, country_name: str,
) -> Path | None:
    """Write the avoidance Pareto PNG. Returns the file path on success."""
    pareto = bundle.get("avoidance_pareto") or []
    if not pareto:
        return None
    totals = bundle.get("totals") or {}
    n_pass = (
        int(totals.get("n_full_pass", 0))
        + int(totals.get("n_avoidance_flag", 0))
    )
    rows = [
        {
            "label": _wrap(_fullname(row), max_chars=42),
            "n": int(row.get("n_sites") or 0),
            "share": float(row.get("share_of_exclusionary_pass") or 0.0),
            "criterion_id": row.get("criterion_id"),
        }
        for row in pareto
    ]
    title = (
        f"{country_name}: avoidance flags concentrate on a small set of "
        f"criteria ({n_pass} exclusionary-pass sites)"
    )
    subtitle = (
        "Resolving any of these unlocks more sites for Stage 3 review."
    )
    _draw_pareto(
        rows=rows, denominator=n_pass, path=path,
        title=title, subtitle=subtitle, x_label="Share of exclusionary-pass sites",
        bar_color="#d4a017",
    )
    return path


def write_failure_pareto_png(
    bundle: dict[str, Any], path: Path, *, country_name: str,
) -> Path | None:
    """Write the exclusionary-failure Pareto PNG."""
    pareto = bundle.get("exclusionary_failure_pareto") or []
    if not pareto:
        return None
    totals = bundle.get("totals") or {}
    n_country = int(totals.get("n_sites", 0))
    rows = [
        {
            "label": _wrap(_fullname(row), max_chars=42),
            "n": int(row.get("n_sites") or 0),
            "share": float(row.get("share_of_country") or 0.0),
            "criterion_id": row.get("criterion_id"),
        }
        for row in pareto
    ]
    title = (
        f"{country_name}: exclusionary failures by criterion "
        f"({n_country} country sites)"
    )
    subtitle = (
        "Each bar shows how many sites the criterion removes from further "
        "consideration."
    )
    _draw_pareto(
        rows=rows, denominator=n_country, path=path,
        title=title, subtitle=subtitle, x_label="Share of country sites",
        bar_color="#c0392b",
    )
    return path


def _draw_pareto(
    *,
    rows: list[dict[str, Any]],
    denominator: int,
    path: Path,
    title: str,
    subtitle: str,
    x_label: str,
    bar_color: str,
) -> None:
    import matplotlib.pyplot as plt

    rows = sorted(rows, key=lambda r: r["share"])
    height = max(2.6, 0.55 * len(rows) + 1.6)
    fig, ax = plt.subplots(figsize=(10.5, height))
    ax.barh(
        [r["label"] for r in rows],
        [r["share"] * 100 for r in rows],
        color=bar_color, edgecolor="#1c1c1c", linewidth=0.6, height=0.7,
    )
    for i, r in enumerate(rows):
        share_text = f"{r['share'] * 100:.0f}%"
        n_text = f"{r['n']} of {denominator}" if denominator else f"{r['n']}"
        ax.text(
            r["share"] * 100 + 0.6, i,
            f"{share_text}  ({n_text})",
            va="center", ha="left", fontsize=9, color="#1c1c1c",
        )
    max_pct = max((r["share"] * 100 for r in rows), default=0)
    ax.set_xlim(0, max(max_pct * 1.25, 10))
    ax.set_xlabel(x_label)
    ax.set_title(title, fontsize=12, fontweight="bold", loc="left")
    ax.text(
        0.0, 1.02, subtitle,
        transform=ax.transAxes,
        ha="left", va="bottom", fontsize=9, color="#444",
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="x", labelsize=9)
    ax.tick_params(axis="y", labelsize=9)
    ax.grid(axis="x", linestyle=":", alpha=0.4)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _fullname(row: dict[str, Any]) -> str:
    name = row.get("criterion_name") or row.get("criterion_id") or "?"
    cid = row.get("criterion_id") or ""
    return f"{name} ({cid})" if cid and cid not in name else str(name)


def _wrap(text: str, *, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    words = text.split()
    out: list[str] = []
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if len(candidate) > max_chars and line:
            out.append(line)
            line = word
        else:
            line = candidate
    if line:
        out.append(line)
    return "\n".join(out)


__all__ = ["write_avoidance_pareto_png", "write_failure_pareto_png"]
