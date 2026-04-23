# man_hours: 1.0
"""Extra audit sections for Phase 1.6.

Split from :mod:`_phase_1_6_audit` so every file stays ≤ 300 lines.
Renders the OAT importance table and the site-banding table from
their companion CSV artefacts.
"""

from __future__ import annotations

import csv
from pathlib import Path


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


def append_banding_table(lines: list[str], csv_path: Path | None) -> None:
    """Append the site-banding summary and Band-A detail list."""
    lines.append("## Site stability banding")
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
    lines.append("| Band | Sites |")
    lines.append("| --- | ---: |")
    for band in ("A", "B", "C", "D"):
        lines.append(f"| {band} | {counts.get(band, 0)} |")
    lines.append("")
    band_a = [r for r in rows if r["band"] == "A"]
    if band_a:
        lines.append("### Band A sites (top-5 % in ≥ 80 % of scenarios)")
        lines.append("")
        lines.append("| Site | Country | Top-5 % hit rate | Top-10 % hit rate |")
        lines.append("| --- | --- | ---: | ---: |")
        for r in band_a[:25]:
            lines.append(
                f"| {r['site_name']} | {r['country']} | "
                f"{r['top5pct_hit_rate']} | {r['top10pct_hit_rate']} |"
            )
        if len(band_a) > 25:
            lines.append(f"| … {len(band_a) - 25} more | | | |")
        lines.append("")
