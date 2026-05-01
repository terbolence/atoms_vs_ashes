# man_hours: 1.5
"""Markdown renderer for :mod:`scripts.build_shortlist_handpick_report`."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any


def md_cell(value: object | None) -> str:
    """Single table cell: flatten newlines and escape ``|`` for GFM tables."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (list, tuple)):
        return ", ".join(md_cell(x) for x in value)
    s = str(value).replace("\r\n", "\n").replace("\r", "\n")
    s = " ".join(line.strip() for line in s.split("\n") if line.strip())
    return s.replace("|", "\\|")


def _fmt_float(x: float | Decimal | None) -> str:
    if x is None:
        return ""
    v = float(x)
    return f"{v:.4f}".rstrip("0").rstrip(".")


def render_shortlist_handpick_md(
    *,
    stamp: str,
    scoring_run_id: str,
    sensitivity_run_id: str,
    smr_key: str,
    weight_profile: str,
    db_profile: str,
    git_sha: str | None,
    top_n: int,
    shortlist_by_country: dict[str, list[dict[str, Any]]],
    full_pass_rows: list[dict[str, Any]],
    avoidance_pairs: list[dict[str, Any]],
    verdicts_by_pair: dict[tuple[uuid.UUID, str], list[dict[str, Any]]],
) -> str:
    lines: list[str] = [
        "# Shortlist (hand-pick) + avoidance annex",
        "",
        "## Provenance",
        "",
        f"- **Stamp**: `{stamp}`",
        f"- **Scoring run**: `{scoring_run_id}`",
        f"- **Sensitivity run**: `{sensitivity_run_id}`",
        f"- **SMR**: `{smr_key}`",
        f"- **Weight profile**: `{weight_profile}`",
        f"- **DB profile**: `{db_profile}`",
        f"- **Git SHA**: `{git_sha or 'unknown'}`",
        "",
        "National ranks and stability bands come from `country_site_rankings` "
        f"(sensitivity). Composite pass flags and scores below labelled "
        "`composite_ranking_*` come from `composite_rankings` for the scoring run.",
        "",
        "---",
        "",
        "## Executive shortlist (top N per country)",
        "",
        f"Up to **{top_n}** sites per country by national rank (normal qualification: "
        "avoidance-flagged sites may appear).",
        "",
    ]
    for cc in sorted(shortlist_by_country):
        rows = shortlist_by_country[cc]
        lines.append(f"### {cc}")
        lines.append("")
        lines.append(
            "| Rank | Band | Site | site_id | CSR composite | CR composite | "
            "rank_pos | passed_excl | passed_avoid | acceptability |"
        )
        lines.append("| ---: | :--- | :--- | :--- | :--- | :--- | ---: | :--- | :--- | :--- |")
        for r in rows:
            lines.append(
                "| "
                + " | ".join(
                    [
                        md_cell(r.get("national_rank")),
                        md_cell(r.get("band")),
                        md_cell(r.get("site_name")),
                        md_cell(r.get("site_id")),
                        md_cell(r.get("composite_score")),
                        md_cell(_fmt_float(r.get("composite_ranking_score"))),
                        md_cell(r.get("rank_position")),
                        md_cell(r.get("passed_exclusionary")),
                        md_cell(r.get("passed_avoidance")),
                        md_cell(r.get("acceptability_flag")),
                    ]
                )
                + " |"
            )
        lines.append("")
    lines.extend(
        [
            "---",
            "",
            "## Annex A — Full pass (exclusionary + avoidance)",
            "",
            "All sites with `passed_exclusionary` and `passed_avoidance` for this run.",
            "",
            "| Country | Site | site_id | composite | rank_pos |",
            "| :--- | :--- | :--- | :--- | ---: |",
        ]
    )
    for r in full_pass_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_cell(r.get("country_code")),
                    md_cell(r.get("site_name")),
                    md_cell(r.get("site_id")),
                    md_cell(_fmt_float(r.get("composite_score"))),
                    md_cell(r.get("rank_position")),
                ]
            )
            + " |"
        )
    lines.append("")
    lines.extend(
        [
            "---",
            "",
            "## Annex B — Avoidance-flagged (still exclusionary-clear)",
            "",
            "Sites with `passed_exclusionary` true and `passed_avoidance` false.",
            "",
            "| Country | Site | site_id | composite | rank_pos |",
            "| :--- | :--- | :--- | :--- | ---: |",
        ]
    )
    for r in avoidance_pairs:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_cell(r.get("country_code")),
                    md_cell(r.get("site_name")),
                    md_cell(r.get("site_id")),
                    md_cell(_fmt_float(r.get("composite_score"))),
                    md_cell(r.get("rank_position")),
                ]
            )
            + " |"
        )
    lines.extend(["", "---", "", "## Annex C — Avoidance verdict detail", ""])
    if not avoidance_pairs:
        lines.append("_No avoidance-flagged sites for this run._")
        lines.append("")
        return "\n".join(lines)

    for r in avoidance_pairs:
        sid = r["site_id"]
        sk = str(r["smr_key"])
        key = (sid, sk)
        vrows = verdicts_by_pair.get(key, [])
        title = f"{r.get('country_code')} — {r.get('site_name')} (`{sk}`)"
        lines.append(f"### {md_cell(title)}")
        lines.append("")
        lines.append(f"- **site_id**: `{sid}`")
        lines.append("")
        if not vrows:
            lines.append("_No avoidance-phase caution/fail rows found for this pair "
                         "(data mismatch — check `screening_verdicts.run_id`)._")
            lines.append("")
            continue
        lines.append(
            "| criterion_id | verdict | measured | threshold | "
            "meas_num | thresh_num | units | confidence | prompt_key | "
            "data_sources | justification |"
        )
        lines.append(
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
        )
        for v in vrows:
            ds = v.get("data_sources")
            ds_s = ", ".join(ds) if isinstance(ds, list) else md_cell(ds)
            lines.append(
                "| "
                + " | ".join(
                    [
                        md_cell(v.get("criterion_id")),
                        md_cell(v.get("verdict")),
                        md_cell(v.get("measured_value")),
                        md_cell(v.get("threshold")),
                        md_cell(v.get("measured_value_numeric")),
                        md_cell(v.get("threshold_numeric")),
                        md_cell(v.get("measured_units")),
                        md_cell(v.get("confidence")),
                        md_cell(v.get("prompt_key")),
                        md_cell(ds_s),
                        md_cell(v.get("justification")),
                    ]
                )
                + " |"
            )
        lines.append("")
    return "\n".join(lines)


__all__ = ["md_cell", "render_shortlist_handpick_md"]
