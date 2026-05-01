# man_hours: 0.1
"""Small CSS helper for Results-page tab labels and tool selector."""

from __future__ import annotations

import streamlit as st


def inject_results_tool_selector_style() -> None:
    st.markdown(
        """
<style>
button[data-baseweb="tab"] p {
  font-size: 1.08rem;
  font-weight: 650;
}
div[data-baseweb="radio"] label {
  font-size: 1.02rem;
  font-weight: 600;
}
</style>
""",
        unsafe_allow_html=True,
    )


def inject_results_tab_style() -> None:
    """Deprecated name: use :func:`inject_results_tool_selector_style`."""
    inject_results_tool_selector_style()


__all__ = [
    "inject_results_tab_style",
    "inject_results_tool_selector_style",
]
