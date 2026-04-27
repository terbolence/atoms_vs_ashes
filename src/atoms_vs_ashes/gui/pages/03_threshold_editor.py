# man_hours: 2.0
"""Page 3 — Threshold editor with live rubric preview and (i) info icons.

Every input the user touches re-runs :func:`build_preview`, so the
0–10 band table, normalised weights, and modified-from-recommended
diff stay in sync. Tooltips use ``help=`` (hover) per Streamlit
convention. Exclusionary pass-marks (safety floor) are shown only for
criteria with at least one ``action: exclude`` fail condition;
ranking / avoidance rows only show score boundaries.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

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
from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.threshold_overrides import save_threshold_rows
from atoms_vs_ashes.runprofile.schema import RunProfile


def _action_kind_label(action: str) -> str:
    if action == "exclude":
        return "exclusionary"
    return "ranking-only"


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


def _norms_differences_table(preview: PreviewBundle) -> None:
    """Rows where current override ≠ recommended, with exclusionary kind."""
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
                        "kind": _action_kind_label(fc.action),
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
        "Only **exclusionary** rows (kind = exclusionary) change pass/fail "
        "or safety-floor behaviour. **ranking-only** rows adjust score bands."
    )
    st.dataframe(rows, hide_index=True, use_container_width=True)


def _threshold_input(
    crit: CriterionPreview, fc: FailConditionPreview, expert_override: bool
) -> None:
    label = _input_label(fc)
    help_text = _help_caption(fc)
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
    if cols[2].button("Save", key=f"save_{crit.criterion_id}_{fc.code}", type="primary"):
        _save_one_threshold(crit, fc, expert_override)
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


def _save_one_threshold(
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


def _criterion_card(crit: CriterionPreview, expert_override: bool) -> None:
    title = (
        f"**{crit.criterion_id}** — {crit.name}  "
        f"  weight: {crit.weight_factor} ({crit.weight_normalised:.1%})"
    )
    if crit.is_exclusionary and crit.exclusion_pass_mark is not None:
        title += f"  pass-mark (floor): {crit.exclusion_pass_mark:g}"
    with st.expander(title, expanded=False):
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
        st.success("All thresholds at recommended values (compiled audit).")
        return
    st.subheader("Modified from recommended (compiler audit)")
    st.dataframe(preview.diff_vs_recommended, hide_index=True, use_container_width=True)


def _save_all_to_profile_yaml(target: str | Path) -> None:
    """Optional: write full fail_thresholds snapshot to YAML (batch/CLI sync)."""
    profile = get_profile()
    if profile is None:
        st.error("No profile loaded.")
        return
    fts: dict[str, dict[str, Any]] = {**{k: dict(v) for k, v in get_fail_thresholds().items()}}  # type: ignore[assignment]
    expert = bool(st.session_state.get("expert_override", False))
    new_profile = profile.model_copy(
        update={"fail_thresholds": fts, "expert_override": expert}
    )
    tpath = Path(target)
    tpath.parent.mkdir(parents=True, exist_ok=True)
    tpath.write_text(
        yaml.safe_dump(new_profile.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    st.session_state["profile"] = new_profile
    st.session_state["profile_path"] = str(tpath)
    st.success(f"Wrote full profile (including thresholds) → {tpath}")


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
    profile_for_preview: RunProfile = profile.model_copy(
        update={"fail_thresholds": fts, "expert_override": expert}
    )
    try:
        preview = build_live_preview(profile_for_preview, profile.spec_dir)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Preview failed: {exc}")
        return

    with st.expander("Differences from norms (overrides vs template)", expanded=True):
        _norms_differences_table(preview)

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
    st.caption(
        "Use **Save** on a row to persist that threshold to the database. "
        "Optional: export the full run profile (including all session overrides) to YAML for CLI/batch."
    )
    ypath = st.text_input(
        "Optional — export full profile YAML",
        value=st.session_state.get("profile_path", "config/run_profiles/baseline.yaml"),
    )
    if st.button("Export profile to YAML"):
        try:
            _save_all_to_profile_yaml(ypath)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Export failed: {exc}")


render()
