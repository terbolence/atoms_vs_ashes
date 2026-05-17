# man_hours: 1.5
"""Country-pack PDF renderer."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from atoms_vs_ashes.gui.reports.charts import country_chart_images
from atoms_vs_ashes.gui.reports.models import CountryPackReport
from atoms_vs_ashes.gui.reports.pdf_common import (
    fmt,
    h1,
    h2,
    latlon,
    p,
    pct,
    reportlab_parts,
    table,
    value_range,
)


def render_country_pack_pdf(report: CountryPackReport) -> bytes:
    """Render country-by-country top-N expert pack to PDF bytes."""
    rl = reportlab_parts()
    buf = BytesIO()
    doc = rl["doc"](
        buf, pagesize=rl["landscape"](rl["A4"]),
        rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24,
    )
    story = [
        h1(f"Top {report.top_n} Country Metrics"),
        p(f"Run: {report.run_id}"),
        p(f"Baseline run: {report.baseline_run_id}"),
        p(f"Sensitivity run: {report.sensitivity_run_id or 'not selected'}"),
        p(f"Weight profile: {report.weight_profile}"),
        p(f"Scope: {report.scope_summary}"),
        rl["spacer"],
    ]
    for idx, country in enumerate(report.countries):
        if idx:
            story.append(rl["page_break"])
        story += _country_story(country, rl, report.top_n)
    doc.build(story)
    return buf.getvalue()


def _country_story(country, rl: dict, top_n: int) -> list[Any]:
    story = [
        h1(f"{country.country_name} ({country.country_code})"),
        p(f"Top-N setting: {top_n}; rows are site x SMR pairs."),
    ]
    if not country.sites:
        return story + [p("No top-site rows are available for this country.")]
    story.append(_top_sites_table(country.sites))
    story += _chart_story(country, rl)
    story += _stability_story(country)
    story += _sensitivity_story(country)
    story += _national_sensitivity_story(country)
    for site in country.sites:
        story += _site_detail_story(site)
    return story


def _top_sites_table(sites: list[Any]) -> Any:
    rows = [[
        "Rank", "Site", "SMR", "Status", "Composite", "MC band",
        "Lat/Lon", "Plant MW", "Export MW", "Area ha",
    ]]
    for site in sites:
        core = {m.key: m for m in site.metrics.core}
        rows.append([
            site.rank or "",
            site.name,
            site.smr_key,
            site.status,
            fmt(site.composite),
            value_range(site.composite_low, site.composite_high),
            latlon(site.latitude, site.longitude),
            fmt(site.capacity_mw),
            fmt(getattr(core.get("grid_export_capacity_mw"), "value", None)),
            fmt(getattr(core.get("buildable_area_ha"), "value", None)),
        ])
    return table(rows, widths=[32, 120, 65, 65, 55, 70, 75, 50, 55, 50])


def _chart_story(country, rl: dict) -> list[Any]:
    story: list[Any] = []
    for title, png in country_chart_images(country):
        story += [h2(title), rl["image"](BytesIO(png), width=680, height=210)]
    return story


def _stability_story(country) -> list[Any]:
    rows = country.sensitivity.stability_rows
    if not rows:
        return [h2("Country Stability"), p("No country-scoped stability rows available.")]
    table_rows = [["Band", "Site", "SMR", "Top 10% hit", "Scenarios", "MC band"]]
    for row in rows[:20]:
        table_rows.append([
            row.band,
            row.site_name,
            row.smr_key or "",
            pct(row.top10pct_hit_rate),
            f"{row.scenarios_scored}/{row.scenarios_total}",
            value_range(row.mc_low, row.mc_high),
        ])
    return [h2("Country Stability"), table(table_rows, widths=[35, 150, 70, 70, 70, 75])]


def _sensitivity_story(country) -> list[Any]:
    snap = country.sensitivity.sensitivity_snapshot
    if not country.sensitivity.has_sensitivity or snap is None:
        return [h2("Country Sensitivity"), p("Not available for this run.")]
    story: list[Any] = [h2("Country Sensitivity")]
    if snap.country_balance:
        rows = [["Baseline", "Balanced", "Delta", "Floor swap"]]
        rows += [
            [r["baseline_count"], r["balanced_count"], r["delta"], r["triggered_floor_swap"]]
            for r in snap.country_balance
        ]
        story.append(table(rows, widths=[70, 70, 50, 75]))
    if snap.threshold_sweep:
        rows = [["Criterion", "Direction", "Affected", "Score delta", "+", "-"]]
        rows += [
            [
                r["criterion_id"], r["direction"], r["n_pairs_affected"],
                fmt(r["mean_abs_score_delta"]), r["survivors_added"],
                r["survivors_removed"],
            ]
            for r in snap.threshold_sweep[:20]
        ]
        story.append(table(rows, widths=[60, 70, 55, 70, 35, 35]))
    return story


def _national_sensitivity_story(country) -> list[Any]:
    report = country.sensitivity
    snap = report.national_sensitivity_snapshot
    if not report.has_national_sensitivity or snap is None:
        return [h2("National Sensitivity"), p("Not available for this run.")]
    story: list[Any] = [h2("National Sensitivity")]
    if report.national_stability_rows:
        rows = [["Band", "Site", "SMR", "Top 10% hit", "Scenarios", "MC band"]]
        for row in report.national_stability_rows[:20]:
            rows.append([
                row.band, row.site_name, row.smr_key or "",
                pct(row.top10pct_hit_rate),
                f"{row.scenarios_scored}/{row.scenarios_total}",
                value_range(row.mc_low, row.mc_high),
            ])
        story.append(table(rows, widths=[35, 150, 70, 70, 70, 75]))
    if snap.summary_rows:
        rows = [["SMR", "Scenario", "Mean |rank d|", "Top-3 Jaccard", "Small-n"]]
        rows += [
            [
                r["smr_key"], r["weight_profile"], fmt(r["mean_abs_rank_delta"]),
                fmt(r["top3_jaccard"]), r["small_n"],
            ]
            for r in snap.summary_rows[:20]
        ]
        story.append(table(rows, widths=[70, 100, 80, 80, 45]))
    if snap.mc_rank_rows:
        rows = [["SMR", "Site", "P(rank=1)", "P(rank<=3)", "Median rank"]]
        rows += [
            [
                r["smr_key"], r["site"], fmt(r["p_rank_1"]),
                fmt(r["p_rank_le_3"]), fmt(r["median_rank"]),
            ]
            for r in snap.mc_rank_rows[:20]
        ]
        story.append(table(rows, widths=[70, 170, 70, 75, 70]))
    return story


def _site_detail_story(site) -> list[Any]:
    story = [h2(f"{site.name} / {site.smr_key}")]
    detail = site.detail
    if detail and detail.strengths:
        rows = [["Strength", "Score", "Justification"]]
        rows += [[s.criterion_id, fmt(s.score_0_10), s.justification] for s in detail.strengths[:8]]
        story.append(table(rows, widths=[70, 45, 420]))
    if detail and detail.all_criterion_scores:
        rows = [["Criterion", "Family", "Score"]]
        rows += [[r.criterion_id, r.family, fmt(r.score_0_10)] for r in detail.all_criterion_scores]
        story.append(table(rows, widths=[70, 55, 50]))
    raw = [["Criterion", "Metric", "Value", "Units"]]
    raw += [
        [m.criterion_id or "", m.label, fmt(m.value), m.units or ""]
        for m in site.metrics.criteria
    ]
    story.append(table(raw, widths=[65, 190, 80, 50]))
    return story


__all__ = ["render_country_pack_pdf"]
