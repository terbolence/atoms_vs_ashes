# man_hours: 1.75
"""Streamlit widgets for the threshold editor (norms table, criterion cards, save)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pandas as pd
import streamlit as st

from atoms_vs_ashes.criterion_spec.preview import (
    CriterionPreview,
    FailConditionPreview,
    PreviewBundle,
)
from atoms_vs_ashes.gui._state import (
    get_fail_thresholds,
    get_profile,
    reset_fail_threshold,
    update_fail_threshold,
)
from atoms_vs_ashes.gui._threshold_editor_palette import (
    AVOID_ROW_BG,
    EXCL_ROW_BG,
    NEUTRAL_ROW_BG,
    action_kind_label,
    criterion_expander_label,
    fc_accent_bar,
)
from atoms_vs_ashes.gui._threshold_editor_weight import criterion_weight_input
from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.threshold_overrides import save_threshold_rows
from atoms_vs_ashes.runprofile.schema import RunProfile


def _value_line_for_action(fc: FailConditionPreview) -> str:
    if fc.action == "exclude":
        return (
            f"**Fail value:** `{fc.recommended_value}`"
            f"{' ' + fc.units if fc.units else ''}  \n"
            "*(Exclusion: site fails this criterion if the hard E-code "
            "triggers or the 0–10 band score is strictly below the pass mark.)*"
        )
    return (
        f"**Score boundary (mark 5):** `{fc.recommended_value}`"
        f"{' ' + fc.units if fc.units else ''}  \n"
        "*(Ranking / avoidance: this is not a pass–fail gate; it sets where "
        "the rubric maps to a score of 5 — the site is not globally excluded "
        "for this alone.)*"
    )


def _help_caption(fc: FailConditionPreview) -> str:
    lines = [
        _value_line_for_action(fc),
        f"Expression: `{fc.condition_expr}`  \n**Action:** `{fc.action}`",
    ]
    if fc.recommended_rationale:
        lines.append(str(fc.recommended_rationale))
    if fc.recommended_sources:
        lines.append(
            "Sources: " + ", ".join(f"`{s}`" for s in fc.recommended_sources)
        )
    if fc.bounds_min is not None or fc.bounds_max is not None:
        lines.append(
            f"Bounds: [{fc.bounds_min if fc.bounds_min is not None else '-∞'}"
            f", {fc.bounds_max if fc.bounds_max is not None else '+∞'}]"
        )
    return "  \n".join(lines)


def _input_label(fc: FailConditionPreview) -> str:
    base = f"{fc.code} — {fc.label or fc.metric or 'threshold'}"
    if fc.units:
        return f"{base} ({fc.units})"
    return base


def _style_norms_table(df: pd.DataFrame) -> Any:
    def row_colors(row: pd.Series) -> list[str]:
        k = row["kind"]
        if k == "exclusionary":
            bg = f"background-color: {EXCL_ROW_BG}"
        elif k == "avoidance":
            bg = f"background-color: {AVOID_ROW_BG}"
        elif k == "ranking-only":
            bg = f"background-color: {NEUTRAL_ROW_BG}"
        else:
            bg = ""
        return [bg] * len(row)

    return df.style.apply(row_colors, axis=1)  # type: ignore[union-attr]


def norms_differences_table(preview: PreviewBundle) -> None:
    """Rows where current override ≠ recommended, with importance kind."""
    fts = get_fail_thresholds()
    rows: list[dict[str, Any]] = []
    for crit in preview.criteria:
        for fc in crit.fail_codes:
            if not fc.user_editable:
                continue
            rec = fc.recommended_value
            cur = fts.get(crit.criterion_id, {}).get(fc.code, rec)
            if cur is None and rec is None:
                continue
            if cur != rec:
                rows.append(
                    {
                        "criterion": crit.criterion_id,
                        "code": fc.code,
                        "kind": action_kind_label(fc.action),
                        "current": cur,
                        "recommended": rec,
                        "units": fc.units or "",
                    }
                )
    if not rows:
        st.success("All user-editable thresholds match recommended / template values.")
        return
    st.subheader("Differences from norms (recommended / template)")
    st.caption(
        "**exclusionary** rows affect pass/fail and safety-floor behaviour. "
        "**avoidance** rows set soft penalties / screening. **ranking-only** "
        "rows adjust score bands."
    )
    df = pd.DataFrame(rows)
    st.dataframe(_style_norms_table(df), hide_index=True, use_container_width=True)


def threshold_input(
    crit: CriterionPreview, fc: FailConditionPreview, expert_override: bool,
) -> None:
    label = _input_label(fc)
    help_text = _help_caption(fc)
    accent = fc_accent_bar(fc)

    def _inputs_row() -> None:
        cols = st.columns([3, 1, 1])
        current = fc.value if fc.value is not None else fc.recommended_value
        key_base = f"{crit.criterion_id}_{fc.code}"
        if isinstance(current, (int, float)):
            new_val = cols[0].number_input(
                label,
                value=float(current),
                min_value=(
                    float(fc.bounds_min)
                    if fc.bounds_min is not None and not expert_override
                    else None
                ),
                max_value=(
                    float(fc.bounds_max)
                    if fc.bounds_max is not None and not expert_override
                    else None
                ),
                help=help_text,
                key=key_base,
            )
        else:
            new_val = cols[0].text_input(
                label,
                value=str(current) if current is not None else "",
                help=help_text,
                key=key_base,
            )
        if cols[1].button("Reset", key=f"reset_{crit.criterion_id}_{fc.code}"):
            reset_fail_threshold(crit.criterion_id, fc.code)
            st.rerun()
        if cols[2].button(
            "Save", key=f"save_{crit.criterion_id}_{fc.code}", type="primary"
        ):
            save_one_threshold(crit, fc, expert_override)
        if new_val != current:
            update_fail_threshold(crit.criterion_id, fc.code, new_val)
        if fc.modified_from_recommended:
            pct = (
                f"{fc.deviation_pct:+.1f}%"
                if fc.deviation_pct is not None
                else ""
            )
            st.caption(
                f":violet[modified from recommended]  •  Δ {pct}"
                if pct
                else ":violet[modified from recommended]"
            )
        if fc.out_of_bounds:
            st.warning(
                "Value outside template bounds — enable `expert_override` "
                "in the RunProfile or reset to recommended."
            )

    if accent:
        bar, main = st.columns([0.022, 0.978])
        with bar:
            st.markdown(
                "<div style='min-height:3.25rem;display:flex;align-items:stretch;'>"
                f"<div style='flex:1;background:{accent};border-radius:4px;'>"
                "</div></div>",
                unsafe_allow_html=True,
            )
        with main:
            _inputs_row()
    else:
        _inputs_row()


def save_one_threshold(
    crit: CriterionPreview, fc: FailConditionPreview, expert_override: bool,
) -> None:
    """Validate, persist to DB, sync profile fail_thresholds in session."""
    if not fc.user_editable:
        st.error("This code is not user-editable.")
        return
    if not expert_override and fc.out_of_bounds:
        st.error("Value out of bounds — enable expert_override or fix the value.")
        return
    profile = get_profile()
    if profile is None:
        st.error("No profile loaded.")
        return
    fts = get_fail_thresholds()
    val = fts.get(crit.criterion_id, {}).get(fc.code, fc.recommended_value)
    try:
        with session_scope() as session:
            save_threshold_rows(
                session,
                [(crit.criterion_id, fc.code, val, None)],
            )
    except Exception as exc:  # noqa: BLE001
        st.error(f"Save failed: {exc}")
        return
    new_fts = deepcopy(fts)
    new_fts.setdefault(crit.criterion_id, {})[fc.code] = val
    st.session_state["fail_thresholds"] = new_fts
    st.session_state["profile"] = profile.model_copy(
        update={"fail_thresholds": deepcopy(new_fts)}
    )
    st.success(f"Saved {crit.criterion_id} / {fc.code} to database.")
    st.rerun()


def criterion_card(crit: CriterionPreview, expert_override: bool) -> None:
    with st.expander(criterion_expander_label(crit), expanded=False):
        criterion_weight_input(crit)
        st.divider()
        editable = [fc for fc in crit.fail_codes if fc.user_editable]
        if not editable:
            st.caption("No user-editable fail-thresholds for this criterion.")
        for fc in editable:
            threshold_input(crit, fc, expert_override)
        if crit.bands:
            st.markdown("**Scoring bands**")
            st.dataframe(
                [
                    {
                        "score": f"{b.score_range[0]:g}–{b.score_range[1]:g}",
                        "descriptor": b.descriptor,
                        "rule": b.condition_expr,
                    }
                    for b in crit.bands
                ],
                hide_index=True,
                use_container_width=True,
            )


def diff_panel(preview: PreviewBundle) -> None:
    if not preview.diff_vs_recommended:
        st.success("All thresholds at recommended values (compiled audit).")
        return
    st.subheader("Modified from recommended (compiler audit)")
    st.dataframe(preview.diff_vs_recommended, hide_index=True, use_container_width=True)


__all__ = [
    "criterion_card",
    "diff_panel",
    "norms_differences_table",
    "threshold_input",
]
