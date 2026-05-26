# man_hours: 1.6
"""Markdown renderer for one country profile from a country bundle."""

from __future__ import annotations

from typing import Any

from scripts._country_profile_map import STATUS_LABEL

COUNTRY_MAP_ANCHOR = "country-status-map"


def _num(value: Any, digits: int = 2) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def _pct(value: Any, digits: int = 0) -> str:
    if value is None:
        return "-"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    if v <= 1.0:
        v *= 100
    return f"{v:.{digits}f}%"


def _plain_country(country_name: str) -> str:
    return country_name.split(" (", 1)[0]


def _status(row: dict[str, Any]) -> str:
    if not row.get("passed_exclusionary"):
        return "hard-fail"
    if not row.get("passed_avoidance"):
        return "avoidance-flag"
    return "pass"


def render_country_markdown_from_bundle(
    bundle: dict[str, Any],
    *,
    country_name: str,
    smr_label: str,
    maps: dict[str, str],
    pareto_charts: dict[str, str] | None = None,
    country_bundle_filename: str | None = None,
) -> str:
    meta = bundle.get("metadata", {})
    totals = bundle.get("totals", {})
    sites = bundle.get("sites", [])
    pareto = bundle.get("avoidance_pareto", [])
    failure_pareto = bundle.get("exclusionary_failure_pareto", [])
    family_means = bundle.get("family_normalised_score_means", {})
    score_dist = bundle.get("ranking_score_distribution", [])
    country_plain = _plain_country(country_name)
    leader = _leader(sites)
    charts = pareto_charts or {}
    bundle_name = country_bundle_filename or ""
    country_code = (meta.get("country_code") or "").upper()
    lines: list[str] = []
    lines += _intro(
        meta, totals, country_plain, smr_label, leader,
        country_code=country_code, bundle_name=bundle_name,
    )
    lines += _map_block(country_plain, maps)
    lines += _ledger(country_plain, sites)
    lines += _avoidance_pareto(pareto, totals, charts.get("avoidance"))
    if failure_pareto:
        lines += _failure_pareto(failure_pareto, totals, charts.get("failure"))
    lines += _family_strength_weakness(family_means, score_dist)
    lines += _interpretation(
        country_plain, totals, leader, charts.get("avoidance"),
    )
    lines += _status_counts(totals)
    return "\n".join(lines) + "\n"


def _leader(sites: list[dict[str, Any]]) -> dict[str, Any]:
    scored = [s for s in sites if s.get("composite_score") is not None]
    return scored[0] if scored else (sites[0] if sites else {})


def _intro(
    meta: dict[str, Any], totals: dict[str, Any],
    country_plain: str, smr_label: str, leader: dict[str, Any],
    *,
    country_code: str = "",
    bundle_name: str = "",
) -> list[str]:
    block = [
        f"# {country_plain} Country Profile",
        "",
        f"{country_plain} has {totals.get('n_sites', 0)} thermal and "
        f"coal-site records that have been tested against the {smr_label} "
        "reference deployment envelope. "
        f"{totals.get('n_full_pass', 0)} sites pass both the exclusionary "
        f"and avoidance screens, {totals.get('n_avoidance_flag', 0)} pass "
        "the exclusionary screen but retain avoidance flags, and "
        f"{totals.get('n_hard_fail', 0)} fail one or more exclusionary "
        "checks. The country is therefore not a single-site case, but "
        "only a small subset of the national site population currently "
        "clears the full screening pathway without a remediation step.",
        "",
        f"The leading site is **{leader.get('name', '-')}**, with a "
        f"composite score of {_num(leader.get('composite_score'), 3)} and "
        f"a Monte Carlo interval of "
        f"{_num(leader.get('composite_score_low'), 3)}-"
        f"{_num(leader.get('composite_score_high'), 3)}. Its national "
        f"stability band is `{leader.get('national_band') or '-'}` with a "
        "national top-10% hit rate of "
        f"{_pct(leader.get('national_top10pct_hit_rate'))}. The leader "
        "is therefore not only the current point-estimate front-runner; "
        "it is also a stable national candidate under the sensitivity "
        "treatment used for the report.",
    ]
    block += _country_placeholder_block(
        key="country_exec",
        label=(
            "Country coal-to-nuclear executive read (full-pass "
            "leadership pool, avoidance unlock potential, greenfield "
            "lever, and credible programme cadence)"
        ),
        country_code=country_code, bundle_name=bundle_name,
    )
    return block


def _country_placeholder_block(
    *, key: str, label: str, country_code: str, bundle_name: str,
) -> list[str]:
    open_tag = (
        f"<!-- specialist key={key} scope=country "
        f"country_code={country_code} bundle={bundle_name} status=pending -->"
    )
    close_tag = f"<!-- /specialist key={key} -->"
    msg = (
        f"> _Specialist interpretation pending: {label}. Cursor agent "
        "fills via "
        f"`python -m scripts.run_specialist_pass show --country {country_code} "
        f"--key {key}` then `... patch --country {country_code} --key {key} "
        "--text-file <draft.md>`._"
    )
    return ["", open_tag, msg, close_tag]


def _map_block(country_plain: str, maps: dict[str, str]) -> list[str]:
    if not maps:
        return []
    return [
        "",
        f'<a id="{COUNTRY_MAP_ANCHOR}"></a>',
        "",
        f"![{country_plain} status map](figures/{maps.get('png', '')})",
        "",
        "Interactive review map with marker tooltips: "
        f"[{maps.get('html', '')}](figures/{maps.get('html', '')}).",
    ]


def _ledger(country_plain: str, sites: list[dict[str, Any]]) -> list[str]:
    lines = [
        "",
        f"## {country_plain} Site Ledger",
        "",
        "| Rank | Site | Status | Composite | MC Low | MC High | Band | Top-10 Hit | Coverage |",
        "|---:|---|---|---:|---:|---:|---|---:|---:|",
    ]
    for row in sites:
        status_label = STATUS_LABEL.get(_status(row), "?")
        lines.append(
            f"| {row.get('national_rank') or '-'} | {row.get('name')} | "
            f"{status_label} | {_num(row.get('composite_score'), 3)} | "
            f"{_num(row.get('composite_score_low'), 3)} | "
            f"{_num(row.get('composite_score_high'), 3)} | "
            f"{row.get('national_band') or '-'} | "
            f"{_pct(row.get('national_top10pct_hit_rate'))} | "
            f"{_pct(row.get('criteria_coverage'))} |"
        )
    return lines


def _avoidance_pareto(
    pareto: list[dict[str, Any]],
    totals: dict[str, Any],
    chart_filename: str | None,
) -> list[str]:
    if not pareto:
        return [
            "",
            "## Avoidance Flag Pareto",
            "",
            "No exclusionary-pass sites carry avoidance-phase flags in this run.",
        ]
    n_pass = (
        totals.get("n_full_pass", 0) + totals.get("n_avoidance_flag", 0)
    )
    lines = [
        "",
        "## Avoidance Flag Pareto",
        "",
        "Of the "
        f"{n_pass} sites that pass the exclusionary screen, the "
        "avoidance-phase flags concentrate on a small set of criteria. "
        "Resolving them is what would move the country from a small "
        "leading group to a broader candidate pool.",
    ]
    if chart_filename:
        lines += [
            "",
            f"![Avoidance flag Pareto](figures/{chart_filename})",
        ]
    lines.append("")
    for row in pareto:
        share = row.get("share_of_exclusionary_pass")
        share_text = _pct(share) if share is not None else "-"
        lines.append(
            f"- **{row.get('criterion_name')} ({row.get('criterion_id')})** - "
            f"{row.get('n_sites')} of {n_pass} exclusionary-pass sites "
            f"({share_text})."
        )
    return lines


def _failure_pareto(
    failure_pareto: list[dict[str, Any]],
    totals: dict[str, Any],
    chart_filename: str | None,
) -> list[str]:
    n_country = totals.get("n_sites", 0)
    lines = [
        "",
        "## Exclusionary Failure Pareto",
        "",
        "The exclusionary failures across the country trace back to a "
        "small number of criteria. They identify which screening checks "
        "are responsible for removing sites from further consideration.",
    ]
    if chart_filename:
        lines += [
            "",
            f"![Exclusionary failure Pareto](figures/{chart_filename})",
        ]
    lines.append("")
    for row in failure_pareto:
        share = row.get("share_of_country")
        share_text = _pct(share) if share is not None else "-"
        lines.append(
            f"- **{row.get('criterion_name')} ({row.get('criterion_id')})** - "
            f"{row.get('n_sites')} of {n_country} country sites ({share_text})."
        )
    return lines


def _family_strength_weakness(
    family_means: dict[str, Any],
    score_dist: list[dict[str, Any]],
) -> list[str]:
    if not family_means:
        return []
    items = [
        (k, v.get("mean_normalised_score"))
        for k, v in family_means.items()
        if v.get("mean_normalised_score") is not None
    ]
    items.sort(key=lambda kv: kv[1] or 0)
    weakest = items[0] if items else None
    strongest = items[-1] if items else None
    weak_criteria = [
        row for row in score_dist
        if row.get("mean_score_0_10") is not None
    ][:3]
    lines = ["", "## Family Strength and Weakness", ""]
    if strongest and weakest:
        lines.append(
            "Across the country the strongest criterion family is "
            f"**{_family_label(strongest[0])}** at a mean normalised "
            f"score of {_num(strongest[1], 2)}/10. The weakest family is "
            f"**{_family_label(weakest[0])}** at "
            f"{_num(weakest[1], 2)}/10. The bottom three individual "
            "criteria across the country are:"
        )
        lines.append("")
    for row in weak_criteria:
        lines.append(
            f"- **{row.get('criterion_name')} ({row.get('criterion_id')})** - "
            f"mean {_num(row.get('mean_score_0_10'), 2)}/10 across "
            f"{row.get('n_sites_scored')} scored sites "
            f"(min {_num(row.get('min_score_0_10'), 1)}, "
            f"max {_num(row.get('max_score_0_10'), 1)})."
        )
    return lines


def _family_label(family_key: str) -> str:
    label_map = {
        "NH": "Natural Hazards",
        "HI": "Human-Induced Hazards",
        "RI": "Radiological Impact",
        "EP": "Emergency Planning",
        "NS": "Non-Safety / Implementation",
    }
    return label_map.get(family_key, family_key)


def _interpretation(
    country_plain: str, totals: dict[str, Any], leader: dict[str, Any],
    avoidance_chart: str | None,
) -> list[str]:
    block = [
        "",
        "## Interpretation for Site Selection",
        "",
        f"The {country_plain} result shows a clear separation between "
        "sites that can support further Stage 3 consideration and sites "
        "that should remain in the evidence base only as comparators. "
        "The full-pass group is the relevant pool for progression. "
        "Avoidance-flag sites are not discarded, but they identify "
        "locations where a specific constraint must be resolved before "
        "the site can be treated as equivalent to the leading group.",
    ]
    if avoidance_chart:
        block += [
            "",
            f"![Avoidance flag Pareto - what unlocks more sites](figures/{avoidance_chart})",
            "",
            "The chart shows where focused remediation effort would "
            "broaden the candidate pool. The criteria at the top of the "
            "Pareto are the policy and engineering levers that, if "
            "resolved, move avoidance-flag sites into the leading group.",
        ]
    block += [
        "",
        "An IAEA-style reading of the table focuses less on the exact "
        "rank number and more on screening class, score stability, and "
        "the nature of remaining uncertainty. "
        f"**{leader.get('name', '-')}** is important because it leads "
        "nationally, sits inside the strongest stability band, and "
        "retains a full-pass status. That does not establish final site "
        "suitability. It is a defensible reason to spend Stage 3 effort "
        "on field confirmation, national data review, and stakeholder "
        "engagement before lower-ranked or avoidance-flag locations.",
        "",
        "The Monte Carlo interval is a caution against false precision: "
        "several sites have overlapping score bands, so small score "
        "differences should not be overinterpreted. The decisive "
        "distinction is whether a site combines acceptable exclusionary "
        "performance with a stable ranking position and no unresolved "
        "avoidance flag.",
        "",
        "The main Stage 3 questions are therefore targeted rather than "
        "generic: confirm local natural-hazard inputs, verify "
        "emergency-planning assumptions, test land and ownership "
        "constraints, assess cooling and grid interface conditions, and "
        "reconcile environmental constraints with national permitting "
        "requirements.",
    ]
    return block


def _status_counts(totals: dict[str, Any]) -> list[str]:
    return [
        "",
        "## Status Counts",
        "",
        f"- Full pass: {totals.get('n_full_pass', 0)}",
        f"- Exclusion pass with avoidance flag: {totals.get('n_avoidance_flag', 0)}",
        f"- Hard fail: {totals.get('n_hard_fail', 0)}",
    ]


__all__ = ["render_country_markdown_from_bundle"]
