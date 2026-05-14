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
    "NS": "ns_nuclear_safety.yaml",
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


def criterion_weight_block(crit: CriterionPreview) -> str:
    """Return criterion-level weight and norms metadata."""
    factors = crit.weight_factors or {}
    basis = crit.weight_basis_source or {}
    epri_weight = factors.get("epri")
    baseline_weight = factors.get("baseline", crit.weight_factor)
    lines = [
        f"**Criterion:** `{crit.criterion_id}` - {crit.name}",
        f"**Active weight:** `{crit.weight_factor}`",
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
) -> str:
    """Return EP-01-style details for one fail/avoidance/screen code."""
    lines = [
        f"**Code:** `{fc.code}` | **Action:** `{fc.action}`",
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
    if crit is not None:
        lines.append(f"Rubric source: `{_rubric_source(crit.criterion_id)}`")
    return "  \n".join(lines)


def criterion_info_markdown(crit: CriterionPreview) -> str:
    """Build the complete criterion info body used by all '?' popovers."""
    parts = [criterion_weight_block(crit)]
    if crit.fail_codes:
        parts.append("### Failure / Flag Rules")
        for fc in crit.fail_codes:
            parts.append(criterion_infobox(crit, fc))
    else:
        parts.append("No failure or avoidance rule is defined for this criterion.")
    if crit.notes:
        parts.append("### Notes")
        parts.append(crit.notes)
    parts.append(f"Rubric source: `{_rubric_source(crit.criterion_id)}`")
    return "\n\n".join(parts)


def criterion_info_popover(crit: CriterionPreview, *, label: str = "?") -> None:
    """Render the universal criterion norms / fail-rule popover."""
    with st.popover(label, help=f"Details for {crit.criterion_id}"):
        st.markdown(criterion_info_markdown(crit))


__all__ = [
    "criterion_infobox",
    "criterion_info_markdown",
    "criterion_info_popover",
    "criterion_weight_block",
]
