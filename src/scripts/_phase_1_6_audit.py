# man_hours: 2.0
"""Consolidated-audit writer for Phase 1.6.

Pulls cross-profile stability metrics from :mod:`_phase_1_6_analytics`
and the standalone artefacts from :mod:`_suite_importance` and
:mod:`_suite_banding`, then produces a single regulatory-style
markdown report. Kept ≤ 300 lines per the python file-size rule.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from scripts._phase_1_6_analytics import (
    PhaseAnalytics,
    ProfileStats,
)
from scripts._phase_1_6_audit_tables import (
    append_banding_table,
    append_country_summary_table,
    append_importance_table,
)
from atoms_vs_ashes.scoring.suite import SensitivitySuiteResult


def write_consolidated_audit(
    audit_dir: Path,
    run_id: str,
    db_profile: str,
    stages: list[SensitivitySuiteResult],
    analytics: PhaseAnalytics,
    *,
    importance_csv: Path | None = None,
    bands_csv: Path | None = None,
    nuscale_bands_csv: Path | None = None,
    country_summary_csv: Path | None = None,
) -> Path:
    """Write ``<audit_dir>/<YYYYMMDD>_phase1_6_sensitivity.md``.

    Optional paths surface OAT importance, A–H bands (regional pool +
    NuScale) and the country roll-up as top-level audit sections.
    """
    audit_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    path = audit_dir / f"{stamp}_phase1_6_sensitivity.md"

    lines: list[str] = []
    lines.append(f"# Phase 1.6 sensitivity suite — {stamp}")
    lines.append("")
    lines.append(f"- Run ID: `{run_id}`")
    lines.append(f"- DB profile: `{db_profile}`")
    lines.append(f"- Stages run: {len(stages)}")
    first = stages[0] if stages else None
    if first is not None:
        lines.append(f"- Pairs processed: **{first.pairs}** (sites × SMRs)")
    lines.append(
        f"- Baseline scored rows: **{analytics.baseline_scored_rows}** / "
        f"{analytics.baseline_total_rows}"
    )
    lines.append(
        f"- Top-5 % slice: **{analytics.baseline_top5pct_size}** pairs; "
        f"top-10 % slice: **{analytics.baseline_top10pct_size}** pairs."
    )
    lines.append("")

    _append_executive_summary(lines, analytics)
    append_importance_table(lines, importance_csv)
    _append_stage_table(lines, stages)
    _append_stability_table(lines, analytics)
    _append_category_table(lines, analytics)
    append_banding_table(
        lines,
        bands_csv,
        heading="Site stability banding (regional, all SMRs)",
        scope_hint="Percentiles computed across all scored (site, SMR) pairs.",
    )
    append_banding_table(
        lines,
        nuscale_bands_csv,
        heading="Site stability banding — NuScale `nuscale_voygr6`",
        scope_hint="Percentiles computed on the NuScale-only pool.",
    )
    append_country_summary_table(lines, country_summary_csv)
    _append_country_balance(lines, first, analytics)
    _append_profile_legend(lines, stages)
    _append_notes(lines, stages, analytics)
    _append_json_block(lines, stages)

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Section helpers
# ---------------------------------------------------------------------------


def _append_executive_summary(lines: list[str], analytics: PhaseAnalytics) -> None:
    lines.append("## Executive summary")
    lines.append("")
    if not analytics.profiles:
        lines.append(
            "_No non-baseline profiles found — the sensitivity run has not "
            "persisted any rows yet._"
        )
        lines.append("")
        return
    worst = min(analytics.profiles, key=lambda p: p.top10pct_jaccard)
    biggest_drift = max(
        (p for p in analytics.profiles if p.mean_abs_drift is not None),
        key=lambda p: p.mean_abs_drift or 0.0,
        default=None,
    )
    lines.append(
        f"- Profiles compared vs `baseline`: **{len(analytics.profiles)}**."
    )
    lines.append(
        f"- Lowest top-10 % Jaccard: **{worst.top10pct_jaccard}** "
        f"(profile `{worst.label}`, overlap "
        f"{worst.top10pct_overlap}/{analytics.baseline_top10pct_size})."
    )
    if biggest_drift is not None:
        lines.append(
            f"- Largest mean |Δscore|: **{biggest_drift.mean_abs_drift}** "
            f"(profile `{biggest_drift.label}`)."
        )
    lines.append("")


def _append_stage_table(
    lines: list[str], stages: list[SensitivitySuiteResult]
) -> None:
    lines.append("## Stages")
    lines.append("")
    lines.append(
        "| # | Stage | Iterations | Weight rows | MC rows | Threshold rows "
        "| Country rows | Audit file |"
    )
    lines.append("| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for idx, r in enumerate(stages, start=1):
        stage_label = f"MC @ {r.iterations}"
        if r.preset_label:
            stage_label += f" ({r.preset_label})"
        audit_name = Path(r.audit_path).name if r.audit_path else "(none)"
        lines.append(
            f"| {idx} | {stage_label} | {r.iterations} | "
            f"{r.weight_rows_persisted} | {r.mc_rows_persisted} | "
            f"{r.threshold_rows_persisted} | "
            f"{r.country_balanced_rows_persisted} | `{audit_name}` |"
        )
    lines.append("")


def _append_stability_table(lines: list[str], analytics: PhaseAnalytics) -> None:
    lines.append("## Top-N stability vs. baseline (pct-based)")
    lines.append("")
    if not analytics.profiles:
        lines.append("_No perturbed profiles to compare._")
        lines.append("")
        return
    b5 = analytics.baseline_top5pct_size or 0
    b10 = analytics.baseline_top10pct_size or 0
    lines.append(
        f"Top-5 % = **{b5}** pairs; top-10 % = **{b10}** pairs "
        "(fractions of the baseline scored slice)."
    )
    lines.append("")
    lines.append(
        "| Profile | Scored pairs | Top-5 % overlap | Jaccard@5 % | "
        "Top-10 % overlap | Jaccard@10 % | Mean |Δ| | Max |Δ| | Pairs in drift |"
    )
    lines.append(
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
    )
    for p in analytics.profiles:
        lines.append(_stability_row(p, b5, b10))
    lines.append("")


def _stability_row(p: ProfileStats, b5: int, b10: int) -> str:
    return (
        f"| `{p.label}` | {p.scored_rows} | "
        f"{p.top5pct_overlap}/{b5 or p.top5pct_size} | "
        f"{p.top5pct_jaccard} | "
        f"{p.top10pct_overlap}/{b10 or p.top10pct_size} | "
        f"{p.top10pct_jaccard} | "
        f"{_fmt(p.mean_abs_drift)} | {_fmt(p.max_abs_drift)} | "
        f"{p.pairs_drift_compared} |"
    )


def _fmt(value: float | None) -> str:
    return "—" if value is None else f"{value}"


def _append_category_table(lines: list[str], analytics: PhaseAnalytics) -> None:
    lines.append("## Weight sensitivity by category (±20 %)")
    lines.append("")
    if not analytics.per_category_weight:
        lines.append(
            "_No per-category weight profiles persisted yet — re-run the "
            "suite after fixing the weight perturbation bug._"
        )
        lines.append("")
        return
    b10 = analytics.baseline_top10pct_size or 0
    lines.append(
        f"| Category | Avg mean |Δscore| | Avg top-10 % overlap (of {b10}) |"
    )
    lines.append("| --- | ---: | ---: |")
    for cat, drift, overlap in analytics.per_category_weight:
        lines.append(f"| `{cat}` | {drift} | {overlap} |")
    lines.append("")


def _append_country_balance(
    lines: list[str],
    first: SensitivitySuiteResult | None,
    analytics: PhaseAnalytics,
) -> None:
    lines.append("## Country balance (baseline top-10 %)")
    lines.append("")
    counts = analytics.baseline_top10pct_countries
    if counts:
        lines.append("| Country | Count |")
        lines.append("| --- | ---: |")
        for code, cnt in counts.items():
            lines.append(f"| {code} | {cnt} |")
        lines.append("")
    if first is None or first.country_report is None:
        lines.append("_No stage-level country report produced._")
        lines.append("")
        return
    rep = first.country_report
    lines.append(
        f"- Stage 1 country-balance report: max_share=**{rep['max_share']}** "
        f"(flagged: **{rep['flagged']}**; threshold 40 %)."
    )
    lines.append("")


def _append_profile_legend(
    lines: list[str], stages: list[SensitivitySuiteResult]
) -> None:
    lines.append("## Weight profiles persisted")
    lines.append("")
    lines.append("Each stage writes into ``composite_rankings`` using these labels:")
    lines.append("")
    lines.append("- `baseline` — original Phase 1.5 run (not written by this script).")
    lines.append(
        "- `w_<CAT>_plus_20` / `w_<CAT>_minus_20` — per-category weight "
        "perturbation for CAT ∈ {NH, HI, RI, EP, NS}."
    )
    for r in stages:
        lines.append(f"- `mc_{r.iterations}` — Monte Carlo @ N={r.iterations}.")
    lines.append(
        "- `threshold_plus_25` / `threshold_minus_25` — "
        "numeric context scaled by ±25 %."
    )
    lines.append("- `country_balanced` — baseline clone used by the top-N check.")
    lines.append("")


def _append_notes(
    lines: list[str],
    stages: list[SensitivitySuiteResult],
    analytics: PhaseAnalytics,
) -> None:
    lines.append("## Notes")
    lines.append("")
    aggregated: set[str] = set()
    for r in stages:
        aggregated.update(r.notes)
    for w in analytics.warnings:
        aggregated.add(f"analytics: {w}")
    if not aggregated:
        lines.append("- (no stage-level notes)")
    else:
        for n in sorted(aggregated):
            lines.append(f"- `{n}`")
    lines.append("")


def _append_json_block(
    lines: list[str], stages: list[SensitivitySuiteResult]
) -> None:
    lines.append("## Per-stage JSON")
    lines.append("")
    lines.append("```json")
    lines.append(
        json.dumps([r.to_dict() for r in stages], indent=2, default=str)
    )
    lines.append("```")
    lines.append("")
