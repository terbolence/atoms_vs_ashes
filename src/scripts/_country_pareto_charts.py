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
            "label": _wrap(_fullname(row), max_chars=38),
            "n": int(row.get("n_sites") or 0),
            "share": float(row.get("share_of_exclusionary_pass") or 0.0),
            "criterion_id": row.get("criterion_id"),
        }
        for row in pareto
    ]
    title = (
        f"{country_name}: avoidance flags concentrate on a small set "
        f"of criteria ({n_pass} exclusionary-pass sites)"
    )
    subtitle = (
        "Resolving any of these unlocks more sites for Stage 3 review."
    )
    _draw_pareto(
        rows=rows, denominator=n_pass, path=path,
        title=title, subtitle=subtitle,
        x_label="Share of exclusionary-pass sites",
        bar_color="#d4a017",
        legend_label="Sites flagged on this avoidance criterion",
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
            "label": _wrap(_fullname(row), max_chars=38),
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
        title=title, subtitle=subtitle,
        x_label="Share of country sites",
        bar_color="#c0392b",
        legend_label="Sites failing this exclusionary criterion",
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
    legend_label: str,
) -> None:
    import textwrap

    import matplotlib.patches as mpatches
    import matplotlib.pyplot as plt

    rows = sorted(rows, key=lambda r: r["share"])
    n_bars = max(1, len(rows))
    n_label_lines = sum(r["label"].count("\n") + 1 for r in rows)
    bar_band = 0.55 * n_bars + 0.18 * (n_label_lines - n_bars)
    height = max(3.4, bar_band + 2.4)
    fig, ax = plt.subplots(
        figsize=(11.5, height), constrained_layout=True,
    )
    ax.barh(
        [r["label"] for r in rows],
        [r["share"] * 100 for r in rows],
        color=bar_color, edgecolor="#1c1c1c", linewidth=0.6, height=0.7,
        label=legend_label,
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
    headroom = 28 if denominator and denominator > 0 else 18
    ax.set_xlim(0, max(max_pct + headroom, 30))
    ax.set_xlabel(x_label, fontsize=10)
    wrapped_title = "\n".join(
        textwrap.wrap(title, width=80, break_long_words=False),
    )
    wrapped_subtitle = "\n".join(
        textwrap.wrap(subtitle, width=92, break_long_words=False),
    )
    fig.suptitle(
        wrapped_title, fontsize=12, fontweight="bold",
        x=0.02, ha="left",
    )
    ax.set_title(
        wrapped_subtitle, fontsize=9, color="#444",
        loc="left", pad=8,
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="x", labelsize=9)
    ax.tick_params(axis="y", labelsize=9)
    ax.grid(axis="x", linestyle=":", alpha=0.4)
    legend_patch = mpatches.Patch(color=bar_color, label=legend_label)
    ax.legend(
        handles=[legend_patch],
        loc="lower right", frameon=False, fontsize=9,
    )
    fig.savefig(path, dpi=180, bbox_inches="tight")
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
