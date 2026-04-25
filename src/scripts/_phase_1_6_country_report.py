# man_hours: 0.75
"""Per-country sensitivity MD writer (one file per ISO2 country).

Emits ``national/{CC_name}.md`` with a ranked shortlist (all-SMR and
NuScale), within-country bands, embedded figure link and a plain-English
robustness sentence for executive readers.
"""

from __future__ import annotations

from pathlib import Path

from atoms_vs_ashes.scoring._band_rules import BAND_DISPLAY_ORDER
from scripts._phase_1_6_report_writer import (
    count_bands,
    country_display_name,
    country_slug,
    format_shortlist,
    read_bands,
    stamp_today,
)


def write_country_report(
    *,
    out_dir: Path,
    stamp: str,
    country_code: str,
    bands_csv_all_smr: Path,
    bands_csv_nuscale: Path,
    figure_rel: str | None = None,
) -> Path:
    """Write ``national/{CC_name}.md`` and return its path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{country_slug(country_code)}.md"

    all_rows = read_bands(bands_csv_all_smr)
    ns_rows = read_bands(bands_csv_nuscale)
    n = len(all_rows)
    n_ns = len(ns_rows)
    all_counts = count_bands(all_rows)
    ns_counts = count_bands(ns_rows)
    scenarios_total = all_rows[0]["scenarios_total"] if all_rows else "0"
    name = country_display_name(country_code)

    lines: list[str] = []
    lines.append(
        f"# {name} ({country_code}) — sensitivity shortlist — {stamp}"
    )
    lines.append("")
    lines.append(f"_Generated on {stamp_today()} (UTC)._")
    lines.append("")
    lines.append("## Envelope")
    lines.append("")
    lines.append(f"- Scored sites (all-SMR pool): **{n}**.")
    lines.append(f"- Scored sites (NuScale pool): **{n_ns}**.")
    lines.append(f"- Non-baseline scenarios: **{scenarios_total}**.")
    lines.append(
        "- Within-country top-5 / 10 / 30 % percentiles are computed on "
        "the local pool, so **bands reflect national competitiveness**."
    )
    lines.append("")

    if figure_rel is not None:
        lines.append(f"![Top sites in {name}]({figure_rel})")
        lines.append("")

    lines.append("## Ranked shortlist — all SMRs pooled (top 10)")
    lines.append("")
    lines.extend(format_shortlist(all_rows, limit=10))
    lines.append("")
    lines.append(
        "**Band counts:** "
        + ", ".join(f"{b}={all_counts.get(b, 0)}" for b in BAND_DISPLAY_ORDER)
        + "."
    )
    lines.append("")

    lines.append("## Ranked shortlist — NuScale `nuscale_voygr6` (top 10)")
    lines.append("")
    lines.extend(format_shortlist(ns_rows, limit=10))
    lines.append("")
    lines.append(
        "**NuScale band counts:** "
        + ", ".join(f"{b}={ns_counts.get(b, 0)}" for b in BAND_DISPLAY_ORDER)
        + "."
    )
    lines.append("")

    lines.append("## Interpretation")
    lines.append("")
    a_b_c = sum(all_counts.get(b, 0) for b in ("A", "B", "C"))
    lines.append(
        f"- Sites in Bands A–C (within-country robust top tier): **{a_b_c}**."
    )
    lines.append(
        "- Band A / B sites are in the local top-5 % / 10 % slice in "
        "≥ 80 % of the 14 non-baseline scenarios — the defensible "
        "national shortlist under perturbation."
    )
    lines.append(
        "- Sources: "
        f"`{bands_csv_all_smr.name}`, `{bands_csv_nuscale.name}`."
    )
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
