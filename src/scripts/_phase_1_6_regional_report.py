# man_hours: 0.75
"""Regional sensitivity summary MD writer (``00_regional_summary.md``).

Consumes the all-SMR bands CSV, the NuScale bands CSV and (optionally)
the per-country summary CSV produced by the extended-stages pipeline
and emits a single-file regional overview with A–H band counts at both
scopes, top-site tables and a country roll-up.
"""

from __future__ import annotations

import csv
from pathlib import Path

from scripts._phase_1_6_report_writer import (
    count_bands,
    format_band_counts,
    format_shortlist,
    read_bands,
    stamp_today,
)


def write_regional_report(
    *,
    out_dir: Path,
    stamp: str,
    bands_csv: Path,
    nuscale_bands_csv: Path,
    country_summary_csv: Path | None,
    figures_rel: dict[str, str],
) -> Path:
    """Write ``00_regional_summary.md`` and return its path.

    ``figures_rel`` keys (all optional): ``band_counts_global``,
    ``band_counts_nuscale``, ``oat_top15``, ``jaccard_by_profile``.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "00_regional_summary.md"

    all_rows = read_bands(bands_csv)
    ns_rows = read_bands(nuscale_bands_csv)
    all_counts = count_bands(all_rows)
    ns_counts = count_bands(ns_rows)

    lines: list[str] = []
    lines.append(f"# Regional sensitivity summary — {stamp}")
    lines.append("")
    lines.append(f"_Generated on {stamp_today()} (UTC) from audit CSVs._")
    lines.append("")
    lines.append(
        "This document presents **site stability banding** (A–H) at two scopes:"
    )
    lines.append("")
    lines.append(
        f"- **Regional — all SMRs pooled** ({len(all_rows)} sites)."
    )
    lines.append(
        f"- **Regional — NuScale `nuscale_voygr6` only** ({len(ns_rows)} sites)."
    )
    lines.append("")
    lines.append(
        "Per-country rankings (with local top-K shortlists and within-country "
        "bands) live in `national/`."
    )
    lines.append("")

    _append_section_band_counts(
        lines,
        title="1. Band counts — all SMRs pooled",
        counts=all_counts,
        total=len(all_rows),
        figure_rel=figures_rel.get("band_counts_global"),
        alt_text="A–H band counts (all SMRs)",
    )
    _append_section_band_counts(
        lines,
        title="2. Band counts — NuScale `nuscale_voygr6`",
        counts=ns_counts,
        total=len(ns_rows),
        figure_rel=figures_rel.get("band_counts_nuscale"),
        alt_text="A–H band counts (NuScale)",
    )

    lines.append("## 3. Top sites — NuScale (Band A/B/C, ≤ 25)")
    lines.append("")
    lines.extend(
        format_shortlist(
            [r for r in ns_rows if r["band"] in ("A", "B", "C")], limit=25
        )
    )
    lines.append("")

    lines.append("## 4. Top sites — all SMRs (Band A/B/C, ≤ 25)")
    lines.append("")
    lines.extend(
        format_shortlist(
            [r for r in all_rows if r["band"] in ("A", "B", "C")], limit=25
        )
    )
    lines.append("")

    if country_summary_csv is not None and country_summary_csv.exists():
        _append_country_rollup(lines, country_summary_csv)

    lines.append("## 6. Source artefacts")
    lines.append("")
    lines.append(f"- `{bands_csv.name}` — all-SMR bands.")
    lines.append(f"- `{nuscale_bands_csv.name}` — NuScale bands.")
    if country_summary_csv is not None:
        lines.append(f"- `{country_summary_csv.name}` — country roll-up.")
    lines.append(
        "- Methodology: [`report/methodology/sensitivity_analysis.md`]"
        "(../../methodology/sensitivity_analysis.md)."
    )
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _append_section_band_counts(
    lines: list[str],
    *,
    title: str,
    counts: dict[str, int],
    total: int,
    figure_rel: str | None,
    alt_text: str,
) -> None:
    lines.append(f"## {title}")
    lines.append("")
    lines.extend(format_band_counts(counts, total))
    lines.append("")
    if figure_rel:
        lines.append(f"![{alt_text}]({figure_rel})")
        lines.append("")


def _append_country_rollup(lines: list[str], country_summary_csv: Path) -> None:
    lines.append("## 5. Country roll-up (all-SMR)")
    lines.append("")
    lines.append(
        "| Country | n sites | K (shortlist) | Band A | Band B | Band C "
        "| Mean Jaccard vs baseline top-K |"
    )
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    with country_summary_csv.open("r", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            lines.append(
                f"| {r['country_code']} | {r['n_sites']} | {r['K']} | "
                f"{r.get('band_a_count', '')} | {r.get('band_b_count', '')} | "
                f"{r.get('band_c_count', '')} | "
                f"{r.get('mean_jaccard_vs_baseline_topk', '')} |"
            )
    lines.append("")
