# man_hours: 1.0
"""Per-rule audit status rows for the suitable-sites scoring audit."""

from __future__ import annotations

from dataclasses import dataclass

from atoms_vs_ashes.scoring_audit.catalog import AuditRule
from atoms_vs_ashes.scoring_audit.db import CodeImpact


@dataclass(frozen=True)
class AuditStatusRow:
    """Human-reviewable status for one E/A rule or synthetic safety floor."""

    criterion_id: str
    code: str
    phase: str
    audit_item_type: str
    threshold_intent: str
    band_conversion: str
    data_application: str
    suitability_role: str
    current_impact_rows: int
    current_fail_or_caution_rows: int
    decision: str
    evidence: str


def build_audit_status_rows(
    rules: list[AuditRule], impacts: list[CodeImpact],
) -> list[AuditStatusRow]:
    """Return explicit audit status rows for all E/A codes and floors."""
    impact_map = _impact_map(impacts)
    rows: list[AuditStatusRow] = []
    for rule in rules:
        rows.append(_rule_status(rule, impact_map))
        if rule.action == "exclude" and rule.pass_mark is not None:
            rows.append(_floor_status(rule, impact_map))
    return rows


def _impact_map(impacts: list[CodeImpact]) -> dict[tuple[str, str], list[CodeImpact]]:
    grouped: dict[tuple[str, str], list[CodeImpact]] = {}
    for impact in impacts:
        grouped.setdefault((impact.code, impact.phase), []).append(impact)
    return grouped


def _rule_status(
    rule: AuditRule, impact_map: dict[tuple[str, str], list[CodeImpact]],
) -> AuditStatusRow:
    phase = "exclusionary" if rule.action == "exclude" else "avoidance"
    impacts = impact_map.get((rule.code, phase), [])
    return AuditStatusRow(
        criterion_id=rule.criterion_id,
        code=rule.code,
        phase=phase,
        audit_item_type="hard_rule" if rule.action == "exclude" else "avoidance_rule",
        threshold_intent=_threshold_intent(rule),
        band_conversion=_band_conversion(rule),
        data_application=_data_application(rule),
        suitability_role=_suitability_role(rule),
        current_impact_rows=sum(i.rows for i in impacts),
        current_fail_or_caution_rows=sum(
            i.rows for i in impacts if i.verdict in {"fail", "caution"}
        ),
        decision=_decision(rule),
        evidence=_evidence(rule, impacts),
    )


def _floor_status(
    rule: AuditRule, impact_map: dict[tuple[str, str], list[CodeImpact]],
) -> AuditStatusRow:
    code = f"{rule.code}:floor"
    impacts = impact_map.get((code, "exclusionary"), [])
    return AuditStatusRow(
        criterion_id=rule.criterion_id,
        code=code,
        phase="exclusionary",
        audit_item_type="safety_floor",
        threshold_intent=f"Safety-floor backstop at pass_mark={rule.pass_mark}.",
        band_conversion="review: floor can hard-exclude rankable low-score sites",
        data_application=_data_application(rule),
        suitability_role="hard exclusion via score floor",
        current_impact_rows=sum(i.rows for i in impacts),
        current_fail_or_caution_rows=sum(i.rows for i in impacts if i.verdict == "fail"),
        decision="review_floor_policy",
        evidence=_evidence(rule, impacts),
    )


def _threshold_intent(rule: AuditRule) -> str:
    if rule.action == "avoidance_penalty":
        return "avoidance threshold: risk flag and ranking pressure, not intrinsic hard exclusion"
    if rule.threshold_default is not None:
        return f"hard threshold with metadata default {rule.threshold_op} {rule.threshold_default} {rule.threshold_units or ''}".strip()
    return "hard threshold from rubric descriptor; domain source review required"


def _band_conversion(rule: AuditRule) -> str:
    if rule.pass_mark is not None:
        return f"pass_mark={rule.pass_mark}; first-match bands must align with hard rule"
    return "no pass_mark; direct fail_condition only"


def _data_application(rule: AuditRule) -> str:
    issues = list(rule.missing_context_names) + list(rule.missing_model_fields)
    return "ok" if not issues else "review: " + "; ".join(issues)


def _suitability_role(rule: AuditRule) -> str:
    if rule.action == "exclude":
        return "hard unsuitable when fail is triggered"
    return "avoidance caution; should not be labelled as hard unsuitable"


def _decision(rule: AuditRule) -> str:
    if rule.missing_context_names or rule.missing_model_fields:
        return "fix_or_enrich_data_application"
    if rule.action == "avoidance_penalty":
        return "valid_as_risk_flag"
    return "validated_or_domain_review_only"


def _evidence(rule: AuditRule, impacts: list[CodeImpact]) -> str:
    impact_text = ", ".join(f"{i.verdict}:{i.rows}" for i in impacts) or "no rows"
    return f"{rule.condition_expr}; impacts={impact_text}"
