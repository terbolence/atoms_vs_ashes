# man_hours: 1.1
"""Output coordinator for reusable country/site profile artefacts."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from scripts._country_pareto_charts import (
    write_avoidance_pareto_png,
    write_failure_pareto_png,
)
from scripts._country_profile_map import STATUS_LABEL, write_maps
from scripts._country_profile_markdown import (
    COUNTRY_MAP_ANCHOR,
    render_country_markdown_from_bundle,
)
from scripts._site_profile_charts import write_site_charts
from scripts._site_profile_markdown import (
    render_site_markdown_from_bundle,
    set_criteria_lookup,
)


def write_artifacts(
    *,
    out: Path,
    country_bundle: dict[str, Any],
    site_bundle: dict[str, Any] | None,
    detail: dict[str, Any],
    selected_row: dict[str, Any] | None,
    country_name: str,
    country_code: str,
    smr_label: str,
    site_slug: str | None,
    site_only: bool = False,
) -> None:
    """Write data, figures, and markdown for one country/site profile.

    The site bundle, site charts, and site profile are written only
    when ``site_bundle``, ``selected_row``, and ``site_slug`` are all
    present. When ``site_only`` is true the country artefacts
    (bundle JSON, ledger CSV, status maps, Pareto charts, country
    markdown) are skipped (useful when patching one site without
    touching the country profile, which preserves a filled
    ``country_exec`` placeholder). When called in country-only mode the
    country artefacts are written without touching anything under
    ``sites/``.
    """
    write_site = (
        site_bundle is not None
        and selected_row is not None
        and site_slug
    )
    write_country = not site_only
    (out / "data").mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(parents=True, exist_ok=True)
    if write_site:
        (out / "sites").mkdir(parents=True, exist_ok=True)
    country_prefix = country_code

    set_criteria_lookup(country_bundle.get("criteria_lookup", {}))

    country_md_name = f"{country_prefix}_country_prototype.md"
    if write_country:
        country_bundle_filename = f"{country_prefix}_country_bundle.json"
        _write_json(out / "data" / country_bundle_filename, country_bundle)
        _write_csv(
            out / "data" / f"{country_prefix}_site_ledger.csv",
            country_bundle.get("sites", []),
        )

        bundle_rows = [
            _ledger_row(row) for row in country_bundle.get("sites", [])
        ]
        maps = write_maps(
            out / "figures", bundle_rows, country_name=country_name,
            country_code=country_code, smr_label=smr_label,
        )
        pareto_charts = _write_pareto_charts(
            out / "figures", country_bundle,
            country_prefix=country_prefix,
            country_name=country_name.split(" (", 1)[0],
        )
        (out / country_md_name).write_text(
            render_country_markdown_from_bundle(
                country_bundle, country_name=country_name,
                smr_label=smr_label, maps=maps,
                pareto_charts=pareto_charts,
                country_bundle_filename=country_bundle_filename,
            ),
            encoding="utf-8",
        )

    if write_site:
        site_prefix = f"{country_code}_{site_slug}"
        site_bundle_filename = f"{site_prefix}_site_bundle.json"
        _write_json(out / "data" / site_bundle_filename, site_bundle)
        charts = write_site_charts(
            out / "figures", detail, file_prefix=site_prefix,
            site_name=selected_row["name"],
        )
        composite_summary = {"national_rank": selected_row.get("national_rank")}
        country_profile_link = {
            "label": f"{country_name.split(' (', 1)[0]} Country Profile",
            "href": f"../{country_md_name}#{COUNTRY_MAP_ANCHOR}",
        }
        site_md_path = out / "sites" / f"{site_prefix}.md"
        new_md = render_site_markdown_from_bundle(
            site_bundle,
            country_name=country_name, smr_label=smr_label,
            chart_paths=charts,
            composite_summary=composite_summary,
            country_profile_link=country_profile_link,
            site_bundle_filename=site_bundle_filename,
        )
        if site_md_path.exists():
            new_md = _preserve_filled_placeholders(
                old_text=site_md_path.read_text(encoding="utf-8"),
                new_text=new_md,
            )
        site_md_path.write_text(new_md, encoding="utf-8")

    _write_index(out)


_PLACEHOLDER_BLOCK_RE = re.compile(
    r"<!-- specialist key=(?P<key>\S+)[^>]*?-->\n.*?\n<!-- /specialist key=(?P=key) -->",
    re.DOTALL,
)


def _preserve_filled_placeholders(*, old_text: str, new_text: str) -> str:
    """Carry forward any ``status=filled`` specialist blocks from the
    previous render of the same site profile.

    Re-rendering site markdown is needed when the auto-generated
    criterion bullets, snapshot labels, or static template change.
    Without preservation, the agent would lose every paragraph
    already drafted by the siting expert.
    """
    filled: dict[str, str] = {}
    for match in _PLACEHOLDER_BLOCK_RE.finditer(old_text):
        block = match.group(0)
        if "status=filled" in block.split("\n", 1)[0]:
            filled[match.group("key")] = block
    if not filled:
        return new_text

    def swap(m: re.Match[str]) -> str:
        key = m.group("key")
        return filled.get(key, m.group(0))

    return _PLACEHOLDER_BLOCK_RE.sub(swap, new_text)


def _write_pareto_charts(
    figures: Path,
    country_bundle: dict[str, Any],
    *,
    country_prefix: str,
    country_name: str,
) -> dict[str, str]:
    out: dict[str, str] = {}
    avoidance_path = figures / f"{country_prefix}_avoidance_pareto.png"
    if write_avoidance_pareto_png(
        country_bundle, avoidance_path, country_name=country_name,
    ):
        out["avoidance"] = avoidance_path.name
    failure_path = figures / f"{country_prefix}_exclusionary_pareto.png"
    if write_failure_pareto_png(
        country_bundle, failure_path, country_name=country_name,
    ):
        out["failure"] = failure_path.name
    return out


def _ledger_row(row: dict[str, Any]) -> dict[str, Any]:
    """Translate a country-bundle site row to the row shape the map writer
    expects (legacy keys composite/status_label/etc.)."""
    status = (
        "pass" if row.get("passed_exclusionary") and row.get("passed_avoidance")
        else "hard-fail" if not row.get("passed_exclusionary")
        else "avoidance-flag"
    )
    return {
        "national_rank": row.get("national_rank"),
        "site_id": row.get("site_id"),
        "name": row.get("name"),
        "status": status,
        "status_label": STATUS_LABEL.get(status, status),
        "latitude": row.get("latitude"),
        "longitude": row.get("longitude"),
        "composite": row.get("composite_score"),
        "composite_low": row.get("composite_score_low"),
        "composite_high": row.get("composite_score_high"),
        "national_band": row.get("national_band"),
        "national_top10_rate": row.get("national_top10pct_hit_rate"),
        "criteria_coverage": row.get("criteria_coverage"),
    }


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    cols = [
        "national_rank", "name", "passed_exclusionary",
        "passed_avoidance", "composite_score", "composite_score_low",
        "composite_score_high", "national_band",
        "national_top10pct_hit_rate", "criteria_coverage",
        "avg_confidence", "installed_capacity_mw",
        "latitude", "longitude",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col) for col in cols})


_COUNTRY_DISPLAY = {
    "AL": "Albania", "AT": "Austria", "BA": "Bosnia and Herzegovina",
    "BG": "Bulgaria", "BY": "Belarus", "CZ": "Czechia", "HR": "Croatia",
    "HU": "Hungary", "LV": "Latvia", "MD": "Moldova", "ME": "Montenegro",
    "MK": "North Macedonia", "PL": "Poland", "RO": "Romania",
    "RS": "Serbia", "SI": "Slovenia", "SK": "Slovakia", "TR": "Türkiye",
    "UA": "Ukraine", "XK": "Kosovo",
}


def _write_index(out: Path) -> None:
    country_links = sorted(out.glob("*_country_prototype.md"))
    site_links = sorted((out / "sites").glob("*.md")) if (out / "sites").exists() else []
    lines = [
        "# Chapter 5 - Country and Site Profiles",
        "",
        "## Country profiles",
        "",
    ]
    for path in country_links:
        cc = path.name.split("_", 1)[0]
        display = _COUNTRY_DISPLAY.get(cc, cc)
        lines.append(f"- [{display} ({cc})]({path.name})")
    failure_section = out / "consolidated_failure_section.md"
    if failure_section.exists():
        lines += [
            "",
            "## Consolidated failure section",
            "",
            "- [Countries with no exclusionary-pass site]"
            f"({failure_section.name})",
        ]
    if site_links:
        lines += ["", "## Site profiles", ""]
        for path in site_links:
            stem = path.stem
            lines.append(f"- [{stem}](sites/{path.name})")
    top5 = out / "recommended_top5_sites.md"
    if top5.exists():
        lines += [
            "", "## Top-5 site recommendations", "",
            f"- [Region-wide ranked top-5]({top5.name})",
        ]
    caveat = out / "02_ukraine_occupied_territory_caveat_plan.md"
    if caveat.exists():
        lines += [
            "", "## Caveats", "",
            "- [Ukraine occupied-territory caveat plan]"
            "(02_ukraine_occupied_territory_caveat_plan.md)",
        ]
    (out / "00_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


__all__ = ["STATUS_LABEL", "write_artifacts"]
