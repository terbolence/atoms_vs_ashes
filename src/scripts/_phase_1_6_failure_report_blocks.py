# man_hours: 0.5
"""Markdown table renderers + reusable static blocks for the failure report.

Split out of :mod:`scripts._phase_1_6_failure_report` to keep that
module under 300 lines. Pure formatting; no I/O, no DB.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from atoms_vs_ashes.scoring._failure_breakdown import (
    CountryStat,
    CriterionStat,
    FailureBreakdown,
    SmrStat,
)


def pct(num: int, denom: int, *, digits: int = 1) -> str:
    if denom <= 0:
        return "n/a"
    return f"{(num / denom) * 100.0:.{digits}f}%"


def md_table_per_criterion(
    rows: Sequence[CriterionStat], *, total_failed: int,
) -> str:
    head = (
        "| Criterion | Name | Hard fails | Floor fails | "
        "Hard ∧ floor | Total pairs failed | Share of all failures |\n"
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |"
    )
    lines = [head]
    for r in rows:
        lines.append(
            f"| `{r.criterion_id}` | {r.criterion_name} | {r.hard_pairs} | "
            f"{r.floor_pairs} | {r.intersection_pairs} | {r.union_pairs} | "
            f"{pct(r.union_pairs, total_failed)} |"
        )
    return "\n".join(lines)


def md_table_per_country(
    rows: Sequence[CountryStat], *, country_pretty: Mapping[str, str],
) -> str:
    head = (
        "| ISO | Country | n sites | n pairs | Survived | "
        "Survival rate | Hard only | Hard ∧ floor | Floor only | "
        "Sites w/ survivor |\n"
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
    )
    lines = [head]
    for r in rows:
        name = country_pretty.get(r.country_code, r.country_code)
        lines.append(
            f"| {r.country_code} | {name} | {r.n_sites} | {r.n_pairs} | "
            f"{r.survived} | {pct(r.survived, r.n_pairs)} | "
            f"{r.hard_only} | {r.both} | {r.floor_only} | "
            f"{r.n_sites_with_survivor} |"
        )
    return "\n".join(lines)


def md_table_per_smr(
    rows: Sequence[SmrStat], *, smr_pretty: Mapping[str, str],
) -> str:
    head = (
        "| Vendor / Design | smr_key | n pairs | Survived | "
        "Survival rate | Hard only | Hard ∧ floor | Floor only |\n"
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"
    )
    lines = [head]
    for r in rows:
        name = smr_pretty.get(r.smr_key, r.smr_key)
        lines.append(
            f"| {name} | `{r.smr_key}` | {r.n_pairs} | {r.survived} | "
            f"{pct(r.survived, r.n_pairs)} | "
            f"{r.hard_only} | {r.both} | {r.floor_only} |"
        )
    return "\n".join(lines)


def md_table_multi_failure(
    histogram: dict[int, int], *, total_failed: int,
) -> str:
    if not histogram:
        return "_No compound failures observed._"
    head = (
        "| Distinct criteria failed | Pairs | Share of failed |\n"
        "| ---: | ---: | ---: |"
    )
    lines = [head]
    for k in sorted(histogram):
        lines.append(
            f"| {k} | {histogram[k]} | {pct(histogram[k], total_failed)} |"
        )
    return "\n".join(lines)


def glossary_block() -> str:
    return "\n".join([
        "## Glossary",
        "",
        "| Term | Definition |",
        "| --- | --- |",
        "| **Site** | One candidate parcel identified by `site_id`, "
        "associated with a country code. |",
        "| **SMR design** | One vendor / model identified by `smr_key` "
        "(e.g. `nuscale_voygr6`). 8 designs are evaluated. |",
        "| **Site × technology evaluation (pair)** | One row per "
        "`(site_id, smr_key)` pairing. The universe is sites × designs. |",
        "| **Exclusionary phase** | Pre-scoring screening: a pair is "
        "rejected before any composite score is computed. |",
        "| **Hard E-code** (`prompt_key = E1, E2, …`) | A rubric "
        "`condition_expr` evaluated to true (e.g. `nearest_fault_km < 5`). |",
        "| **Safety floor** (`prompt_key = E<k>:floor`) | The 0–10 "
        "ranking score for an exclusionary criterion is strictly below "
        "its `pass_mark` (5.0 by default). |",
        "| **Survived** | Pair passed every hard E-code and every floor. |",
        "| **Hard only** | Hard expression triggered; floor not breached. |",
        "| **Floor only** | Score below 5.0 floor; rubric expression "
        "did not trigger. |",
        "| **Hard ∧ floor** | Both gates failed for the same pair. |",
        "",
    ])


def tldr_block(
    breakdown: FailureBreakdown, *, smr_label: str | None,
) -> str:
    top = max(breakdown.per_criterion,
              key=lambda r: r.union_pairs, default=None)
    survived_pct = pct(breakdown.survived, breakdown.total_pairs)
    failed_pct = pct(breakdown.failed_any, breakdown.total_pairs)
    floor_pct = pct(breakdown.failed_by_floor, breakdown.failed_any)
    scope = f" ({smr_label})" if smr_label else ""
    lines = [
        f"> **TL;DR{scope}**",
        f"> - **Universe**: **{breakdown.total_pairs}** site × technology "
        f"evaluations across **{breakdown.n_distinct_sites}** sites × "
        f"**{breakdown.n_distinct_smrs}** SMR design(s).",
        f"> - **Survivors**: **{breakdown.survived}** ({survived_pct}); "
        f"**failed any check**: **{breakdown.failed_any}** ({failed_pct}).",
    ]
    if top is not None:
        top_pct = pct(top.union_pairs, breakdown.failed_any)
        lines.append(
            f"> - **Dominant filter**: `{top.criterion_id}` — "
            f"{top.criterion_name}; rejects **{top.union_pairs}** "
            f"pairings ({top_pct} of failed)."
        )
    lines.append(
        f"> - **Floor share**: **{floor_pct}** of failed pairings are "
        "caught by the safety floor (alone or together with a hard E-code)."
    )
    return "\n".join(lines)


def criterion_glossary(rows: Sequence[CriterionStat]) -> str:
    if not rows:
        return ""
    parts = ["**Criterion glossary** "]
    parts.extend(f"`{r.criterion_id}` {r.criterion_name}" for r in rows)
    return "  \n".join(parts)


__all__ = [
    "pct",
    "md_table_per_criterion",
    "md_table_per_country",
    "md_table_per_smr",
    "md_table_multi_failure",
    "glossary_block",
    "tldr_block",
    "criterion_glossary",
]
