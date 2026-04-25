# man_hours: 0.75
"""Markdown methodology renderer for the Phase 1.6 failure analysis."""

from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path

from atoms_vs_ashes.scoring._failure_breakdown import (
    CountryStat,
    CriterionStat,
    FailureBreakdown,
    SmrStat,
)


def _link(target: Path, anchor: Path) -> str:
    try:
        return target.relative_to(anchor.parent.resolve()).as_posix()
    except ValueError:
        return os.path.relpath(target, anchor.parent).replace(os.sep, "/")


def _md_table_per_criterion(rows: Sequence[CriterionStat]) -> str:
    head = (
        "| Criterion | Name | Hard fails | Floor fails | "
        "Hard ∧ floor | Total pairs failed |\n"
        "| --- | --- | ---: | ---: | ---: | ---: |"
    )
    lines = [head]
    for r in rows:
        lines.append(
            f"| `{r.criterion_id}` | {r.criterion_name} | {r.hard_pairs} | "
            f"{r.floor_pairs} | {r.intersection_pairs} | {r.union_pairs} |"
        )
    return "\n".join(lines)


def _md_table_per_country(rows: Sequence[CountryStat]) -> str:
    head = (
        "| Country | n sites | n pairs | Survived | Hard only | "
        "Hard ∧ floor | Floor only | Sites w/ survivor |\n"
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
    )
    lines = [head]
    for r in rows:
        lines.append(
            f"| {r.country_code} | {r.n_sites} | {r.n_pairs} | "
            f"{r.survived} | {r.hard_only} | {r.both} | "
            f"{r.floor_only} | {r.n_sites_with_survivor} |"
        )
    return "\n".join(lines)


def _md_table_per_smr(rows: Sequence[SmrStat]) -> str:
    head = (
        "| SMR design | n pairs | Survived | Hard only | "
        "Hard ∧ floor | Floor only |\n"
        "| --- | ---: | ---: | ---: | ---: | ---: |"
    )
    lines = [head]
    for r in rows:
        lines.append(
            f"| `{r.smr_key}` | {r.n_pairs} | {r.survived} | "
            f"{r.hard_only} | {r.both} | {r.floor_only} |"
        )
    return "\n".join(lines)


def _md_table_multi_failure(histogram: dict[int, int]) -> str:
    if not histogram:
        return "_No compound failures observed._"
    head = (
        "| Distinct criteria failed | Pairs |\n"
        "| ---: | ---: |"
    )
    lines = [head]
    for k in sorted(histogram):
        lines.append(f"| {k} | {histogram[k]} |")
    return "\n".join(lines)


def render_methodology(
    breakdown: FailureBreakdown,
    *,
    stamp: str,
    run_id: str | None,
    audit_paths: dict[str, Path],
    figure_paths: dict[str, Path],
    out_path: Path,
) -> Path:
    """Render the methodology MD file. Creates parent dir if needed."""
    survived_pct = (
        breakdown.survived / breakdown.total_pairs * 100.0
        if breakdown.total_pairs else 0.0
    )
    floor_dom_pct = (
        breakdown.failed_by_floor / breakdown.failed_any * 100.0
        if breakdown.failed_any else 0.0
    )

    parts: list[str] = [
        f"# Phase 1.6 failure-mode analysis — {stamp}",
        "",
        f"- Run ID: `{run_id or '(none)'}`",
        f"- Universe: **{breakdown.total_pairs}** (site, SMR) pairs across "
        f"{breakdown.n_distinct_sites} sites × {breakdown.n_distinct_smrs} "
        "SMR designs.",
        f"- Survivors: **{breakdown.survived}** "
        f"({survived_pct:.1f} % of the universe).",
        f"- Failed any exclusionary check: **{breakdown.failed_any}** "
        f"(hard only **{breakdown.hard_only}**, floor only "
        f"**{breakdown.floor_only}**, hard ∧ floor **{breakdown.both}**).",
        f"- Of failed pairs, **{floor_dom_pct:.1f} %** are caught by the "
        "safety floor at some criterion (alone or together with a hard "
        "E-code).",
        "",
        "Source artefacts:",
        f"- `{audit_paths['summary'].as_posix()}` — top-level counts.",
        f"- `{audit_paths['per_criterion'].as_posix()}` — per-criterion "
        "fails.",
        f"- `{audit_paths['per_country'].as_posix()}` — per-country fails.",
        f"- `{audit_paths['per_smr'].as_posix()}` — per-SMR fails.",
        f"- `{audit_paths['per_pair'].as_posix()}` — one row per (site, "
        "SMR).",
        "",
        "Two failure mechanisms are tracked side by side:",
        "",
        "1. **Hard E-code** (`prompt_key = E1, E2, …`) — a rubric "
        "`condition_expr` evaluated to true (e.g. `nearest_fault_km < 5`).",
        "2. **Safety floor** (`prompt_key = E<k>:floor`) — the 0–10 "
        "ranking score for an exclusionary criterion is strictly below "
        "its declared `pass_mark`. See "
        "[`exclusionary_floors.md`](./exclusionary_floors.md).",
        "",
        "Both produce `passed_exclusionary = False` and "
        "`composite_score = NULL`. Per-criterion ranking rows are kept "
        "on disk for transparency, so the audit can show *why* a site "
        "failed without contaminating the suitable-site ranking.",
        "",
        "## 1. Funnel — universe → survivors",
        "",
        f"![Failure funnel]({_link(figure_paths['funnel'], out_path)})",
        "",
        "## 2. Failures by exclusionary criterion",
        "",
        "Counts are unique pairs (a pair that triggers both `EP-01` hard "
        "and `EP-01:floor` is counted once in `Hard ∧ floor`, **not** "
        "twice).",
        "",
        _md_table_per_criterion(breakdown.per_criterion),
        "",
        f"![Failures by criterion]"
        f"({_link(figure_paths['per_criterion'], out_path)})",
        "",
        "## 3. Failures by country",
        "",
        _md_table_per_country(breakdown.per_country),
        "",
        f"![Per-country outcomes]"
        f"({_link(figure_paths['per_country'], out_path)})",
        "",
        "## 4. Failures by SMR design",
        "",
        "All exclusionary fail expressions in the current rubric are "
        "site-physics-driven (faults, slope, karst, EP-01 composite "
        "score, trauma-centre access). None reference the SMR's EPZ "
        "radius, footprint, or thermal output, so the screening verdicts "
        "are SMR-invariant by construction. SMR design only matters in "
        "the `ranking` phase (different `weight_factor` × score "
        "combinations). If future rubric iterations need SMR-specific "
        "exclusions (e.g. EPZ radius vs. nearest population centre), the "
        "rows below will diverge.",
        "",
        _md_table_per_smr(breakdown.per_smr),
        "",
        f"![Per-SMR outcomes]({_link(figure_paths['per_smr'], out_path)})",
        "",
        "## 5. Compound vs. single-criterion failures",
        "",
        _md_table_multi_failure(breakdown.multi_failure_histogram),
        "",
        f"![Multi-failure histogram]"
        f"({_link(figure_paths['multi_failure'], out_path)})",
        "",
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
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")
    return out_path


__all__ = ["render_methodology"]
