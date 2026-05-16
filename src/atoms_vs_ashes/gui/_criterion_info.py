# man_hours: 1.2
"""Shared criterion norms / fail-rule popover content."""

from __future__ import annotations

import streamlit as st

from atoms_vs_ashes.criterion_spec.preview import (
    CriterionPreview,
    FailConditionPreview,
)

_RUBRIC_FILES = {
    "BF": "nh_natural_hazards.yaml",
    "NH": "nh_natural_hazards.yaml",
    "HI": "hi_human_induced.yaml",
    "NS": "ns_non_safety.yaml",
    "RI": "ri_radiological.yaml",
    "EP": "ep_emergency_planning.yaml",
}


def _rubric_source(criterion_id: str) -> str:
    family = criterion_id.split("-", 1)[0].upper()
    name = _RUBRIC_FILES.get(family, f"{family.lower()}_*.yaml")
    return f"config/scoring_rubrics/{name}"


def _value_label(fc: FailConditionPreview) -> str:
    value = fc.recommended_value
    if value is None:
        value = fc.value
    if value is None:
        return "`fixed expression`"
    units = f" {fc.units}" if fc.units else ""
    return f"`{value}`{units}"


def _value_line_for_action(fc: FailConditionPreview) -> str:
    if fc.action == "exclude":
        return (
            f"**Fail value:** {_value_label(fc)}  \n"
            "*(Exclusion: site fails this criterion if the hard E-code "
            "triggers or the 0-10 band score is strictly below the pass mark.)*"
        )
    return (
        f"**Score boundary (mark 5):** {_value_label(fc)}  \n"
        "*(Ranking / avoidance: this is not a pass-fail gate; it sets where "
        "the rubric maps to a score of 5. The site is not globally excluded "
        "for this alone.)*"
    )


def _action_meaning(action: str) -> str:
    meanings = {
        "exclude": (
            "Hard exclusion gate. A matching E-code removes the site from the "
            "eligible pool, independent of ranking weight."
        ),
        "avoidance_penalty": (
            "Avoidance-phase screen. It flags a material siting concern and "
            "can apply a soft penalty, but does not by itself globally exclude "
            "the site."
        ),
        "screen_flag": (
            "Basic screening flag. It records a gate or caution used before "
            "detailed ranking."
        ),
        "review_flag": (
            "Review flag. It calls for expert follow-up where the automated "
            "criterion evidence is not sufficient for a simple pass/fail rule."
        ),
    }
    return meanings.get(action, "Criterion rule used by the compiled scorer.")


def _criterion_role(crit: CriterionPreview) -> str:
    if crit.is_exclusionary:
        return "exclusionary gate"
    if "avoidance" in crit.phases:
        return "avoidance / ranking"
    if "basic_filter" in crit.phases:
        return "basic filter"
    return "ranking / screening"


def criterion_weight_block(crit: CriterionPreview) -> str:
    """Return criterion-level weight and norms metadata."""
    factors = crit.weight_factors or {}
    basis = crit.weight_basis_source or {}
    epri_weight = factors.get("epri")
    baseline_weight = factors.get("baseline", crit.weight_factor)
    lines = [
        f"**Criterion:** `{crit.criterion_id}` - {crit.name}",
        f"**Role:** `{_criterion_role(crit)}`",
        f"**Phases:** `{', '.join(crit.phases)}`",
        f"**Active weight:** `{crit.weight_factor}`",
        f"**Scoring share:** `{crit.weight_normalised:.2%}`",
        f"**Baseline weight:** `{baseline_weight}`",
        f"**EPRI weight:** `{epri_weight if epri_weight is not None else 'n/a'}`",
    ]
    if basis.get("epri"):
        lines.append(f"**IAEA / EPRI basis:** {basis['epri']}")
    elif basis:
        lines.append(
            "**Weight basis:** "
            + "; ".join(f"{k}: {v}" for k, v in sorted(basis.items()))
        )
    return "  \n".join(lines)


def criterion_infobox(
    crit: CriterionPreview | None,
    fc: FailConditionPreview,
    *,
    include_rubric_source: bool = False,
) -> str:
    """Return EP-01-style details for one fail/avoidance/screen code."""
    lines = [
        f"**Code:** `{fc.code}` | **Action:** `{fc.action}`",
        f"**Action meaning:** {_action_meaning(fc.action)}",
        f"**Pass mark:** `{fc.pass_mark if fc.pass_mark is not None else 'n/a'}`",
        _value_line_for_action(fc),
        f"**Expression:** `{fc.condition_expr}`",
    ]
    if fc.descriptor:
        lines.append(f"**Descriptor:** {fc.descriptor}")
    if fc.recommended_rationale:
        lines.append(str(fc.recommended_rationale))
    if fc.recommended_sources:
        lines.append(
            "Sources: " + ", ".join(f"`{s}`" for s in fc.recommended_sources)
        )
    if fc.bounds_min is not None or fc.bounds_max is not None:
        lines.append(
            f"Bounds: [{fc.bounds_min if fc.bounds_min is not None else '-inf'}, "
            f"{fc.bounds_max if fc.bounds_max is not None else '+inf'}]"
        )
    lines.append(f"User-tunable: `{'yes' if fc.user_editable else 'no'}`")
    if include_rubric_source and crit is not None:
        lines.append(f"Rubric source: `{_rubric_source(crit.criterion_id)}`")
    return "  \n".join(lines)


def criterion_input_info_markdown(
    crit: CriterionPreview,
    fc: FailConditionPreview | None = None,
) -> str:
    """Build one reconciled info body for an in-expander criterion control."""
    parts = [criterion_weight_block(crit)]
    if fc is not None:
        parts.append("### Selected Rule")
        parts.append(criterion_infobox(crit, fc))
        other_rules = [
            other
            for other in crit.fail_codes
            if other.code != fc.code or other.action != fc.action
        ]
        if other_rules:
            parts.append("### Other Failure / Flag Rules")
            for other in other_rules:
                parts.append(criterion_infobox(crit, other))
    elif crit.fail_codes:
        parts.append("### Failure / Flag Rules")
        for fail_code in crit.fail_codes:
            parts.append(criterion_infobox(crit, fail_code))
    else:
        parts.append("No failure, avoidance, or review rule is defined for this criterion.")
    if crit.primary_metric:
        parts.append(f"**Primary metric:** `{crit.primary_metric}`")
    if crit.band_kind:
        parts.append(f"**Band model:** `{crit.band_kind}`")
    if crit.notes:
        parts.append("### Notes")
        parts.append(crit.notes)
    parts.append(f"Rubric source: `{_rubric_source(crit.criterion_id)}`")
    return "\n\n".join(parts)


def criterion_info_markdown(crit: CriterionPreview) -> str:
    """Build the complete criterion info body used by all '?' popovers."""
    return criterion_input_info_markdown(crit)


def criterion_info_popover(
    crit: CriterionPreview,
    *,
    label: str = "?",
    fc: FailConditionPreview | None = None,
) -> None:
    """Render the universal criterion norms / fail-rule popover."""
    with st.popover(label, help=f"Details for {crit.criterion_id}"):
        st.markdown(criterion_input_info_markdown(crit, fc))


__all__ = [
    "criterion_infobox",
    "criterion_input_info_markdown",
    "criterion_info_markdown",
    "criterion_info_popover",
    "criterion_weight_block",
]
