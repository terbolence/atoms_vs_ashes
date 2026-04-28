# man_hours: 0.45
"""Hex colours for site × SMR pair status in Results (Sites / Coverage).

Semantics match ``composite_rankings`` gates:

- **Full pass** — passed exclusionary *and* avoidance.
- **Avoidance flag** — passed exclusionary, failed avoidance (still rankable).
- **Hard-fail** — failed exclusionary screening.

Palette: green · **lemon yellow** · red-orange. The outer pair keeps a tight
HSL match; the middle hue is shifted toward true yellow (not brown/amber) so
near-miss reads clearly on white. Chart (Altair) and legend share these hex
values.
"""

from __future__ import annotations

import html

import streamlit as st

# Full pass (both gates) — clear green, matched lightness to red-orange pair
FULL_PASS_HEX = "#45cd85"

# Near-miss / avoidance — lemon yellow (hue ~58°, high chroma; avoids ochre)
EXCLUSION_PASS_AVOIDANCE_FAIL_HEX = "#e4da3a"

# Hard exclusionary failure — same family as before (red-orange)
HARD_FAIL_HEX = "#cd5745"

STATUS_HEX = {
    "pass": FULL_PASS_HEX,
    "avoidance-flag": EXCLUSION_PASS_AVOIDANCE_FAIL_HEX,
    "hard-fail": HARD_FAIL_HEX,
}

COVERAGE_CHART_DOMAIN = ["survivors", "near-miss", "hard-fail"]
COVERAGE_CHART_RANGE = [
    FULL_PASS_HEX,
    EXCLUSION_PASS_AVOIDANCE_FAIL_HEX,
    HARD_FAIL_HEX,
]

# Ledger / table text (no platform-dependent emoji colours)
STATUS_LEDGER_LABEL = {
    "pass": "Full pass",
    "avoidance-flag": "Avoidance flag",
    "hard-fail": "Hard-fail",
}


def _swatch_span(hex_color: str) -> str:
    """Inline square using ``background`` so it matches Vega bar fills pixel-for-pixel."""
    safe = html.escape(hex_color, quote=True)
    return (
        f'<span style="display:inline-block;width:0.65em;height:0.65em;'
        f"background:{safe};border-radius:2px;vertical-align:text-bottom;"
        f'margin-right:0.2em;border:1px solid rgba(0,0,0,0.06)"></span>'
    )


def severity_hex(severity: str) -> str:
    """Criterion severity tint for drawer cards (exclusionary vs avoidance)."""
    return {
        "exclusionary": HARD_FAIL_HEX,
        "avoidance": EXCLUSION_PASS_AVOIDANCE_FAIL_HEX,
    }.get(severity, "#888")


def render_site_status_legend() -> None:
    """One-line legend for Sites / Coverage (swatches + labels; hex = chart scale)."""
    st.markdown(
        "<p style='margin:0 0 0.5rem 0;font-size:0.88rem;color:#555;line-height:1.45'>"
        f"{_swatch_span(FULL_PASS_HEX)}"
        "full pass (exclusion + avoidance) &nbsp; "
        f"{_swatch_span(EXCLUSION_PASS_AVOIDANCE_FAIL_HEX)}"
        "exclusion pass · avoidance flag &nbsp; "
        f"{_swatch_span(HARD_FAIL_HEX)}"
        "hard-fail (exclusionary)"
        "</p>",
        unsafe_allow_html=True,
    )


__all__ = [
    "COVERAGE_CHART_DOMAIN",
    "COVERAGE_CHART_RANGE",
    "EXCLUSION_PASS_AVOIDANCE_FAIL_HEX",
    "FULL_PASS_HEX",
    "HARD_FAIL_HEX",
    "render_site_status_legend",
    "severity_hex",
    "STATUS_HEX",
    "STATUS_LEDGER_LABEL",
]
