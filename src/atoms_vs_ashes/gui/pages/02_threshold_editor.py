# man_hours: 2.0
"""Page 2 — Threshold editor with live rubric preview and (i) info icons.

Every input the user touches re-runs :func:`build_preview`, so the
0–10 band table, normalised weights, and modified-from-recommended
diff stay in sync without a page refresh. Invalid edits surface as
warnings under the row instead of crashing the page (the preview
service catches ``ValueError`` and reports the message).
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import streamlit as st
import yaml

from atoms_vs_ashes.criterion_spec.preview import (
    CriterionPreview,
    FailConditionPreview,
    PreviewBundle,
)
from atoms_vs_ashes.gui._data import build_live_preview
from atoms_vs_ashes.gui._state import (
    get_fail_thresholds,
    get_profile,
    reset_fail_threshold,
    update_fail_threshold,
)


def _info_caption(fc: FailConditionPreview) -> str:
    bits = [f"**Recommended:** `{fc.recommended_value}`"]
    if fc.units:
        bits[0] += f" {fc.units}"
    if fc.recommended_rationale:
        bits.append(fc.recommended_rationale)
    if fc.recommended_sources:
        bits.append("Sources: " + ", ".join(f"`{s}`" for s in fc.recommended_sources))
    if fc.bounds_min is not None or fc.bounds_max is not None:
        bits.append(
            f"Bounds: [{fc.bounds_min if fc.bounds_min is not None else '-∞'}"
            f", {fc.bounds_max if fc.bounds_max is not None else '+∞'}]"
        )
    return "  \n".join(bits)


def _threshold_input(
    crit: CriterionPreview, fc: FailConditionPreview, expert_override: bool
) -> None:
    label = f"{fc.code} — {fc.label or fc.metric or 'threshold'}"
    cols = st.columns([3, 1, 1])
    current = fc.value if fc.value is not None else fc.recommended_value
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
            help=f"`{fc.condition_expr}`  •  action: **{fc.action}**",
            key=f"{crit.criterion_id}_{fc.code}",
        )
    else:
        new_val = cols[0].text_input(
            label,
            value=str(current) if current is not None else "",
            help=f"`{fc.condition_expr}` • action: **{fc.action}**",
            key=f"{crit.criterion_id}_{fc.code}",
        )
    if cols[1].button("Reset", key=f"reset_{crit.criterion_id}_{fc.code}"):
        reset_fail_threshold(crit.criterion_id, fc.code)
        st.rerun()
    with cols[2].popover("ⓘ"):
        st.markdown(_info_caption(fc))
    if new_val != current:
        update_fail_threshold(crit.criterion_id, fc.code, new_val)
    if fc.modified_from_recommended:
        st.caption(
            f":orange[modified] from recommended  •  Δ "
            f"{fc.deviation_pct:+.1f}%" if fc.deviation_pct is not None else ""
        )
    if fc.out_of_bounds:
        st.warning(
            "Value outside template bounds — enable `expert_override` "
            "in the RunProfile or reset to recommended."
        )


def _criterion_card(crit: CriterionPreview, expert_override: bool) -> None:
    with st.expander(
        f"**{crit.criterion_id}** — {crit.name}  "
        f"  weight: {crit.weight_factor} ({crit.weight_normalised:.1%}) "
        f"  pass-mark: {crit.pass_mark}",
        expanded=False,
    ):
        editable = [fc for fc in crit.fail_codes if fc.user_editable]
        if not editable:
            st.caption("No user-editable fail-thresholds for this criterion.")
        for fc in editable:
            _threshold_input(crit, fc, expert_override)
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


def _diff_panel(preview: PreviewBundle) -> None:
    if not preview.diff_vs_recommended:
        st.success("All thresholds at recommended values.")
        return
    st.subheader("Modified from recommended")
    st.dataframe(preview.diff_vs_recommended, hide_index=True, use_container_width=True)


def _save_overrides_to_profile(profile_path: str | Path) -> None:
    """Write the current `fail_thresholds` + `expert_override` back to YAML."""
    profile = get_profile()
    if profile is None:
        st.error("No profile loaded.")
        return
    fts = deepcopy(get_fail_thresholds())
    expert = bool(st.session_state.get("expert_override", False))
    new_profile = profile.model_copy(
        update={"fail_thresholds": fts, "expert_override": expert}
    )
    target = Path(profile_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        yaml.safe_dump(new_profile.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    st.session_state["profile"] = new_profile
    st.session_state["profile_path"] = str(target)
    st.success(f"Saved overrides → {target}")


def render() -> None:
    st.title("Threshold editor")
    profile = get_profile()
    if profile is None:
        st.info("Load a Run Profile from the sidebar first.")
        return

    expert = st.toggle(
        "expert_override",
        value=bool(st.session_state.get("expert_override", profile.expert_override)),
        help="Bypass per-threshold bounds. Use sparingly — flagged in audit MDs.",
    )
    st.session_state["expert_override"] = expert

    fts = get_fail_thresholds()
    profile_for_preview = profile.model_copy(
        update={"fail_thresholds": fts, "expert_override": expert}
    )
    try:
        preview = build_live_preview(profile_for_preview, profile.spec_dir)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Preview failed: {exc}")
        return

    cols = st.columns([2, 1])
    cols[0].caption(f"Spec dir: `{preview.spec_dir}`")
    cols[1].caption(f"Compiled SHA: `{preview.compiled_sha256[:12]}…`")
    if preview.warnings:
        for w in preview.warnings:
            st.warning(w)

    st.subheader("Criteria")
    for crit in preview.criteria:
        _criterion_card(crit, expert)

    st.divider()
    _diff_panel(preview)

    st.divider()
    target = st.text_input(
        "Save overrides to",
        value=st.session_state.get("profile_path", "config/run_profiles/baseline.yaml"),
    )
    if st.button("Save overrides", type="primary"):
        try:
            _save_overrides_to_profile(target)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Save failed: {exc}")


render()
