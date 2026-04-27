# man_hours: 0.5
"""Small aligned metric-card grid for Streamlit panels."""

from __future__ import annotations

from html import escape

import streamlit as st


def render_metric_grid(
    items: list[tuple[str, str, str | None]],
    *,
    columns: int = 3,
) -> None:
    """Render uniform metric cards in one CSS grid."""
    cards = "\n".join(
        _metric_card(label, value, help_text)
        for label, value, help_text in items
    )
    st.markdown(
        f"""
<style>
.ava-metric-grid {{
  display: grid;
  grid-template-columns: repeat({columns}, minmax(0, 1fr));
  gap: 0.75rem;
  margin: 0.25rem 0 0.75rem;
}}
.ava-metric-card {{
  min-height: 5.75rem;
  padding: 0.75rem 0.9rem;
  border: 1px solid rgba(128, 128, 128, 0.28);
  border-radius: 0.55rem;
  background: rgba(128, 128, 128, 0.06);
  box-sizing: border-box;
}}
.ava-metric-label {{
  min-height: 2.1em;
  font-size: 0.78rem;
  line-height: 1.2;
  opacity: 0.72;
}}
.ava-metric-value {{
  margin-top: 0.35rem;
  font-size: 1.6rem;
  line-height: 1.2;
  font-weight: 500;
  white-space: nowrap;
}}
@media (max-width: 900px) {{
  .ava-metric-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
}}
</style>
<div class="ava-metric-grid">
{cards}
</div>
""",
        unsafe_allow_html=True,
    )


def _metric_card(label: str, value: str, help_text: str | None) -> str:
    title = f' title="{escape(help_text, quote=True)}"' if help_text else ""
    return (
        f'<div class="ava-metric-card"{title}>'
        f'<div class="ava-metric-label">{escape(label)}</div>'
        f'<div class="ava-metric-value">{escape(value)}</div>'
        "</div>"
    )


__all__ = ["render_metric_grid"]
