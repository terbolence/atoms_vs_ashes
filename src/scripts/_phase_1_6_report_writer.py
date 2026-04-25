# man_hours: 0.75
"""Shared primitives for Phase 1.6 extended-banding MD writers.

Kept separate from the per-scope writers so :mod:`_phase_1_6_regional_report`
and :mod:`_phase_1_6_country_report` stay focused and compliant with the
repo's 300-line Python file limit.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from atoms_vs_ashes.scoring._band_rules import BAND_DISPLAY_ORDER

COUNTRY_NAMES = {
    "AL": "albania",
    "AT": "austria",
    "BA": "bosnia_and_herzegovina",
    "BE": "belgium",
    "BG": "bulgaria",
    "BY": "belarus",
    "CH": "switzerland",
    "CY": "cyprus",
    "CZ": "czechia",
    "DE": "germany",
    "DK": "denmark",
    "EE": "estonia",
    "ES": "spain",
    "FI": "finland",
    "FR": "france",
    "GB": "united_kingdom",
    "GR": "greece",
    "HR": "croatia",
    "HU": "hungary",
    "IE": "ireland",
    "IT": "italy",
    "LT": "lithuania",
    "LU": "luxembourg",
    "LV": "latvia",
    "MD": "moldova",
    "ME": "montenegro",
    "MK": "north_macedonia",
    "NL": "netherlands",
    "NO": "norway",
    "PL": "poland",
    "PT": "portugal",
    "RO": "romania",
    "RS": "serbia",
    "SE": "sweden",
    "SI": "slovenia",
    "SK": "slovakia",
    "TR": "turkey",
    "UA": "ukraine",
    "XK": "kosovo",
}


def country_slug(country_code: str) -> str:
    """Return ``CC_name`` slug for filenames (``RO_romania``)."""
    name = COUNTRY_NAMES.get(country_code, country_code.lower())
    return f"{country_code}_{name}"


def country_display_name(country_code: str) -> str:
    """Return a presentable country name (``Romania`` for ``RO``)."""
    return COUNTRY_NAMES.get(country_code, country_code).replace(
        "_", " "
    ).title()


def read_bands(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def count_bands(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for r in rows:
        counts[r["band"]] += 1
    return dict(counts)


def format_band_counts(counts: dict[str, int], total: int) -> list[str]:
    lines = ["| Band | Sites | Share |", "| --- | ---: | ---: |"]
    for band in BAND_DISPLAY_ORDER:
        n = counts.get(band, 0)
        share = f"{100.0 * n / total:.1f} %" if total else "-"
        lines.append(f"| {band} | {n} | {share} |")
    ranked = sum(
        counts.get(b, 0) for b in ("A", "B", "C", "D", "E", "F", "G")
    )
    share_ranked = f"{100.0 * ranked / total:.1f} %" if total else "-"
    lines.append(f"| **A–G (named)** | **{ranked}** | **{share_ranked}** |")
    return lines


def format_shortlist(
    rows: list[dict[str, str]], *, limit: int = 25
) -> list[str]:
    lines = [
        "| Rank | Site | Country | Band | Top-5 % rate | Top-10 % rate | Top-30 % rate |",
        "| ---: | --- | --- | :---: | ---: | ---: | ---: |",
    ]
    for idx, r in enumerate(rows[:limit], start=1):
        lines.append(
            f"| {idx} | {r['site_name']} | {r['country']} | {r['band']} | "
            f"{r['top5pct_hit_rate']} | {r['top10pct_hit_rate']} | "
            f"{r['top30pct_hit_rate']} |"
        )
    if len(rows) > limit:
        lines.append(f"| … {len(rows) - limit} more | | | | | | |")
    return lines


def stamp_today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")
