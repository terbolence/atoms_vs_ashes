# man_hours: 0.4
"""Shared country-focus controls for the Results page."""

from __future__ import annotations

import streamlit as st

from atoms_vs_ashes.gui._country_names import country_name
from atoms_vs_ashes.runtime.scope import RunScope


def render_country_focus(
    run_id: str,
    weight_profile: str,
    *,
    scope: RunScope | None,
    country_session_key: str,
    widget_key: str,
    allow_all: bool = True,
    default_country: str | None = None,
) -> str | None:
    """Render the shared Results country selector."""
    from atoms_vs_ashes.gui._results_data_failure import (
        country_coverage_matrix,
    )

    rows = country_coverage_matrix(
        run_id, weight_profile=weight_profile, scope=scope,
    )
    country_options = [r.country_code for r in rows]
    options = (["(All)"] if allow_all else []) + country_options
    if not options:
        st.warning("No countries are available for this run/scope.")
        return None
    persisted = st.session_state.get(country_session_key)
    if persisted not in options:
        persisted = default_country if default_country in options else None
    if persisted is None and not allow_all and country_options:
        persisted = country_options[0]
    chosen = st.selectbox(
        "Country focus",
        options,
        index=options.index(persisted) if persisted else 0,
        key=widget_key,
        format_func=lambda c: "(All)" if c == "(All)" else country_name(c),
        help=(
            "Controls country-scoped Results views. Pick *(All)* for the "
            "regional dataset; pick a country for the national dataset."
        ),
    )
    if chosen == "(All)":
        st.session_state.pop(country_session_key, None)
        return None
    st.session_state[country_session_key] = chosen
    return str(chosen)


def render_include_eliminated_toggle(*, include_session_key: str) -> bool:
    """Sites-tab eliminated-pair toggle."""
    return st.toggle(
        "Include eliminated sites",
        value=st.session_state.get(include_session_key, True),
        key=include_session_key,
        help=(
            "On: ledger shows full pass (green) / exclusion pass + "
            "avoidance flag (yellow) / hard-fail (red-orange). "
            "Off: shortlist only -- pairs that clear exclusionary and "
            "avoidance flags."
        ),
    )


__all__ = ["render_country_focus", "render_include_eliminated_toggle"]
