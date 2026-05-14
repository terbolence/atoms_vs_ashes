# man_hours: 2.0
"""Streamlit widgets for the threshold editor (norms table, criterion cards, save)."""

from __future__ import annotations

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
    update_fail_threshold,
)
from atoms_vs_ashes.gui._threshold_editor_persistence import (
    reset_one_threshold,
    save_one_threshold,
)
from atoms_vs_ashes.gui._threshold_editor_palette import (
    AVOID_ROW_BG,
    DARK_AVOID_ROW_BG,
    DARK_EXCL_ROW_BG,
    DARK_NEUTRAL_ROW_BG,
    DARK_ROW_TEXT,
    EXCL_ROW_BG,
    LIGHT_ROW_TEXT,
    NEUTRAL_ROW_BG,
    action_kind_label,
    fc_accent_bar,
)
from atoms_vs_ashes.gui._criterion_info import (
    criterion_infobox,
    criterion_info_popover,
)
from atoms_vs_ashes.gui._threshold_editor_criteria_header import criterion_summary_row
from atoms_vs_ashes.gui._threshold_editor_weight import criterion_weight_input


def _help_caption(fc: FailConditionPreview) -> str:
    # Number inputs can only show a tooltip string, not a popover, so reuse
    # the same rule-level content without the criterion weight header.
    return criterion_infobox(None, fc)


def _input_label(fc: FailConditionPreview) -> str:
    base = f"{fc.code} — {fc.label or fc.metric or 'threshold'}"
    if fc.units:
        return f"{base} ({fc.units})"
    return base


def _style_norms_table(df: pd.DataFrame) -> Any:
    dark = st.get_option("theme.base") == "dark"
    backgrounds = {
        "exclusionary": DARK_EXCL_ROW_BG if dark else EXCL_ROW_BG,
        "avoidance": DARK_AVOID_ROW_BG if dark else AVOID_ROW_BG,
        "ranking-only": DARK_NEUTRAL_ROW_BG if dark else NEUTRAL_ROW_BG,
    }
    text = DARK_ROW_TEXT if dark else LIGHT_ROW_TEXT

    def row_colors(row: pd.Series) -> list[str]:
        bg = backgrounds.get(row["kind"])
        style = f"background-color: {bg}; color: {text};" if bg else f"color: {text};"
        return [style] * len(row)

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
        dirty_key = f"threshold_dirty_{crit.criterion_id}_{fc.code}"
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
            reset_one_threshold(crit, fc)
        dirty = bool(st.session_state.get(dirty_key, False))
        if dirty:
            if cols[2].button(
                "Save", key=f"save_{crit.criterion_id}_{fc.code}", type="primary"
            ):
                save_one_threshold(crit, fc, expert_override)
        else:
            cols[2].success("Saved")
        if new_val != current:
            update_fail_threshold(crit.criterion_id, fc.code, new_val)
            st.session_state[dirty_key] = True
            st.rerun()
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


def criterion_card(crit: CriterionPreview, expert_override: bool) -> None:
    with st.container(border=True):
        criterion_summary_row(crit)
        criterion_info_popover(crit)
        with st.expander(f"{crit.criterion_id} details", expanded=False):
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


__all__ = [
    "criterion_card",
    "criterion_infobox",
    "criterion_info_popover",
    "norms_differences_table",
    "threshold_input",
]
