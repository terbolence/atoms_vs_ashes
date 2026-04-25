# man_hours: 0.75
"""Markdown methodology renderer for the Phase 1.6 failure analysis."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from atoms_vs_ashes.scoring._failure_breakdown import FailureBreakdown
from scripts._phase_1_6_failure_chart_styles import COUNTRY_NAMES
from scripts._phase_1_6_failure_report_blocks import (
    criterion_glossary,
    glossary_block,
    md_table_multi_failure,
    md_table_per_country,
    md_table_per_criterion,
    md_table_per_smr,
    tldr_block,
)


@dataclass(frozen=True)
class PerTechPack:
    smr_key: str
    pretty_name: str
    method_md: Path
    featured: bool = False


def _link(target: Path, anchor: Path) -> str:
    try:
        return target.relative_to(anchor.parent.resolve()).as_posix()
    except ValueError:
        return os.path.relpath(target, anchor.parent).replace(os.sep, "/")


def _header_block(
    breakdown: FailureBreakdown,
    *,
    stamp: str,
    run_id: str | None,
    smr_label: str | None,
    smr_banner: str | None,
) -> list[str]:
    title = f"# Phase 1.6 failure-mode analysis — {stamp}"
    if smr_label:
        title += f" — {smr_label}"
    parts = [title, ""]
    if smr_banner:
        parts.extend([f"> {smr_banner}", ""])
    parts.extend([
        f"- Run ID: `{run_id or '(none)'}`",
        f"- Stamp: **{stamp}**",
        f"- Universe: **{breakdown.total_pairs}** site × technology "
        "evaluations.",
        "",
        tldr_block(breakdown, smr_label=smr_label),
        "",
    ])
    return parts


def _source_links(audit_paths: dict[str, Path]) -> list[str]:
    keys = [("summary", "top-level counts"),
            ("per_criterion", "per-criterion fails"),
            ("per_country", "per-country fails"),
            ("per_smr", "per-SMR fails"),
            ("per_pair", "one row per (site, SMR)")]
    out = ["Source artefacts:"]
    for key, gloss in keys:
        if key in audit_paths:
            out.append(f"- `{audit_paths[key].as_posix()}` — {gloss}.")
    out.append("")
    return out


_FOOTER_HOWTO = [
    "## 6. How to read this",
    "",
    "- **Floor-only pairs are recoverable in principle**: the "
    "underlying rubric expression did not trigger; tightening the "
    "rubric or improving the data behind the criterion can move the "
    "score above `pass_mark`.",
    "- **Hard-only and `Hard ∧ floor` pairs are not recoverable**: "
    "the rubric's hard expression triggered, so the site is "
    "geophysically or logistically incompatible with the SMR design.",
    "- **Compound failures** (≥ 2 distinct criteria) cluster the "
    "truly unsuitable sites; single-criterion failures are the "
    "candidates for re-examination once data quality improves.",
    "",
]

_INTRO_PROVENANCE = (
    "Two failure mechanisms are tracked side by side: a **hard "
    "E-code** rubric expression triggering, and a **safety floor** "
    "breach where the 0–10 ranking score for an exclusionary "
    "criterion is below its `pass_mark` (5.0). See "
    "[`exclusionary_floors.md`](./exclusionary_floors.md). Both "
    "produce `passed_exclusionary = False` and "
    "`composite_score = NULL`. Per-criterion ranking rows are kept "
    "on disk for transparency, so the audit can show *why* a site "
    "failed without contaminating the suitable-site ranking."
)


def _per_tech_table(
    packs: Sequence[PerTechPack], anchor: Path,
) -> str:
    head = (
        "| Featured | Vendor / Design | smr_key | Methodology MD |\n"
        "| :---: | --- | --- | --- |"
    )
    lines = [head]
    for p in packs:
        marker = "★" if p.featured else ""
        rel = _link(p.method_md, anchor)
        lines.append(
            f"| {marker} | {p.pretty_name} | `{p.smr_key}` | "
            f"[{p.method_md.name}]({rel}) |"
        )
    return "\n".join(lines)


def render_methodology(
    breakdown: FailureBreakdown,
    *,
    stamp: str,
    run_id: str | None,
    audit_paths: dict[str, Path],
    figure_paths: dict[str, Path],
    out_path: Path,
    smr_pretty: Mapping[str, str] | None = None,
    country_pretty: Mapping[str, str] | None = None,
    smr_label: str | None = None,
    smr_banner: str | None = None,
    per_tech_packs: Sequence[PerTechPack] | None = None,
) -> Path:
    """Render the methodology MD file. Creates parent dir if needed."""
    smr_pretty = smr_pretty or {}
    country_pretty = country_pretty or COUNTRY_NAMES

    parts: list[str] = _header_block(
        breakdown, stamp=stamp, run_id=run_id,
        smr_label=smr_label, smr_banner=smr_banner,
    )
    parts.extend(_source_links(audit_paths))
    parts.extend([_INTRO_PROVENANCE, "", glossary_block()])

    parts.extend([
        "## 1. Funnel — universe → survivors",
        "",
        f"![Failure funnel]({_link(figure_paths['funnel'], out_path)})",
        "",
        "## 2. Failures by exclusionary criterion",
        "",
        "Counts are unique pairs (a pair that triggers both `EP-01` hard "
        "and `EP-01:floor` is counted once in `Hard ∧ floor`, **not** "
        "twice). The *Share of all failures* column expresses each "
        "criterion's contribution against the total of "
        f"**{breakdown.failed_any}** failed pairings.",
        "",
        md_table_per_criterion(
            breakdown.per_criterion, total_failed=breakdown.failed_any),
        "",
        criterion_glossary(breakdown.per_criterion),
        "",
        f"![Failures by criterion]"
        f"({_link(figure_paths['per_criterion'], out_path)})",
        "",
        "## 3. Failures by country",
        "",
        "ISO codes follow ISO 3166-1 alpha-2. *Survival rate* is the "
        "share of evaluations within the country that pass every "
        "exclusionary check.",
        "",
        md_table_per_country(
            breakdown.per_country, country_pretty=country_pretty),
        "",
        f"![Per-country outcomes]"
        f"({_link(figure_paths['per_country'], out_path)})",
        "",
    ])

    if "per_smr" in figure_paths and breakdown.per_smr:
        parts.extend([
            "## 4. Failures by SMR design",
            "",
            "All exclusionary fail expressions in the current rubric are "
            "site-physics-driven (faults, slope, karst, EP-01 composite "
            "score, trauma-centre access). None reference the SMR's EPZ "
            "radius, footprint, or thermal output, so the screening "
            "verdicts are SMR-invariant by construction. SMR design only "
            "matters in the `ranking` phase (different `weight_factor` × "
            "score combinations). If future rubric iterations add "
            "SMR-specific exclusions (e.g. EPZ radius vs. nearest "
            "population centre), the rows below will diverge.",
            "",
            md_table_per_smr(breakdown.per_smr, smr_pretty=smr_pretty),
            "",
            f"![Per-SMR outcomes]"
            f"({_link(figure_paths['per_smr'], out_path)})",
            "",
        ])

    parts.extend([
        "## 5. Compound vs. single-criterion failures",
        "",
        md_table_multi_failure(
            breakdown.multi_failure_histogram,
            total_failed=breakdown.failed_any),
        "",
        f"![Multi-failure histogram]"
        f"({_link(figure_paths['multi_failure'], out_path)})",
        "",
    ])
    parts.extend(_FOOTER_HOWTO)
    if per_tech_packs:
        parts.extend([
            "## 7. Per-technology packs",
            "",
            "Each row links to the same five-section analysis restricted "
            "to a single SMR design (CSVs and figures live alongside "
            "under `audit/.../per_smr/<smr_key>/` and "
            "`figures/failure/per_smr/<smr_key>/`). The featured row (★) "
            "is the primary vendor for executive review.",
            "",
            _per_tech_table(per_tech_packs, out_path),
            "",
        ])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")
    return out_path


__all__ = ["render_methodology", "PerTechPack"]
