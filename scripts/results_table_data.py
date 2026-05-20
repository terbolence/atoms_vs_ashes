# man_hours: 2.8
"""Data selection and Markdown rendering for the v1.2 results table."""

from __future__ import annotations

import csv
import re
import shutil
from pathlib import Path

from results_table_flags import flag_note, site_surface_area
from results_table_model import (
    COUNTRY_NAMES,
    COUNTRY_ORDER,
    CSV_COLUMNS,
    DATA_DIR,
    FAILURE_SECTION,
    FIGURES_DIR,
    NO_PASS_COUNTRIES,
    PUBLISHED_COUNTRIES,
    SiteRow,
)


def _truthy(value: str) -> bool:
    return value.strip().lower() == "true"


def _format_number(value: str, decimals: int = 3) -> str:
    if not value:
        return ""
    try:
        return f"{float(value):.{decimals}f}".rstrip("0").rstrip(".")
    except ValueError:
        return value


def _format_probability(value: str) -> str:
    if not value:
        return ""
    try:
        return f"{float(value) * 100:.0f}%"
    except ValueError:
        return value


def _mc_interval(row: dict[str, str]) -> str:
    low = _format_number(row.get("composite_score_low", ""))
    high = _format_number(row.get("composite_score_high", ""))
    if low and high:
        return f"{low} to {high}"
    return ""


def _status_and_note(row: dict[str, str]) -> tuple[str, str, str]:
    if not _truthy(row.get("passed_exclusionary", "")):
        return (
            "Excluded at screening",
            "Fail",
            "Exclusionary criterion triggered; see the country/site profile for criterion detail.",
        )
    if _truthy(row.get("passed_avoidance", "")):
        return (
            "Exclusionary pass; no avoidance flag",
            "Pass",
            "No avoidance flag recorded in the v1.2 ledger.",
        )
    return (
        "Exclusionary pass; avoidance flag",
        "Pass",
        "Avoidance flag recorded in the v1.2 ledger.",
    )


def _sort_key(row: dict[str, str]) -> tuple[int, float]:
    rank = row.get("national_rank", "").strip()
    if rank:
        try:
            return (0, float(rank))
        except ValueError:
            pass
    score = row.get("composite_score", "").strip()
    try:
        return (1, -float(score))
    except ValueError:
        return (2, 0.0)


def ledger_rows(country_code: str) -> list[dict[str, str]]:
    path = DATA_DIR / f"{country_code}_site_ledger.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def selected_rows(country_code: str, rows: list[dict[str, str]]) -> list[dict[str, str]]:
    if country_code == "RO":
        return sorted(rows, key=_sort_key)
    passing = [row for row in rows if _truthy(row.get("passed_exclusionary", ""))]
    return sorted(passing, key=_sort_key)[:5]


def _site_row(country_code: str, row: dict[str, str]) -> SiteRow:
    status, exclusionary_outcome, note = _status_and_note(row)
    site_name = row.get("name", "").strip()
    passed_exclusionary = _truthy(row.get("passed_exclusionary", ""))
    passed_avoidance = _truthy(row.get("passed_avoidance", ""))
    area = site_surface_area(country_code, site_name)
    return SiteRow(
        country_code=country_code,
        country=COUNTRY_NAMES[country_code],
        rank=row.get("national_rank", "").strip() or "Not ranked",
        site=site_name,
        status=status,
        power_export_proxy_mw=_format_number(row.get("installed_capacity_mw", ""), decimals=1),
        site_surface_area_ha=_format_number(str(area), decimals=1) if area is not None else "",
        composite_score=_format_number(row.get("composite_score", "")),
        mc_interval=_mc_interval(row),
        national_stability_band=row.get("national_band", "").strip(),
        top_tier_probability=_format_probability(row.get("national_top10pct_hit_rate", "")),
        exclusionary_outcome=exclusionary_outcome,
        avoidance_or_failure_note=flag_note(
            country_code,
            site_name,
            passed_exclusionary=passed_exclusionary,
            passed_avoidance=passed_avoidance,
        ) if note else note,
    )


def _parse_no_pass_summaries() -> dict[str, str]:
    if not FAILURE_SECTION.exists():
        return {}
    text = FAILURE_SECTION.read_text(encoding="utf-8")
    summaries: dict[str, str] = {}
    pattern = r"^- \*\*(?P<country>.+?) \((?P<code>[A-Z]{2})\)\*\* - (?P<text>.+)$"
    for match in re.finditer(pattern, text, re.MULTILINE):
        summaries[match.group("code")] = match.group("text").strip()
    return summaries


def _copy_map(country_code: str, assets_dir: Path) -> str | None:
    source = FIGURES_DIR / f"{country_code}_site_status_map.png"
    if not source.exists():
        return None
    assets_dir.mkdir(parents=True, exist_ok=True)
    target = assets_dir / source.name
    shutil.copy2(source, target)
    return f"{assets_dir.name}/{target.name}"


def _escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def _markdown_table(rows: list[SiteRow]) -> str:
    table_rows = [[
        "Rank",
        "Site",
        "Status",
        "Power export proxy (MW)",
        "Site surface area (ha)",
        "Score",
        "MC interval",
        "Band",
        "Top-tier probability",
        "Exclusionary outcome",
        "Avoidance / failure note",
    ], [":---:", ":---", ":---", "---:", "---:", "---:", ":---:", ":---:", "---:", ":---:", ":---"]]
    for row in rows:
        table_rows.append([
            row.rank,
            row.site,
            row.status,
            row.power_export_proxy_mw,
            row.site_surface_area_ha,
            row.composite_score,
            row.mc_interval,
            row.national_stability_band,
            row.top_tier_probability,
            row.exclusionary_outcome,
            row.avoidance_or_failure_note,
        ])
    return "\n".join(
        "| " + " | ".join(_escape_cell(cell) for cell in table_row) + " |"
        for table_row in table_rows
    )


def _write_csv(path: Path, rows: list[SiteRow]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: getattr(row, name) for name in CSV_COLUMNS})


def build_results_markdown(markdown_path: Path, csv_path: Path, output_stem: str) -> dict[str, int]:
    assets_dir = markdown_path.parent / f"{output_stem}_assets"
    rows_for_csv: list[SiteRow] = []
    no_pass_summaries = _parse_no_pass_summaries()
    parts = [
        "# Atoms vs Ashes Results Table",
        "",
        "This companion deliverable is an executive screening table for Central, Eastern and Southern European coal and thermal sites that may warrant SMR follow-up. It uses the same country ledgers and national Monte Carlo sensitivity basis as the main report. The published-country sections show the top five exclusionary-pass sites in each country, except Romania, where the full national ledger is shown. Albania, Slovenia and Kosovo are listed separately because the consolidated screen contains no exclusionary-pass brownfield site for those portfolios.",
        "",
        "The table is designed to answer a board-level question: which assets deserve the next euro of diligence, and why. A reliable answer requires more than a manual list of plant names. Each site has to be passed through exclusionary safety gates, avoidance flags, national scoring, sensitivity bands, map context, legacy power capacity and site-area evidence. A programmatic workflow applies the same rules to every country, expands Romania to its full ledger without hand selection, and allows the list to be rebuilt when evidence, maps or assumptions change.",
        "",
        "Power export proxy reports legacy installed plant capacity where available. It is a screening proxy for existing power-infrastructure scale, not a confirmed SMR export capacity or grid-connection right. Site surface area reports the current screened site area where available. It supports early land-envelope screening, but it does not prove ownership, contiguous developable land, permitting status or final SMR layout suitability.",
        "",
    ]

    countries_with_rows = 0
    copied_maps = 0
    for country_code in COUNTRY_ORDER:
        country_name = COUNTRY_NAMES[country_code]
        parts.extend([f"## {country_name} ({country_code})", ""])
        map_ref = _copy_map(country_code, assets_dir)
        if map_ref:
            copied_maps += 1
            parts.extend([
                f"![{country_name} site status map]({map_ref})" + "{width=9in}",
                "",
            ])
        if country_code in NO_PASS_COUNTRIES:
            summary = no_pass_summaries.get(
                country_code,
                "No exclusionary-pass brownfield site is available in the consolidated v1.2 screen.",
            )
            parts.extend([f"**Portfolio result:** {summary}", ""])
            continue
        selected = [_site_row(country_code, row) for row in selected_rows(country_code, ledger_rows(country_code))]
        rows_for_csv.extend(selected)
        countries_with_rows += 1
        if country_code == "RO":
            parts.append("Romania is shown as a full national ledger, rather than a top-five extract, to support the stakeholder review requested for the domestic portfolio.")
            parts.append("")
        parts.extend([_markdown_table(selected), ""])

    _write_csv(csv_path, rows_for_csv)
    markdown_path.write_text("\n".join(parts).strip() + "\n", encoding="utf-8")
    return {
        "countries_with_rows": countries_with_rows,
        "selected_site_rows": len(rows_for_csv),
        "copied_maps": copied_maps,
        "no_pass_countries": len(NO_PASS_COUNTRIES),
    }
