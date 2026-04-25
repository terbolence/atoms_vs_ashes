# man_hours: 1.25
"""Extra audit sections for Phase 1.6.

Renders the OAT importance table, the (A–H) site-banding table and
the per-country summary table from their companion CSV artefacts.
Split from :mod:`_phase_1_6_audit` so every file stays ≤ 300 lines.
"""

from __future__ import annotations

import csv
from pathlib import Path

from atoms_vs_ashes.scoring._band_rules import BAND_DISPLAY_ORDER


def append_importance_table(lines: list[str], csv_path: Path | None) -> None:
    """Append the top-15 OAT importance section."""
    lines.append("## Criterion importance (OAT, top 15)")
    lines.append("")
    if csv_path is None or not csv_path.exists():
        lines.append("_OAT importance artefact not produced for this run._")
        lines.append("")
        return
    with csv_path.open("r", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        lines.append("_OAT importance table is empty._")
        lines.append("")
        return
    lines.append(f"Source: `{csv_path.name}` ({len(rows)} criteria).")
    lines.append("")
    lines.append("| Rank | Criterion | Family | Name | Importance | Mean |Δrank| |")
    lines.append("| ---: | --- | --- | --- | ---: | ---: |")
    for idx, row in enumerate(rows[:15], start=1):
        lines.append(
            f"| {idx} | `{row['criterion_id']}` | {row['family']} | "
            f"{row['criterion_name']} | {row['importance_score']} | "
            f"{row['mean_abs_rank_change']} |"
        )
    lines.append("")


def append_banding_table(
    lines: list[str],
    csv_path: Path | None,
    *,
    heading: str = "Site stability banding",
    scope_hint: str | None = None,
) -> None:
    """Append the A–H site-banding summary and top-tier detail list."""
    lines.append(f"## {heading}")
    lines.append("")
    if scope_hint:
        lines.append(f"_{scope_hint}_")
        lines.append("")
    if csv_path is None or not csv_path.exists():
        lines.append("_Banding artefact not produced for this run._")
        lines.append("")
        return
    with csv_path.open("r", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        lines.append("_Banding CSV is empty._")
        lines.append("")
        return
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["band"]] = counts.get(r["band"], 0) + 1
    lines.append(f"Source: `{csv_path.name}` ({len(rows)} sites).")
    lines.append("")
    lines.append("| Band | Sites | Share |")
    lines.append("| --- | ---: | ---: |")
    total = len(rows)
    for band in BAND_DISPLAY_ORDER:
        n = counts.get(band, 0)
        share = f"{100.0 * n / total:.1f} %" if total else "-"
        lines.append(f"| {band} | {n} | {share} |")
    lines.append("")
    _append_band_detail(lines, rows, "A", "Band A sites (top-5 % in ≥ 80 % of scenarios)")
    _append_band_detail(lines, rows, "B", "Band B sites (top-10 % in ≥ 80 % of scenarios)")


def _append_band_detail(
    lines: list[str], rows: list[dict[str, str]], band: str, heading: str
) -> None:
    members = [r for r in rows if r["band"] == band]
    if not members:
        return
    lines.append(f"### {heading}")
    lines.append("")
    lines.append(
        "| Site | Country | Top-5 % | Top-10 % | Top-30 % |"
    )
    lines.append("| --- | --- | ---: | ---: | ---: |")
    for r in members[:25]:
        top30 = r.get("top30pct_hit_rate", "")
        lines.append(
            f"| {r['site_name']} | {r['country']} | "
            f"{r['top5pct_hit_rate']} | {r['top10pct_hit_rate']} | "
            f"{top30} |"
        )
    if len(members) > 25:
        lines.append(f"| … {len(members) - 25} more | | | | |")
    lines.append("")


def append_country_summary_table(
    lines: list[str],
    csv_path: Path | None,
    *,
    heading: str = "Country roll-up",
) -> None:
    """Append per-country summary section (n, K, bands, Jaccard).

    Consumes the CSV written by
    :func:`atoms_vs_ashes.scoring._country_summary.write_country_summary_csv`.
    """
    lines.append(f"## {heading}")
    lines.append("")
    if csv_path is None or not csv_path.exists():
        lines.append("_Country summary artefact not produced for this run._")
        lines.append("")
        return
    with csv_path.open("r", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        lines.append("_Country summary CSV is empty._")
        lines.append("")
        return
    lines.append(f"Source: `{csv_path.name}` ({len(rows)} countries).")
    lines.append("")
    lines.append(
        "| Country | n sites | K | Band A | Band B | Band C | Mean Jaccard | Min Jaccard |"
    )
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for r in rows:
        lines.append(
            f"| {r['country_code']} | {r['n_sites']} | {r['K']} | "
            f"{r.get('band_a_count', '')} | {r.get('band_b_count', '')} | "
            f"{r.get('band_c_count', '')} | "
            f"{r.get('mean_jaccard_vs_baseline_topk', '')} | "
            f"{r.get('min_jaccard_vs_baseline_topk', '')} |"
        )
    lines.append("")
