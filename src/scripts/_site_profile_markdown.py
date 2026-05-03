# man_hours: 2.1
"""Markdown renderer for one selected-site profile from a site bundle."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from scripts._country_profile_map import STATUS_LABEL
from scripts._site_profile_intelligence import (
    CRITERION_FIELDS,
    evidence_for,
    quality_for,
)


FAMILY_HEADINGS = [
    ("natural_hazards", "Natural Hazards (NH)"),
    ("human_hazards", "Human-Induced and Security-Relevant Hazards (HI)"),
    ("radiological", "Radiological Impact and Emergency Planning (RI / EP)"),
    ("emergency_planning", None),
    ("infrastructure", "Non-Safety and Implementation Considerations (NS)"),
]

FAMILY_ALIAS = {
    "NH": "natural_hazards", "HI": "human_hazards", "RI": "radiological",
    "EP": "emergency_planning", "NS": "infrastructure", "BF": "infrastructure",
}


def render_site_markdown_from_bundle(
    bundle: dict[str, Any],
    *,
    country_name: str,
    smr_label: str,
    chart_paths: dict[str, str],
    composite_summary: dict[str, Any] | None = None,
    country_profile_link: dict[str, str] | None = None,
    site_bundle_filename: str | None = None,
) -> str:
    site = bundle.get("site") or {}
    families = bundle.get("criterion_families") or {}
    verdicts = (bundle.get("screening") or {}).get("verdicts") or []
    rankings = (bundle.get("scoring") or {}).get("ranking_scores") or []
    composites = (bundle.get("scoring") or {}).get("composite_rankings") or []
    components = (bundle.get("scoring") or {}).get("criterion_components") or []
    bands = (bundle.get("sensitivity") or {}).get("bands") or []
    ownership = bundle.get("ownership") or []
    units = bundle.get("units") or []
    composite = _baseline_composite(composites)
    site_id = str(site.get("site_id") or "")
    bundle_name = site_bundle_filename or ""

    if _is_hard_fail(composite, verdicts):
        return _render_hard_fail(
            site=site, verdicts=verdicts, ownership=ownership, units=units,
            country_name=country_name, smr_label=smr_label,
            country_profile_link=country_profile_link,
            site_id=site_id, bundle_name=bundle_name,
        )

    crit_meta = _criteria_meta(rankings, verdicts)
    by_family = _verdicts_and_scores_by_family(
        rankings, verdicts, components, crit_meta,
    )
    lines: list[str] = []
    lines += _header(site, smr_label, country_name)
    lines += _snapshot(
        site, composite, _band_for(bands, site.get("country_code")),
        composite_summary, country_profile_link,
    )
    lines += _ownership_section(ownership, units)
    lines += _family_section(
        "## Natural Hazards (NH)", "natural_hazards", families, by_family,
        site_id=site_id, bundle_name=bundle_name,
        family_key="family_natural_hazards",
        family_label="Natural Hazards (NH)",
    )
    lines += _family_section(
        "## Human-Induced and Security-Relevant Hazards (HI)",
        "human_hazards", families, by_family,
        site_id=site_id, bundle_name=bundle_name,
        family_key="family_human_hazards",
        family_label="Human-Induced and Security-Relevant Hazards (HI)",
    )
    lines += _family_section(
        "## Radiological Impact and Emergency Planning (RI / EP)",
        ["radiological", "emergency_planning"], families, by_family,
        site_id=site_id, bundle_name=bundle_name,
        family_key="family_radiological_emergency",
        family_label="Radiological Impact and Emergency Planning (RI / EP)",
    )
    lines += _family_section(
        "## Non-Safety and Implementation Considerations (NS)",
        "infrastructure", families, by_family,
        site_id=site_id, bundle_name=bundle_name,
        family_key="family_infrastructure",
        family_label="Non-Safety and Implementation Considerations (NS)",
    )
    lines += _composite_block(
        composite, bands, site, chart_paths,
        site_id=site_id, bundle_name=bundle_name,
    )
    lines += _residual_register(
        by_family, verdicts, families,
        site_id=site_id, bundle_name=bundle_name,
    )
    lines += _stage3_checklist(rankings, verdicts, families, crit_meta)
    lines += _limitations(by_family, families)
    return "\n".join(lines) + "\n"


def _criteria_meta(
    rankings: list[dict[str, Any]],
    verdicts: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rankings + verdicts:
        cid = row.get("criterion_id")
        if cid and cid not in out:
            out[cid] = {
                "criterion_id": cid,
                "family": FAMILY_ALIAS.get(cid.split("-")[0], "infrastructure"),
            }
    return out


def _verdicts_and_scores_by_family(
    rankings: list[dict[str, Any]],
    verdicts: list[dict[str, Any]],
    components: list[dict[str, Any]],
    crit_meta: dict[str, dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    score_by_cid = {row["criterion_id"]: row for row in rankings}
    component_by_cid = {row["criterion_id"]: row for row in components}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen: set[str] = set()
    for cid, meta in crit_meta.items():
        score = score_by_cid.get(cid) or {}
        comp = component_by_cid.get(cid) or {}
        family_key = (
            CRITERION_FIELDS.get(cid, {}).get("family_key")
            or meta["family"]
        )
        grouped[family_key].append(
            {
                "criterion_id": cid,
                "score_0_10": score.get("score_0_10"),
                "score_low_0_10": score.get("score_low_0_10"),
                "score_high_0_10": score.get("score_high_0_10"),
                "weight_normalised": comp.get("weight_normalised") or score.get("weight_normalised"),
                "weighted_contribution": comp.get("weighted_contribution"),
                "category": comp.get("category"),
            }
        )
        seen.add(cid)
    for verdict in verdicts:
        cid = verdict.get("criterion_id")
        if cid not in seen:
            family_key = (
                CRITERION_FIELDS.get(cid, {}).get("family_key")
                or crit_meta.get(cid, {}).get("family", "infrastructure")
            )
            grouped[family_key].append({"criterion_id": cid})
    for items in grouped.values():
        items.sort(key=lambda i: i["criterion_id"])
    return grouped


def _baseline_composite(composites: list[dict[str, Any]]) -> dict[str, Any]:
    for row in composites:
        if (row.get("weight_profile") or "").lower() == "baseline":
            return row
    return composites[0] if composites else {}


def _band_for(bands: list[dict[str, Any]], country_code: str | None) -> dict[str, Any]:
    for row in bands:
        if str(row.get("scope_country_code") or "").upper() == (country_code or "").upper():
            return row
    return next(
        (row for row in bands if str(row.get("scope_country_code") or "") == "XX"),
        {},
    )


def _header(site: dict[str, Any], smr_label: str, country_name: str) -> list[str]:
    name = site.get("name") or "Site"
    cname = country_name.split(" (", 1)[0]
    return [
        f"# {name} Site Profile",
        "",
        f"{name} is a coal/thermal site in {cname} that has been "
        f"tested against the {smr_label} reference deployment envelope. "
        "This profile reads the screening evidence at a level that "
        "supports a decision to progress toward Stage 3 "
        "characterization. It is not a site-suitability determination, "
        "vendor recommendation, or licensing finding.",
    ]


def _snapshot(
    site: dict[str, Any],
    composite: dict[str, Any],
    band: dict[str, Any],
    composite_summary: dict[str, Any] | None,
    country_profile_link: str | None,
) -> list[str]:
    lat = site.get("latitude")
    lon = site.get("longitude")
    cs = composite_summary or {}
    band_letter = band.get("band") or "-"
    top10 = band.get("top10pct_hit_rate")
    coord_text = (
        f"{float(lat):.4f}, {float(lon):.4f}"
        if lat is not None and lon is not None else "-"
    )
    capacity_mw = int(site.get("installed_capacity_mw") or 0)
    rows: list[tuple[str, str]] = [
        ("Site name", str(site.get("name") or "-")),
        ("Coordinates", coord_text),
        ("Subnational unit", str(site.get("subnational_unit") or "-")),
        ("Installed thermal capacity (source data)", f"{capacity_mw:,} MW"),
        (
            "Composite score (baseline weights)",
            f"{_num(composite.get('composite_score'), 3)} "
            f"({_num(composite.get('composite_score_low'), 3)}-"
            f"{_num(composite.get('composite_score_high'), 3)} MC band)",
        ),
        (
            "National stability band",
            f"{band_letter} (top-10% hit rate {_pct(top10)})",
        ),
        ("National rank", str(cs.get("national_rank") or "-")),
    ]
    lines = ["", "## Site Snapshot", "", "| Field | Value |", "| --- | --- |"]
    for label, value in rows:
        lines.append(f"| {label} | {value} |")
    if country_profile_link:
        lines += [
            "",
            f"_See the country status map in_ "
            f"[{country_profile_link['label']}]({country_profile_link['href']}).",
        ]
    return lines


def _ownership_section(
    ownership: list[dict[str, Any]],
    units: list[dict[str, Any]],
) -> list[str]:
    if not ownership and not units:
        return []
    lines = ["", "## Ownership and Coal-to-Nuclear Context", ""]
    grouped: dict[str, dict[str, Any]] = {}
    for row in ownership:
        key = row.get("parent_name") or "Unknown parent"
        existing = grouped.setdefault(
            key,
            {
                "parent_name": key,
                "share_pct": row.get("share_pct"),
                "ownership_path": row.get("ownership_path"),
                "immediate_owner": row.get("immediate_owner"),
                "parent_hq_country": row.get("parent_hq_country"),
            },
        )
        if existing.get("share_pct") is None and row.get("share_pct") is not None:
            existing["share_pct"] = row["share_pct"]
    for entry in grouped.values():
        share = (
            f" ({_num(entry['share_pct'], 2)}% share)"
            if entry.get("share_pct") is not None else ""
        )
        hq = entry.get("parent_hq_country")
        hq_text = f", headquartered in {hq}" if hq else ""
        operator = entry.get("immediate_owner") or "unknown"
        path = entry.get("ownership_path") or ""
        lines.append(
            f"- **{entry['parent_name'].strip()}**{share}{hq_text}; "
            f"immediate operator {operator}. Path: {path}"
        )
    if units:
        status_counts: dict[str, int] = defaultdict(int)
        retire_years: list[int] = []
        start_years: list[int] = []
        for row in units:
            status_counts[str(row.get("status") or "unknown")] += 1
            if row.get("retired_year"):
                retire_years.append(int(row["retired_year"]))
            if row.get("start_year"):
                start_years.append(int(row["start_year"]))
        summary = ", ".join(f"{n} {s}" for s, n in sorted(status_counts.items()))
        lines += [
            "",
            f"Generating units on record: {summary}.",
        ]
        if start_years:
            lines.append(
                f"Earliest unit commissioning: {min(start_years)}; "
                f"most recent: {max(start_years)}."
            )
        if retire_years:
            lines.append(
                f"Retirements span {min(retire_years)} to {max(retire_years)}, "
                "leaving brownfield grid, water, transport, and workforce "
                "assets that materially shorten Stage 3 site preparation."
            )
    return lines


def _family_section(
    heading: str,
    family_keys: str | list[str],
    families: dict[str, Any],
    grouped_scores: dict[str, list[dict[str, Any]]],
    *,
    site_id: str = "",
    bundle_name: str = "",
    family_key: str,
    family_label: str,
) -> list[str]:
    if isinstance(family_keys, str):
        keys = [family_keys]
    else:
        keys = list(family_keys)
    items: list[dict[str, Any]] = []
    for key in keys:
        items.extend(grouped_scores.get(key, []))
    if not items:
        return [""] + [heading, "", "No structured criterion rows for this family."]
    lines = ["", heading, ""]
    for item in sorted(items, key=lambda i: i["criterion_id"]):
        cid = item["criterion_id"]
        crit_name = _full_name(cid)
        evidence = evidence_for(cid, families)
        signals = evidence["signals"]
        score = item.get("score_0_10")
        score_text = (
            f"{_num(score, 1)}/10"
            f" (MC {_num(item.get('score_low_0_10'), 1)}-"
            f"{_num(item.get('score_high_0_10'), 1)})"
            if score is not None else "no native score"
        )
        weight = item.get("weight_normalised")
        weight_text = (
            f"weight {_num(weight, 4)}"
            if weight is not None else "weight n/a"
        )
        signals_text = "; ".join(signals) if signals else "values not in measurement tables"
        quality = _sanitize_quality(quality_for(cid, families))
        lines.append(
            f"- **{crit_name} ({cid})** - score {score_text}, {weight_text}, "
            f"data quality {quality}. Evidence: {signals_text}."
        )
    lines += [
        "",
        f"### Interpretation - {family_label}",
        "",
    ]
    lines += _site_placeholder(
        key=family_key, label=f"Interpretation - {family_label}",
        site_id=site_id, bundle_name=bundle_name,
    )
    return lines


def _site_placeholder(
    *, key: str, label: str, site_id: str, bundle_name: str,
) -> list[str]:
    """Emit a parseable specialist-interpretation placeholder block.

    The ``run_specialist_pass`` helper CLI locates these blocks via
    regex. The Cursor agent reads the single ``siting_expert.md``
    prompt and the bundle slice with ``show`` and writes the
    paragraph back with ``patch``.
    """
    open_tag = (
        f"<!-- specialist key={key} scope=site site_id={site_id} "
        f"bundle={bundle_name} status=pending -->"
    )
    close_tag = f"<!-- /specialist key={key} -->"
    msg = (
        f"> _Specialist interpretation pending: {label}. Cursor agent "
        "fills via "
        f"`python -m scripts.run_specialist_pass show --country <CC> "
        f"--site-name <name> --key {key}` then `... patch --country <CC> "
        f"--site-name <name> --key {key} --text-file <draft.md>`._"
    )
    return ["", open_tag, msg, close_tag]


def _composite_block(
    composite: dict[str, Any],
    bands: list[dict[str, Any]],
    site: dict[str, Any],
    chart_paths: dict[str, str],
    *,
    site_id: str = "",
    bundle_name: str = "",
) -> list[str]:
    band = _band_for(bands, site.get("country_code"))
    block = [
        "",
        "## Composite Score and Stability",
        "",
        f"Baseline composite score is {_num(composite.get('composite_score'), 3)}, "
        f"bracketed by Monte Carlo at "
        f"{_num(composite.get('composite_score_low'), 3)}-"
        f"{_num(composite.get('composite_score_high'), 3)}. National "
        f"stability band is `{band.get('band') or '-'}` with a top-10% hit "
        f"rate of {_pct(band.get('top10pct_hit_rate'))} across "
        f"{band.get('scenarios_scored') or '-'} scored Monte Carlo "
        f"scenarios.",
        "",
        f"![Criterion scores](../figures/{chart_paths.get('criterion','')})",
        "",
        f"![Family contributions](../figures/{chart_paths.get('family','')})",
    ]
    block += _site_placeholder(
        key="stability",
        label="Composite stability and sensitivity (plain-English read)",
        site_id=site_id, bundle_name=bundle_name,
    )
    return block


def _residual_register(
    grouped: dict[str, list[dict[str, Any]]],
    verdicts: list[dict[str, Any]],
    families: dict[str, Any],
    *,
    site_id: str = "",
    bundle_name: str = "",
) -> list[str]:
    """Emit the heading and one specialist placeholder.

    The actual register (markdown table + closing paragraph) is the
    output of the siting expert filling the placeholder. The
    auto-generated bullet preamble that earlier versions emitted was
    redundant once the specialist register became the deliverable.
    """
    del grouped, verdicts, families  # signals consumed by the slicer
    block = ["", "## Residual Risk Register", ""]
    block += _site_placeholder(
        key="residual_risk",
        label="Residual risk register (specialist synthesis)",
        site_id=site_id, bundle_name=bundle_name,
    )
    return block


def _stage3_checklist(
    rankings: list[dict[str, Any]],
    verdicts: list[dict[str, Any]],
    families: dict[str, Any],
    crit_meta: dict[str, dict[str, Any]],
) -> list[str]:
    items: list[str] = []
    for v in verdicts:
        if str(v.get("phase")) == "avoidance" and str(v.get("verdict")) in ("fail", "caution"):
            items.append(
                f"- [ ] Resolve **{_full_name(v['criterion_id'])} "
                f"({v['criterion_id']})** avoidance flag - measured "
                f"{v.get('measured_value')} vs threshold {v.get('threshold')}."
            )
    weakest = sorted(
        [r for r in rankings if r.get("score_0_10") is not None],
        key=lambda r: float(r["score_0_10"]),
    )[:5]
    for r in weakest:
        cid = r["criterion_id"]
        items.append(
            f"- [ ] Re-measure **{_full_name(cid)} ({cid})** - native "
            f"score {_num(r['score_0_10'], 1)}/10 with confidence "
            f"{r.get('confidence')}."
        )
    for cid in CRITERION_FIELDS:
        q = quality_for(cid, families)
        if q in ("low", "no_data", "not_found"):
            items.append(
                f"- [ ] Improve data quality for **{_full_name(cid)} "
                f"({cid})** - current flag `{_sanitize_quality(q)}`."
            )
    return ["", "## Stage 3 Follow-Up Checklist", "", *items[:12]]


def _limitations(
    grouped: dict[str, list[dict[str, Any]]],
    families: dict[str, Any],
) -> list[str]:
    flags: list[str] = []
    for cid in CRITERION_FIELDS:
        q = quality_for(cid, families)
        if q in ("low", "no_data", "not_found"):
            flags.append(
                f"- {_full_name(cid)} ({cid}) - quality `{_sanitize_quality(q)}`."
            )
    if not flags:
        flags.append("- No criterion-family quality fields are flagged as low or missing in this bundle.")
    return ["", "## Evidence Limitations", "", *flags]


def _full_name(criterion_id: str) -> str:
    return _CRITERIA_NAME_CACHE.get(
        criterion_id, criterion_id,
    )


_QUALITY_GRADE_WHITELIST = frozenset(
    {"high", "medium", "low", "insufficient", "no_data", "not_found", "n/a"}
)


def _sanitize_quality(value: str | None) -> str:
    """Strip any source-name leak from the quality string.

    Quality fields in the bundle sometimes carry the dataset slug
    (e.g. ``copernicus_dem_30m``, ``ghsl_pop_100m_r2023a``,
    ``natura2000_eea_wfs``) instead of one of the standard grade
    labels. The report is not allowed to reveal upstream sources, so
    anything outside the grade whitelist is rendered as
    ``screening grade``.
    """
    if not value:
        return "n/a"
    text = str(value).strip().lower()
    if text in _QUALITY_GRADE_WHITELIST:
        return text
    return "screening grade"


def set_criteria_lookup(lookup: dict[str, dict[str, Any]]) -> None:
    """Inject a criteria lookup so renderer can use full names."""
    _CRITERIA_NAME_CACHE.clear()
    _CRITERIA_NAME_CACHE.update(
        {cid: meta["name"] for cid, meta in lookup.items()}
    )


_CRITERIA_NAME_CACHE: dict[str, str] = {}


def _num(value: Any, digits: int) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def _pct(value: Any) -> str:
    if value is None:
        return "-"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    if v <= 1.0:
        v *= 100
    return f"{v:.0f}%"


_ = STATUS_LABEL  # re-export marker; keeps STATUS_LABEL available for callers


def _is_hard_fail(
    composite: dict[str, Any], verdicts: list[dict[str, Any]],
) -> bool:
    """A site is hard-fail when no baseline composite exists or when at
    least one exclusionary verdict is a fail. The composite check covers
    the common case in which the scoring pass simply skipped the site."""
    if composite.get("composite_score") is None:
        return any(
            (str(v.get("phase")) == "exclusionary"
             and str(v.get("verdict")) == "fail")
            for v in verdicts
        )
    return False


def _render_hard_fail(
    *,
    site: dict[str, Any],
    verdicts: list[dict[str, Any]],
    ownership: list[dict[str, Any]],
    units: list[dict[str, Any]],
    country_name: str,
    smr_label: str,
    country_profile_link: dict[str, str] | None,
    site_id: str,
    bundle_name: str,
) -> str:
    """Compact site profile for a hard-fail site.

    Emits: header + one-line subtitle, snapshot table, "Why it failed"
    paragraph and table, and a single ``unlock_analysis`` specialist
    placeholder. Skips family bullets, the composite block, the
    residual-risk register, and the Stage-3 checklist (none of which
    add value when the site is removed at the exclusionary screen).
    """
    name = site.get("name") or "Site"
    cname = country_name.split(" (", 1)[0]
    fails = [
        v for v in verdicts
        if str(v.get("phase")) == "exclusionary"
        and str(v.get("verdict")) == "fail"
    ]
    fails.sort(key=lambda v: str(v.get("criterion_id") or ""))

    lines: list[str] = [
        f"# {name} Site Profile",
        "",
        f"_{cname} | tested against the {smr_label} reference deployment "
        "envelope | **Hard-fail at the exclusionary screen**._",
        "",
        f"{name} is a coal/thermal site in {cname} that does not survive "
        f"the exclusionary screen against the {smr_label} reference "
        "deployment envelope. This profile records the screening "
        "evidence that drives the failure and provides the siting "
        "expert's read on whether further characterization is justified. "
        "It is not a site-suitability determination, vendor "
        "recommendation, or licensing finding.",
    ]

    lat = site.get("latitude")
    lon = site.get("longitude")
    coord_text = (
        f"{float(lat):.4f}, {float(lon):.4f}"
        if lat is not None and lon is not None else "-"
    )
    capacity_mw = int(site.get("installed_capacity_mw") or 0)
    parents = sorted({
        (row.get("parent_name") or "").strip()
        for row in ownership if (row.get("parent_name") or "").strip()
    })
    parent_text = ", ".join(parents) if parents else "-"
    fail_codes = ", ".join(
        sorted({str(v.get("criterion_id") or "") for v in fails})
    ) or "-"

    rows = [
        ("Site name", str(name)),
        ("Country", cname),
        ("Coordinates", coord_text),
        ("Subnational unit", str(site.get("subnational_unit") or "-")),
        ("Installed thermal capacity (source data)", f"{capacity_mw:,} MW"),
        ("Operating status", str(site.get("status") or "-")),
        ("Parent owner(s)", parent_text),
        ("Generating units on record", str(len(units))),
        ("Screening verdict", "Hard-fail (exclusionary)"),
        ("Failed exclusionary criteria", fail_codes),
        ("Composite score", "— (not scored)"),
        ("National stability band", "— (not banded)"),
    ]
    lines += ["", "## Site Snapshot", "", "| Field | Value |", "| --- | --- |"]
    for label, value in rows:
        lines.append(f"| {label} | {value} |")
    if country_profile_link:
        lines += [
            "",
            f"_See the country status map in_ "
            f"[{country_profile_link['label']}]({country_profile_link['href']}).",
        ]

    lines += [
        "",
        "## Why It Failed",
        "",
        f"The site fails {len(fails)} exclusionary criterion(a) below. "
        "Exclusionary failures act as gates: a single confirmed failure "
        "removes the site from the brownfield candidate pool until the "
        "underlying measurement is refuted by site-specific Stage 3 work "
        "or until a regulatory threshold change makes the failure moot.",
        "",
        "| Criterion | Code | Measured value | Threshold | Confidence | Justification |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for v in fails:
        cid = str(v.get("criterion_id") or "")
        crit_name = _full_name(cid)
        m = v.get("measured_value")
        m_unit = v.get("measured_units") or ""
        m_text = f"{m}" if m is not None else "-"
        if m_unit and m is not None:
            m_text = f"{m} {m_unit}".strip()
        t = v.get("threshold") or "-"
        conf = v.get("confidence") or "-"
        just = (v.get("justification") or "").replace("|", "\\|").strip()
        if len(just) > 220:
            just = just[:217] + "..."
        lines.append(
            f"| {crit_name} | {cid} | {m_text} | {t} | {conf} | {just} |"
        )

    lines += ["", "## Unlock Analysis", ""]
    lines += _site_placeholder(
        key="unlock_analysis",
        label="Unlock analysis (deprecate / characterize / escalate)",
        site_id=site_id, bundle_name=bundle_name,
    )

    lines += [
        "",
        "## Evidence Limitations",
        "",
        "- This profile is intentionally compact. Composite scoring, "
        "Monte-Carlo stability, family contributions, and the residual "
        "risk register are omitted because none of those views are "
        "informative for a site that is removed at the exclusionary "
        "screen.",
        "- The exclusionary thresholds are screening thresholds; site-"
        "specific Stage 3 measurement can either confirm the failure or "
        "lift it. The unlock analysis above states whether that "
        "investment is justified.",
    ]

    return "\n".join(lines) + "\n"


__all__ = ["render_site_markdown_from_bundle", "set_criteria_lookup"]
