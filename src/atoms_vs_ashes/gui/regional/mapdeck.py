# man_hours: 1.0
"""PyDeck map for Regional tab — tooltips, quartile colour, larger viewport."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd
import pydeck as pdk
import streamlit as st

from atoms_vs_ashes.gui.regional.helpers import composite_quartile, quartile_rgb


def _view_state(df: pd.DataFrame) -> pdk.ViewState:
    lat_m = float(df["lat"].mean())
    lon_m = float(df["lon"].mean())
    lat_span = max(float(df["lat"].max() - df["lat"].min()), 0.15)
    lon_span = max(float(df["lon"].max() - df["lon"].min()), 0.15)
    span = max(lat_span, lon_span)
    zoom = max(2.5, min(7.5, 8.0 - math.log(span + 0.2)))
    return pdk.ViewState(latitude=lat_m, longitude=lon_m, zoom=zoom, pitch=0)


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    q = composite_quartile(df["composite"])
    out: list[dict[str, Any]] = []
    for idx, row in df.iterrows():
        qi = int(q.loc[idx]) if idx in q.index else -1
        r, g, b = quartile_rgb(qi)
        excl = str(row.get("passed_exclusionary", "")).lower()
        passed = excl in ("true", "1", "yes")
        alpha = 210 if passed else 95
        comp = row.get("composite")
        if pd.notna(comp):
            radius_px = int(min(22, max(5, 5 + float(comp) * 1.6)))
        else:
            radius_px = 6
        site = str(row.get("site", ""))
        out.append({
            "lon": float(row["lon"]),
            "lat": float(row["lat"]),
            "radius_px": radius_px,
            "fill_color": [r, g, b, alpha],
            "site": site,
            "country": str(row.get("country", "")),
            "smr_key": str(row.get("smr_key", "")),
            "rank": int(row["rank"]) if pd.notna(row.get("rank")) else "",
            "composite": f"{float(comp):.2f}" if pd.notna(comp) else "—",
            "low": f"{float(row['low']):.2f}" if pd.notna(row.get("low")) else "—",
            "high": f"{float(row['high']):.2f}" if pd.notna(row.get("high")) else "—",
            "passed_exclusionary": str(row.get("passed_exclusionary", "")),
            "passed_avoidance": str(row.get("passed_avoidance", "")),
        })
    return out


def render_regional_map(df_geo: pd.DataFrame, *, n_chart_rows: int) -> None:
    """Full-width PyDeck scatter; height scales with number of chart rows."""
    if df_geo.empty:
        return
    df = df_geo.copy()
    records = _records(df)
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=records,
        get_position="[lon, lat]",
        get_radius="radius_px",
        radius_scale=1,
        radius_units="pixels",
        radius_min_pixels=3,
        radius_max_pixels=26,
        get_fill_color="fill_color",
        pickable=True,
        stroked=False,
    )
    deck_height = int(min(720, max(420, 320 + min(n_chart_rows, 40) * 8)))
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=_view_state(df),
        map_style=None,
        tooltip={
            "html": (
                "<b>{site}</b> ({country})<br/>"
                "SMR: {smr_key}<br/>"
                "Rank: {rank}<br/>"
                "Composite: {composite} (0–10)<br/>"
                "MC low / high: {low} … {high}<br/>"
                "Passed exclusionary: {passed_exclusionary}<br/>"
                "Passed avoidance: {passed_avoidance}"
            ),
            "style": {"backgroundColor": "#1a1c24", "color": "white"},
        },
    )
    st.pydeck_chart(deck, use_container_width=True, height=deck_height)
    st.caption(
        "Marker = one (site × SMR) pair. Colour = composite quartile within the "
        "current filter; size scales with composite. Fainter markers failed "
        "exclusionary screening."
    )
