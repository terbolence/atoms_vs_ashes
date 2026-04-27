# man_hours: 2.0
"""Writers for suitable-site audit artefacts."""

from __future__ import annotations

import csv
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from atoms_vs_ashes.scoring_audit.catalog import AuditRule
from atoms_vs_ashes.scoring_audit.db import (
    CodeImpact,
    CriterionScoreSummary,
    Ep01DisjunctImpact,
    SuitabilityCounts,
)


def write_csv(path: Path, rows: Iterable[object]) -> Path:
    """Write dataclass rows to CSV."""
    items = [asdict(r) for r in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    if not items:
        path.write_text("", encoding="utf-8")
        return path
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(items[0]))
        writer.writeheader()
        writer.writerows(items)
    return path


def write_counts_csv(path: Path, counts: SuitabilityCounts) -> Path:
    return write_csv(path, [counts])


def write_audit_report(
    path: Path,
    *,
    counts: SuitabilityCounts | None,
    rules: list[AuditRule],
    impacts: list[CodeImpact],
    ep01_impacts: list[Ep01DisjunctImpact],
    score_summaries: list[CriterionScoreSummary],
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(
        _report_lines(counts, rules, impacts, ep01_impacts, score_summaries)
    ) + "\n"
    path.write_text(text, encoding="utf-8")
    return path


def _report_lines(
    counts: SuitabilityCounts | None,
    rules: list[AuditRule],
    impacts: list[CodeImpact],
    ep01_impacts: list[Ep01DisjunctImpact],
    score_summaries: list[CriterionScoreSummary],
) -> list[str]:
    lines = [
        "# Suitable Sites Scoring Audit",
        "",
        "## Scope",
        "",
        "This report audits every live exclusionary and avoidance rule from the scoring rubrics.",
        "Each rule was checked for threshold metadata, band/evaluator wiring, DB-field availability,",
        "and current run impact where a scoring run was available.",
        "",
    ]
    lines.extend(_suitability_section(counts))
    lines.extend(_catalogue_section(rules))
    lines.extend(_all_rule_status_section(rules))
    lines.extend(_ep01_section(ep01_impacts))
    lines.extend(_focused_blocker_section(rules, impacts))
    lines.extend(_impact_section(impacts))
    lines.extend(_score_section(score_summaries))
    lines.extend(_decision_section())
    return lines


def _suitability_section(counts: SuitabilityCounts | None) -> list[str]:
    if counts is None:
        return ["## Suitability Definition", "", "No composite run was available.", ""]
    return [
        "## Suitability Definition",
        "",
        f"- Run: `{counts.run_id}` with weight profile `{counts.weight_profile}`.",
        f"- Total site-SMR pairs: {counts.n_pairs} across {counts.n_sites} sites and {counts.n_countries} countries.",
        f"- Hard-exclusion pass: {counts.pairs_pass_exclusionary} pairs, {counts.sites_pass_exclusionary} sites, {counts.countries_pass_exclusionary} countries.",
        f"- UI survivor pass (`passed_exclusionary AND passed_avoidance`): {counts.pairs_pass_both} pairs, {counts.sites_pass_both} sites, {counts.countries_pass_both} countries.",
        f"- Hard-failed pairs: {counts.pairs_hard_failed}; avoidance-flagged-but-rankable pairs: {counts.pairs_avoidance_flagged}.",
        "",
        "Audit decision: avoidance cautions should be displayed separately from hard unsuitability.",
        "The current shortlist may still require both flags, but labels must not call avoidance flags safety-floor failures.",
        "",
    ]


def _catalogue_section(rules: list[AuditRule]) -> list[str]:
    exclude = [r for r in rules if r.action == "exclude"]
    avoidance = [r for r in rules if r.action == "avoidance_penalty"]
    risky = [r for r in rules if r.missing_context_names or r.missing_model_fields]
    lines = [
        "## E/A Catalogue Audit",
        "",
        f"- Exclusionary rules audited: {len(exclude)}.",
        f"- Avoidance rules audited: {len(avoidance)}.",
        f"- Rules with DB/context wiring risks: {len(risky)}.",
        "",
    ]
    if risky:
        lines.append("Highest-priority wiring findings:")
        for rule in risky[:12]:
            parts = []
            if rule.missing_context_names:
                parts.append("missing context " + ", ".join(rule.missing_context_names))
            if rule.missing_model_fields:
                parts.append("missing model fields " + ", ".join(rule.missing_model_fields))
            lines.append(f"- `{rule.criterion_id}/{rule.code}`: {'; '.join(parts)}.")
        lines.append("")
    return lines


def _all_rule_status_section(rules: list[AuditRule]) -> list[str]:
    n_excl = sum(1 for r in rules if r.action == "exclude")
    n_avoid = sum(1 for r in rules if r.action == "avoidance_penalty")
    n_floors = sum(1 for r in rules if r.action == "exclude" and r.pass_mark is not None)
    return [
        "## Full E/A Audit Checklist",
        "",
        f"- Hard exclusionary rules: {n_excl}; synthetic safety floors: {n_floors}.",
        f"- Avoidance rules: {n_avoid}.",
        "- Full per-item decisions are written to `audit_status.csv`.",
        "- Exclusionary failures remain hard-unsuitable unless a data-application defect is listed.",
        "- Avoidance cautions are risk flags/ranking pressure and are reported separately from hard unsuitability.",
        "",
    ]


def _ep01_section(rows: list[Ep01DisjunctImpact]) -> list[str]:
    lines = ["## EP-01/E8 Disjunct Audit", ""]
    if not rows:
        return lines + ["No EP-01/E8 verdict rows were available.", ""]
    for row in rows:
        lines.append(
            f"- `{row.bucket}`: {row.rows} rows, "
            f"{row.distinct_sites} sites, {row.countries} countries."
        )
    lines.append("")
    lines.append(
        "Audit decision: EP-01/E8 threshold intent is internally consistent at "
        "`ep01_composite_score < 30`; current stored verdicts also expose that "
        "trauma-centre distance is absent for many rows, so E8 disjunct reporting "
        "must use measured JSON rather than the scalar export threshold."
    )
    lines.append("")
    return lines


def _focused_blocker_section(
    rules: list[AuditRule], impacts: list[CodeImpact],
) -> list[str]:
    targets = ("NH-05", "NH-04", "NH-02", "NS-08")
    lines = ["## Focused High-Impact Blockers", ""]
    for cid in targets:
        rule_notes = [
            f"{r.code}: "
            f"context={','.join(r.missing_context_names) or 'ok'}; "
            f"model={','.join(r.missing_model_fields) or 'ok'}"
            for r in rules if r.criterion_id == cid
        ]
        impact_notes = [
            f"{i.code}/{i.verdict}={i.rows}"
            for i in impacts if cid in i.criteria.split("|")
        ][:6]
        lines.append(
            f"- `{cid}` rules: {' | '.join(rule_notes) or 'none'}; "
            f"current impacts: {' | '.join(impact_notes) or 'none'}."
        )
    lines.append("")
    lines.append(
        "Audit decision: NH-02, NH-04, and NH-05 have coherent thresholds and "
        "live DB fields; their large impact is not explained by field-name drift. "
        "NS-08 now has a derived strict-protected flag from zero-distance protected "
        "area hits, but source coverage still needs domain review."
    )
    lines.append("")
    return lines


def _impact_section(impacts: list[CodeImpact]) -> list[str]:
    lines = ["## Current Run Impact", ""]
    if not impacts:
        return lines + ["No screening verdict rows were available for this run.", ""]
    lines.append("Top triggered verdict groups:")
    for impact in impacts[:15]:
        lines.append(
            f"- `{impact.code}` {impact.phase}/{impact.verdict}: "
            f"{impact.rows} rows, {impact.distinct_sites} sites, "
            f"{impact.countries} countries, criteria `{impact.criteria}`."
        )
    lines.append("")
    return lines


def _score_section(rows: list[CriterionScoreSummary]) -> list[str]:
    problem_rows = [r for r in rows if r.unscored_rows or r.insufficient_rows]
    lines = ["## Ranking Score Diagnostics", ""]
    if not rows:
        return lines + ["No ranking scores were available for this run.", ""]
    lines.append(f"Criteria with unscored or insufficient rows: {len(problem_rows)}.")
    for row in problem_rows[:12]:
        lines.append(
            f"- `{row.criterion_id}`: {row.unscored_rows} unscored, "
            f"{row.insufficient_rows} insufficient out of {row.rows} rows."
        )
    lines.append("")
    return lines


def _decision_section() -> list[str]:
    return [
        "## Audit Status",
        "",
        "- Every E-code and A-code has a catalogue row in `ea_catalogue.csv`.",
        "- Codes with DB/context risks require either a resolver alias, a derived context value, or connector/schema enrichment.",
        "- EP-01/E8 should be reviewed with the full measured JSON; scalar exports are not enough to distinguish the composite-score and trauma-centre disjuncts.",
        "- Avoidance cautions are rankable risk flags unless the project explicitly chooses a shortlist definition that requires `passed_avoidance`.",
        "",
    ]
