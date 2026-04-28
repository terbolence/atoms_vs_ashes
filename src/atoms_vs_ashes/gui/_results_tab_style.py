# man_hours: 0.1
"""Small CSS helper for Results-page tab labels."""

from __future__ import annotations

import streamlit as st


def inject_results_tab_style() -> None:
    st.markdown(
        """
<style>
button[data-baseweb="tab"] p {
  font-size: 1.08rem;
  font-weight: 650;
}
</style>
""",
        unsafe_allow_html=True,
    )


__all__ = ["inject_results_tab_style"]
