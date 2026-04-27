# man_hours: 2.0
"""Page 1 — SMR design catalogue (DB source-of-truth for specs)."""

from __future__ import annotations

import uuid

import pandas as pd
import streamlit as st
from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models import SmrDesign
from atoms_vs_ashes.gui import _data as gui_data
from atoms_vs_ashes.gui._state import get_profile


def _load_df(
    session: Session, *, smr_keys: list[str] | None = None
) -> pd.DataFrame:
    stmt = select(
        SmrDesign.smr_key,
        SmrDesign.name,
        SmrDesign.capacity_mwe,
        SmrDesign.land_requirement_ha,
        SmrDesign.thermal_output_mwt,
        SmrDesign.epz_radius_km,
        SmrDesign.module_weight_t,
        SmrDesign.cooling_type,
        SmrDesign.design_life_yr,
        SmrDesign.regulatory_status,
        SmrDesign.exclusion_zone_radius_m,
        SmrDesign.cooling_water_demand_m3_per_h,
        SmrDesign.notes,
    ).order_by(SmrDesign.smr_key)
    if smr_keys:
        stmt = stmt.where(SmrDesign.smr_key.in_(smr_keys))
    rows = session.execute(stmt).all()
    if not rows:
        return pd.DataFrame(
            columns=[
                "smr_key",
                "name",
                "capacity_mwe",
                "land_requirement_ha",
                "thermal_output_mwt",
                "epz_radius_km",
                "module_weight_t",
                "cooling_type",
                "design_life_yr",
                "regulatory_status",
                "exclusion_zone_radius_m",
                "cooling_water_demand_m3_per_h",
                "notes",
            ]
        )
    return pd.DataFrame(
        rows,
        columns=[
            "smr_key",
            "name",
            "capacity_mwe",
            "land_requirement_ha",
            "thermal_output_mwt",
            "epz_radius_km",
            "module_weight_t",
            "cooling_type",
            "design_life_yr",
            "regulatory_status",
            "exclusion_zone_radius_m",
            "cooling_water_demand_m3_per_h",
            "notes",
        ],
    )


def _validate_row(
    r: dict[str, object],
) -> str | None:
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


def render() -> None:
    st.title("SMR Catalogue")
    st.caption(
        "DB is the source-of-truth for SMR specs. Edit values here; "
        "Run Profile, Threshold Editor, and BF-01/BF-02 screening re-read "
        "on the next action."
    )

    profile = get_profile()
    scope_keys = list(profile.scope.smr_keys) if profile is not None else []

    show_all = st.toggle(
        "Show all designs (out-of-scope)",
        value=not bool(scope_keys),
        help=(
            "Default view shows only the SMR designs in the active run "
            "profile's scope. Toggle on to edit / inspect every row in the "
            "database, regardless of scope."
        ),
        key="smr_cat_show_all",
    )
    apply_filter = bool(scope_keys) and not show_all
    if apply_filter:
        st.info(
            "Filtered to active scope: "
            + ", ".join(f"`{k}`" for k in scope_keys)
            + ". Toggle **Show all designs** above to edit out-of-scope rows."
        )
    elif scope_keys and show_all:
        st.caption(
            "Showing every SMR design — active scope keeps "
            f"{len(scope_keys)} key(s): "
            + ", ".join(f"`{k}`" for k in scope_keys)
        )
    else:
        st.caption("No SMR scope set on the active profile — showing every design.")

    with session_scope() as session:
        df0 = _load_df(
            session,
            smr_keys=scope_keys if apply_filter else None,
        )

    st.subheader("Designs")
    edited = st.data_editor(
        df0,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "smr_key": st.column_config.TextColumn(
                "smr_key (unique id)", required=True, max_chars=30
            ),
            "name": st.column_config.TextColumn("name", required=True, max_chars=120),
            "capacity_mwe": st.column_config.NumberColumn(
                "capacity_mwe (MWe)", required=True, min_value=0.01, format="%.2f"
            ),
            "land_requirement_ha": st.column_config.NumberColumn(
                "land ha", required=True, min_value=0.01, format="%.2f"
            ),
            "thermal_output_mwt": st.column_config.NumberColumn(
                "thermal MWe", min_value=0, format="%.2f"
            ),
            "epz_radius_km": st.column_config.NumberColumn("EPZ km", format="%.2f"),
            "exclusion_zone_radius_m": st.column_config.NumberColumn(
                "excl. zone radius (m)", format="%.1f"
            ),
            "cooling_water_demand_m3_per_h": st.column_config.NumberColumn(
                "cooling water m³/h", format="%.3f"
            ),
            "module_weight_t": st.column_config.NumberColumn("module weight t", format="%.1f"),
            "cooling_type": st.column_config.TextColumn("cooling", max_chars=60),
            "design_life_yr": st.column_config.NumberColumn(
                "design life (yr)", min_value=0, step=1, format="%d"
            ),
            "regulatory_status": st.column_config.TextColumn("regulatory", max_chars=200),
            "notes": st.column_config.TextColumn("notes", max_chars=2000),
        },
        key=f"smr_cat_editor_{'scoped' if apply_filter else 'all'}",
    )

    c1, c2 = st.columns(2)
    if c1.button("Save to database", type="primary"):
        rows: list[dict] = edited.to_dict(orient="records")
        errs: list[str] = []
        for r in rows:
            e = _validate_row(r)
            if e:
                errs.append(e)
        if errs:
            st.error("Validation: " + "; ".join(errs[:8]))
        else:
            with session_scope() as session:
                for r in rows:
                    key = str(r["smr_key"]).strip()
                    row = session.get(SmrDesign, key)
                    payload = {
                        "name": str(r["name"]).strip(),
                        "capacity_mwe": float(r["capacity_mwe"]),
                        "land_requirement_ha": float(r["land_requirement_ha"]),
                        "thermal_output_mwt": _f_or_none(r.get("thermal_output_mwt")),
                        "epz_radius_km": _f_or_none(r.get("epz_radius_km")),
                        "module_weight_t": _f_or_none(r.get("module_weight_t")),
                        "cooling_type": _s_or_none(r.get("cooling_type")),
                        "design_life_yr": _i_or_none(r.get("design_life_yr")),
                        "regulatory_status": _s_or_none(r.get("regulatory_status")),
                        "exclusion_zone_radius_m": _f_or_none(
                            r.get("exclusion_zone_radius_m")
                        ),
                        "cooling_water_demand_m3_per_h": _f_or_none(
                            r.get("cooling_water_demand_m3_per_h")
                        ),
                        "notes": _s_or_none(r.get("notes")),
                    }
                    if row is None:
                        session.add(SmrDesign(smr_key=key, **payload))
                    else:
                        for a, v in payload.items():
                            setattr(row, a, v)
            gui_data.list_smrs.clear()
            st.success("Saved. SMR list cache cleared.")
    if c2.button("Add blank row (client-side only)"):
        st.session_state["_smr_draft_id"] = str(uuid.uuid4())
        st.info("Use the + row control in the table, then set smr_key before Save.")


def _f_or_none(v: object) -> float | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _i_or_none(v: object) -> int | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _s_or_none(v: object) -> str | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).strip()
    return s or None


render()
