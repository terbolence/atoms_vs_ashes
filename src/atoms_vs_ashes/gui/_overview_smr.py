# man_hours: 1.0
"""Inline SMR sub-editor for the Sites & SMR Setup screen.

Shows only the four required ``smr_designs`` fields (``smr_key``,
``name``, ``capacity_mwe``, ``land_requirement_ha``) for whichever SMR
keys are in the active scope. Empty SMR scope means "all designs", matching
the scoring engine. The full catalogue editor (with optional
fields like EPZ radius, cooling type, regulatory status) remains on
page 01 — this widget is intentionally minimal.

The editor is a fixed-row ``st.data_editor``; users cannot add or
delete designs from here. Saving writes back to ``smr_designs`` and
clears :func:`atoms_vs_ashes.gui._data.list_smrs` so dependent screens
pick up the new specs on the next interaction.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from sqlalchemy import select

from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models import SmrDesign
from atoms_vs_ashes.gui import _data as gui_data


_REQUIRED_COLS = ["smr_key", "name", "capacity_mwe", "land_requirement_ha"]


def render_smr_subeditor(selected_keys: list[str]) -> pd.DataFrame | None:
    """Render the mini editor; return the edited DataFrame (or ``None``)."""
    with session_scope() as session:
        stmt = select(
            SmrDesign.smr_key,
            SmrDesign.name,
            SmrDesign.capacity_mwe,
            SmrDesign.land_requirement_ha,
        ).order_by(SmrDesign.smr_key)
        if selected_keys:
            stmt = stmt.where(SmrDesign.smr_key.in_(selected_keys))
        rows = session.execute(stmt).all()

    if not selected_keys:
        st.caption(
            "No SMR technology filter is active, so all designs are shown."
        )

    if not rows:
        st.warning(
            "No matching ``smr_designs`` rows for the selected keys. "
            "Add them on the SMR Catalogue page first."
        )
        return None

    df = pd.DataFrame(rows, columns=_REQUIRED_COLS)
    edited = st.data_editor(
        df,
        num_rows="fixed",
        use_container_width=True,
        column_config={
            "smr_key": st.column_config.TextColumn(
                "smr_key",
                disabled=True,
                help=(
                    "Stable identifier. Edit the key (and create new "
                    "designs) on the SMR Catalogue page."
                ),
            ),
            "name": st.column_config.TextColumn(
                "name",
                required=True,
                max_chars=120,
                help="Display name shown across the GUI.",
            ),
            "capacity_mwe": st.column_config.NumberColumn(
                "capacity (MWe)",
                required=True,
                min_value=0.01,
                format="%.2f",
                help=(
                    "Net electrical output per module. Drives capacity-"
                    "screening and grid-headroom checks."
                ),
            ),
            "land_requirement_ha": st.column_config.NumberColumn(
                "land (ha)",
                required=True,
                min_value=0.01,
                format="%.2f",
                help=(
                    "Total site footprint required by the design. Drives "
                    "BF-02 land-availability screening."
                ),
            ),
        },
        key="overview_smr_subeditor",
    )
    return edited


def _validate_row(r: dict[str, object]) -> str | None:
    key = str(r.get("smr_key") or "").strip()
    if not key:
        return "smr_key is required"
    name = str(r.get("name") or "").strip()
    if not name:
        return f"{key}: name is required"
    try:
        c = float(r.get("capacity_mwe"))
    except (TypeError, ValueError):
        return f"{key}: capacity_mwe must be a number"
    if c <= 0:
        return f"{key}: capacity_mwe must be > 0"
    try:
        h = float(r.get("land_requirement_ha"))
    except (TypeError, ValueError):
        return f"{key}: land_requirement_ha must be a number"
    if h <= 0:
        return f"{key}: land_requirement_ha must be > 0"
    return None


def save_smr_subeditor(edited: pd.DataFrame) -> bool:
    """Validate and persist the edits. Returns ``True`` on success."""
    rows = edited.to_dict(orient="records")
    errs: list[str] = []
    for r in rows:
        msg = _validate_row(r)
        if msg:
            errs.append(msg)
    if errs:
        st.error("Validation: " + "; ".join(errs[:6]))
        return False
    with session_scope() as session:
        for r in rows:
            key = str(r["smr_key"]).strip()
            row = session.get(SmrDesign, key)
            if row is None:
                continue
            row.name = str(r["name"]).strip()
            row.capacity_mwe = float(r["capacity_mwe"])
            row.land_requirement_ha = float(r["land_requirement_ha"])
    gui_data.list_smrs.clear()
    return True


__all__ = ["render_smr_subeditor", "save_smr_subeditor"]
