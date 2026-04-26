# man_hours: 1.5
"""Markdown renderer for the NuScale top-10-per-country report.

Consumes the dict bundles emitted by :mod:`scripts._nuscale_top10_query`
and emits a single markdown file under
``report/output/sensitivity/<stamp>/nuscale_top10.md`` with one section
per country plus a regional intro and a methodology footer.

The renderer is intentionally pure (no DB or filesystem reads) so the
CLI orchestrator can unit-test it against fixture dicts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Sequence

from scripts._nuscale_top10_query import FAMILIES
from scripts._phase_1_6_report_writer import country_display_name, country_slug

NUSCALE_LABEL = "NuScale (VOYGR-6)"


def _fmt_float(v: Any, digits: int = 2, dash: str = "—") -> str:
    if v is None:
        return dash
    try:
        return f"{float(v):.{digits}f}"
    except (TypeError, ValueError):
        return dash


def _fmt_pct(v: Any, digits: int = 0, dash: str = "—") -> str:
    if v is None:
        return dash
    try:
        return f"{float(v) * 100:.{digits}f}%"
    except (TypeError, ValueError):
        return dash


def _band_or_dash(v: Any) -> str:
    return v if v else "—"


def _country_name_lookup(
    rows_by_country: dict[str, list[dict[str, Any]]],
    composites: dict[Any, dict[str, Any]],
) -> dict[str, str]:
    out: dict[str, str] = {}
    for cc in rows_by_country:
        out[cc] = country_display_name(cc)
    return out


def _rank_row(
    rank: int,
    site_row: dict[str, Any],
    composites: dict[Any, dict[str, Any]],
    family_scores: dict[Any, dict[str, float]],
    hit_rates: dict[tuple, dict[str, Any]],
    country_code: str,
) -> str:
    sid = site_row["site_id"]
    site_name = site_row.get("site_name") or str(sid)[:8]
    band = _band_or_dash(site_row.get("band"))
    comp = composites.get(sid, {})
    composite = _fmt_float(site_row.get("composite_score"), 2)
    lo = _fmt_float(site_row.get("composite_score_low"), 2)
    hi = _fmt_float(site_row.get("composite_score_high"), 2)
    fam = family_scores.get(sid, {})
    fam_cells = " | ".join(_fmt_float(fam.get(f), 1) for f in FAMILIES)
    hr = (
        hit_rates.get((sid, country_code))
        or hit_rates.get((sid, None))
        or {}
    )
    p5 = _fmt_pct(hr.get("top5pct"), 0)
    p30 = _fmt_pct(hr.get("top30pct"), 0)
    cov_val = comp.get("coverage") if comp else None
    coverage = (
        f"{float(cov_val):.0f}%" if cov_val is not None else "—"
    )
    return (
        f"| {rank} | {site_name} | {band} | {composite} | {lo} / {hi} "
        f"| {fam_cells} | {p5} | {p30} | {coverage} |"
    )


def _render_country_section(
    *,
    country_code: str,
    country_name: str,
    rows: Sequence[dict[str, Any]],
    summary: dict[str, Any] | None,
    composites: dict[Any, dict[str, Any]],
    family_scores: dict[Any, dict[str, float]],
    hit_rates: dict[tuple, dict[str, Any]],
    figures_subdir: str,
) -> list[str]:
    lines: list[str] = [f"## {country_code} — {country_name}"]
    if summary:
        bands = (
            f"A={summary.get('band_a') or 0} · "
            f"B={summary.get('band_b') or 0} · "
            f"C={summary.get('band_c') or 0}"
        )
        jacc = _fmt_float(summary.get("mean_jaccard"), 2)
        lines.append(
            f"- n_sites={summary.get('n_sites')} · K={summary.get('k_value')} "
            f"· scenarios={summary.get('scenarios_compared')} "
            f"· mean Jaccard@K vs baseline = {jacc} "
            f"· bands {bands}"
        )
    if not rows:
        lines.append("- _No NuScale-scored sites for this country in the run._")
        return lines
    fam_header = " | ".join(FAMILIES)
    lines.extend([
        "",
        "| # | Site | Band | Composite | UI low/high "
        f"| {fam_header} | Top-5% | Top-30% | Coverage |",
        "| --- | --- | :-: | ---: | --- "
        + "| ---: " * len(FAMILIES) + "| ---: | ---: | ---: |",
    ])
    for idx, r in enumerate(rows, start=1):
        lines.append(_rank_row(
            idx, r, composites, family_scores, hit_rates, country_code,
        ))
    lines.extend([
        "",
        f"![{country_code} composite shortlist]({figures_subdir}/"
        f"{country_code}_composite_top10.png)",
        f"![{country_code} family score heatmap]({figures_subdir}/"
        f"{country_code}_family_heatmap.png)",
    ])
    national_md = f"national/{country_slug(country_code)}.md"
    lines.append(f"_Cross-link:_ [`{national_md}`]({national_md})")
    lines.append("")
    return lines


def _render_regional_block(
    *,
    smr_key: str,
    rows_by_country: dict[str, list[dict[str, Any]]],
    composites: dict[Any, dict[str, Any]],
    stability: dict[str, dict[str, Any]],
    summary_global: dict[str, Any] | None,
    n_top: int = 10,
) -> list[str]:
    flat: list[tuple[int, dict[str, Any]]] = []
    for rows in rows_by_country.values():
        for r in rows:
            rr = r.get("regional_rank")
            if rr is None:
                continue
            flat.append((int(rr), r))
    flat.sort(key=lambda t: t[0])
    top_regional = flat[:n_top]

    lines: list[str] = ["## Regional summary"]
    if summary_global:
        bands = (
            f"A={summary_global.get('band_a') or 0} · "
            f"B={summary_global.get('band_b') or 0} · "
            f"C={summary_global.get('band_c') or 0}"
        )
        lines.append(
            f"- Global NuScale shortlist: K={summary_global.get('k_value')} "
            f"· scenarios={summary_global.get('scenarios_compared')} "
            f"· mean Jaccard@K = "
            f"{_fmt_float(summary_global.get('mean_jaccard'), 2)} "
            f"· bands {bands}"
        )
    if stability:
        worst = max(
            stability.values(),
            key=lambda v: (v.get("max_delta") or 0.0),
            default=None,
        )
        if worst is not None:
            lines.append(
                "- Weight-profile stability (worst profile): "
                f"max |Δscore| = {_fmt_float(worst.get('max_delta'), 2)} "
                f"· mean |Δscore| = {_fmt_float(worst.get('mean_delta'), 2)} "
                f"· Jaccard@5 = {_fmt_float(worst.get('jaccard5'), 2)} "
                f"· Jaccard@10 = {_fmt_float(worst.get('jaccard10'), 2)}"
            )
    if top_regional:
        lines.extend([
            "",
            "| Rank | Site | Country | Band | Composite | UI low/high |",
            "| ---: | --- | :-: | :-: | ---: | --- |",
        ])
        for rank, r in top_regional:
            sid = r["site_id"]
            comp = composites.get(sid, {})
            country_code = r.get("country_code") or comp.get("country_code") or "??"
            site_name = r.get("site_name") or comp.get("site_name") or str(sid)[:8]
            lines.append(
                f"| {rank} | {site_name} | {country_code} "
                f"| {_band_or_dash(r.get('band'))} "
                f"| {_fmt_float(r.get('composite_score'), 2)} "
                f"| {_fmt_float(r.get('composite_score_low'), 2)} / "
                f"{_fmt_float(r.get('composite_score_high'), 2)} |"
            )
    lines.extend([
        "",
        "![NuScale band counts](figures/band_counts_ah_nuscale.png)",
        "![NuScale failure funnel]"
        "(figures/failure/per_smr/nuscale_voygr6/failure_funnel.png)",
        "",
    ])
    return lines


def _render_methodology(
    *,
    smr_key: str,
    sensitivity_run_id: str,
    scoring_run_id: str,
) -> list[str]:
    return [
        "## Methodology",
        "- Bands A–H: see `report/methodology/methodology.md` §"
        "Stability bands.",
        "- Sensitivity envelope: ±20 % weights, 10 000 Monte-Carlo draws, "
        "±25 % thresholds.",
        "- DB tables consulted: `country_site_rankings`, "
        "`composite_rankings`, `composite_score_components`, `site_bands`, "
        "`country_rankings_summary`, `weight_profile_stability`.",
        "- Reproduce: `python -m scripts.inspect_run --run-id "
        f"{sensitivity_run_id} top-n-per-country --smr {smr_key} --n 10`",
        f"- Scoring run: `{scoring_run_id}` "
        f"· sensitivity run: `{sensitivity_run_id}`.",
        "",
    ]


def render_report(
    *,
    smr_key: str,
    smr_label: str,
    stamp: str,
    sensitivity_run_id: str,
    scoring_run_id: str,
    git_sha: str | None,
    rows_by_country: dict[str, list[dict[str, Any]]],
    summaries: dict[str, dict[str, Any]],
    composites: dict[Any, dict[str, Any]],
    family_scores: dict[Any, dict[str, float]],
    hit_rates: dict[tuple, dict[str, Any]],
    stability: dict[str, dict[str, Any]],
    figures_subdir: str = "nuscale_top10/figures",
) -> str:
    """Assemble the consolidated markdown."""
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    head = [
        f"# {smr_label} — top 10 sites per country ({stamp})",
        "",
        f"_Generated {now_utc}_  ",
        f"_Sensitivity run_id_: `{sensitivity_run_id}`  ",
        f"_Scoring run_id_: `{scoring_run_id}`  ",
        f"_git_sha_: `{git_sha or 'n/a'}`",
        "",
    ]
    summary_global = summaries.get("_all_") or summaries.get("ALL") or None
    body: list[str] = list(head)
    body.extend(_render_regional_block(
        smr_key=smr_key,
        rows_by_country=rows_by_country,
        composites=composites,
        stability=stability,
        summary_global=summary_global,
    ))
    name_by_cc = _country_name_lookup(rows_by_country, composites)
    for cc in sorted(rows_by_country.keys()):
        body.extend(_render_country_section(
            country_code=cc,
            country_name=name_by_cc.get(cc, cc),
            rows=rows_by_country[cc],
            summary=summaries.get(cc),
            composites=composites,
            family_scores=family_scores,
            hit_rates=hit_rates,
            figures_subdir=figures_subdir,
        ))
    body.extend(_render_methodology(
        smr_key=smr_key,
        sensitivity_run_id=sensitivity_run_id,
        scoring_run_id=scoring_run_id,
    ))
    return "\n".join(body) + "\n"


__all__ = ["render_report"]
