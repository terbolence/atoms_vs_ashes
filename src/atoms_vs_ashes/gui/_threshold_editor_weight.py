# man_hours: 0.75
"""Per-criterion weight (1-10) input + section-level Save/Discard controls.

The Site Selection Criteria page renders one card per criterion. Inside
each card we expose a numeric weight (1..10) input that writes through
:func:`atoms_vs_ashes.gui._state.set_weight_override` into the live
``weight_overrides_draft`` dict held in ``st.session_state``. The
threshold-editor view rebuilds the live preview bundle off this draft
on every rerun, so the **relative share** (``weight_normalised``)
shown next to every criterion recomputes immediately when one weight
moves.

Saving is intentionally section-level — every weight participates in
the normalisation, so a single ``Save weights`` click commits the
whole draft to the active :class:`RunProfile` row in Postgres via
:func:`commit_weight_overrides_draft`. ``Discard weight changes``
rolls the draft back to the values currently persisted in the DB.
"""

from __future__ import annotations

import streamlit as st

from atoms_vs_ashes.criterion_spec.preview import CriterionPreview
from atoms_vs_ashes.gui._state import (
    commit_weight_overrides_draft,
    discard_weight_overrides_draft,
    get_weight_overrides_draft,
    has_weight_overrides_changes,
    reset_weight_override,
    set_weight_override,
)


_WEIGHT_HELP = (
    "Importance weight (1–10). The percentage shown next to each "
    "criterion is its weight divided by the sum of all criterion "
    "weights, so editing this value re-balances the rubric's "
    "relative shares immediately. **Reset to spec** drops the override "
    "for this criterion; **Save weights** persists the active profile."
)


def _rev_key(criterion_id: str) -> str:
    return f"weight_rev_{criterion_id}"


def _input_key(criterion_id: str) -> str:
    rev = st.session_state.get(_rev_key(criterion_id), 0)
    return f"weight_input_{criterion_id}_{rev}"


def criterion_weight_input(crit: CriterionPreview) -> None:
    """Render the weight ``number_input`` + per-criterion ``Reset`` button."""
    cid = crit.criterion_id
    overrides = get_weight_overrides_draft()
    has_override = cid in overrides
    current = int(overrides.get(cid, crit.weight_factor))
    cols = st.columns([3, 1])
    new_val = cols[0].number_input(
        "Weight (1–10)",
        min_value=1,
        max_value=10,
        step=1,
        value=current,
        help=_WEIGHT_HELP,
        key=_input_key(cid),
    )
    if int(new_val) != int(current):
        set_weight_override(cid, int(new_val))
        st.rerun()
    if cols[1].button(
        "Reset to spec",
        key=f"weight_reset_{cid}",
        disabled=not has_override,
        help="Drop this criterion's weight override and use the spec value.",
    ):
        reset_weight_override(cid)
        st.session_state[_rev_key(cid)] = (
            int(st.session_state.get(_rev_key(cid), 0)) + 1
        )
        st.rerun()
    note = (
        f"effective weight `{int(new_val)}` "
        f"&nbsp;•&nbsp; relative share `{crit.weight_normalised:.2%}`"
    )
    if has_override:
        note += " &nbsp;•&nbsp; :violet[modified from spec]"
    st.caption(note, unsafe_allow_html=True)


def weight_section_controls() -> None:
    """Render the section-level Save / Discard row for the weight draft."""
    dirty = has_weight_overrides_changes()
    cols = st.columns([2, 1, 1])
    if dirty:
        cols[0].markdown(
            ":violet[**Unsaved weight changes** — click *Save weights* to "
            "persist them to the active run profile.]"
        )
    else:
        cols[0].caption(
            "All weights are in sync with the active run profile."
        )
    if cols[1].button(
        "Save weights",
        type="primary",
        disabled=not dirty,
        key="weight_section_save",
    ):
        try:
            commit_weight_overrides_draft(
                updated_by="gui:site_selection_criteria"
            )
        except Exception as exc:  # noqa: BLE001
            st.error(f"Save failed: {exc}")
        else:
            st.success("Saved scoring.weight_overrides to active profile.")
            st.rerun()
    if cols[2].button(
        "Discard weight changes",
        disabled=not dirty,
        key="weight_section_discard",
    ):
        discard_weight_overrides_draft()
        st.rerun()


__all__ = ["criterion_weight_input", "weight_section_controls"]
