# man_hours: 1.0
"""PyDeck map for Regional tab — tooltips, quartile colour, larger viewport."""

from __future__ import annotations

import html
import math
from typing import Any

import pandas as pd
import pydeck as pdk
import streamlit as st

from atoms_vs_ashes.gui.regional.helpers import (
    MISSING_COMPOSITE_RGB,
    QUARTILE_PALETTE,
    composite_quartile,
    quartile_rgb,
)

# Marker size (pixels): subtler than legacy 5–22 so plant locations read clearly.
_RADIUS_BASE_PX = 2
_RADIUS_PER_SCORE = 1.0
_RADIUS_MIN_PX = 3
_RADIUS_MAX_PX = 13
_RADIUS_MISSING_PX = 4

# Match fill alpha in _records (passed vs failed exclusionary).
_ALPHA_PASSED_EXCLUSIONARY = 210
_ALPHA_FAILED_EXCLUSIONARY = 95

# PyDeck layer clamps (align with _RADIUS_*).
_LAYER_RADIUS_MIN_PX = 2
_LAYER_RADIUS_MAX_PX = 14

_QUARTILE_LABELS = (
    "Lowest 25% of composite scores (this filter)",
    "Next 25%",
    "Next 25%",
    "Highest 25%",
)


def _view_state(df: pd.DataFrame) -> pdk.ViewState:
    lat_m = float(df["lat"].mean())
    lon_m = float(df["lon"].mean())
    lat_span = max(float(df["lat"].max() - df["lat"].min()), 0.15)
    lon_span = max(float(df["lon"].max() - df["lon"].min()), 0.15)
    span = max(lat_span, lon_span)
    zoom = max(2.5, min(7.5, 8.0 - math.log(span + 0.2)))
    return pdk.ViewState(latitude=lat_m, longitude=lon_m, zoom=zoom, pitch=0)


def _composite_radius_px(comp: Any) -> int:
    if pd.isna(comp):
        return _RADIUS_MISSING_PX
    raw = _RADIUS_BASE_PX + float(comp) * _RADIUS_PER_SCORE
    return int(min(_RADIUS_MAX_PX, max(_RADIUS_MIN_PX, raw)))


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    q = composite_quartile(df["composite"])
    out: list[dict[str, Any]] = []
    for idx, row in df.iterrows():
        qi = int(q.loc[idx]) if idx in q.index else -1
        r, g, b = quartile_rgb(qi)
        excl = str(row.get("passed_exclusionary", "")).lower()
        passed = excl in ("true", "1", "yes")
        alpha = (
            _ALPHA_PASSED_EXCLUSIONARY if passed else _ALPHA_FAILED_EXCLUSIONARY
        )
        comp = row.get("composite")
        radius_px = _composite_radius_px(comp)
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


def _swatch_style(rgb: tuple[int, int, int], alpha: int) -> str:
    r, g, b = rgb
    return (
        f"display:inline-block;width:14px;height:14px;border-radius:3px;"
        f"background:rgba({r},{g},{b},{alpha / 255.0:.3f});"
        f"border:1px solid rgba(0,0,0,0.25);vertical-align:middle;"
    )


def _render_regional_map_legend() -> None:
    """Visual key for quartile colours, missing composite, and opacity rule."""
    rows_html: list[str] = []
    for i, (label, rgb) in enumerate(
        zip(_QUARTILE_LABELS, QUARTILE_PALETTE, strict=True),
    ):
        sw = _swatch_style(rgb, _ALPHA_PASSED_EXCLUSIONARY)
        rows_html.append(
            f'<div style="display:flex;align-items:center;gap:0.5rem;'
            f'margin:0.15rem 0"><span style="{sw}"></span>'
            f"<span>Q{i + 1} — {html.escape(label)}</span></div>",
        )
    mr, mg, mb = MISSING_COMPOSITE_RGB
    rows_html.append(
        f'<div style="display:flex;align-items:center;gap:0.5rem;'
        f'margin:0.15rem 0"><span style="{_swatch_style(MISSING_COMPOSITE_RGB, _ALPHA_PASSED_EXCLUSIONARY)}"></span>'
        f"<span>{html.escape('No composite — quartile not assigned')}</span></div>",
    )
    # Opacity: same hue, passed vs failed
    br, bg, bb = QUARTILE_PALETTE[0]
    rows_html.append(
        '<div style="display:flex;align-items:center;gap:0.65rem;flex-wrap:wrap;'
        'margin:0.35rem 0 0 0">'
        f'<span style="{_swatch_style((br, bg, bb), _ALPHA_PASSED_EXCLUSIONARY)}"></span>'
        "<span>Passed exclusionary</span>"
        f'<span style="{_swatch_style((br, bg, bb), _ALPHA_FAILED_EXCLUSIONARY)}"></span>'
        "<span>Failed exclusionary (fainter)</span>"
        "</div>",
    )
    block = (
        '<div style="font-size:0.88rem;line-height:1.35;opacity:0.95">'
        "<strong>Map legend</strong> — colours are <em>quartiles of composite score "
        "among the points shown</em> (not fixed 0–10 cutoffs). "
        f'{"".join(rows_html)}</div>'
    )
    st.markdown(block, unsafe_allow_html=True)


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
        radius_min_pixels=_LAYER_RADIUS_MIN_PX,
        radius_max_pixels=_LAYER_RADIUS_MAX_PX,
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
    _render_regional_map_legend()
    st.caption(
        "Each marker is one (site × SMR) pair. Marker diameter scales with composite "
        "(0–10); see the legend for quartile colours and screening opacity."
    )


__all__ = ["render_regional_map"]
