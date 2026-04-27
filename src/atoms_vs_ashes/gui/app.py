# man_hours: 1.25
"""Streamlit entry-point: ``streamlit run src/atoms_vs_ashes/gui/app.py``.

The GUI no longer asks the user to pick a YAML — the active
:class:`RunProfile` is the singleton row in the ``active_run_profile``
DB table (alembic 039). The **Sites & SMR Setup** screen exposes the user-meaningful
slice of that profile as inline forms; the deeper *Run Profile* screen
(page 02) keeps the full editor for power-users and stays reachable by
URL but is hidden from the sidebar.

Navigation uses :func:`streamlit.navigation` with the menu hidden so
the sidebar can list :func:`streamlit.page_link` entries, each with a
right-aligned info icon (SVG) whose blurb is shown on **hover** via a
native HTML :attr:`title` tooltip (no second help chip, no click).
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

import streamlit as st

from atoms_vs_ashes.gui._overview import render as render_overview

_GUI_DIR = Path(__file__).resolve().parent
_PAGES_DIR = _GUI_DIR / "pages"

# (filename, sidebar label, tooltip for the info icon, hidden_from_sidebar)
_SCREEN_PAGES: tuple[tuple[str, str, str, bool], ...] = (
    (
        "01_smr_catalogue.py",
        "SMR Catalogue (advanced)",
        (
            "Full editor for every ``smr_designs`` field — cooling, EPZ radius, "
            "regulatory status, etc. Hidden from the sidebar because **Sites & SMR Setup** "
            "already exposes the four required fields (name, capacity, "
            "land) for the in-scope SMRs; reach this screen via the "
            "/smr_catalogue URL when you need the full row."
        ),
        True,
    ),
    (
        "02_run_profile.py",
        "Run Profile (advanced)",
        (
            "Full inline editor for every ``RunProfile`` field — sensitivity defaults, "
            "output paths, ``run_label``, etc. Hidden from the sidebar because "
            "**Sites & SMR Setup** already covers the day-to-day knobs; reachable via the "
            "/run_profile URL when you need the long form."
        ),
        True,
    ),
    (
        "03_threshold_editor.py",
        "Site Selection Criteria",
        (
            "Adjust fail thresholds with live rubric preview: recommended values, bounds, "
            "and diffs versus the template. Complements fail-threshold fields omitted from "
            "Run profile."
        ),
        False,
    ),
    (
        "04_run_dashboard.py",
        "Scoring Engine",
        (
            "Start and monitor scoring and sensitivity jobs: progress, logs, and run "
            "controls tied to the active profile."
        ),
        False,
    ),
    (
        "05_results.py",
        "Results",
        (
            "Consolidated DB-backed view of every persisted run: country breakdown, top "
            "sites, near-miss roll-up, and sensitivity diagnostics (MC, threshold sweep, "
            "country balance, weight perturbation). Optional ``*_metrics.json`` bundle "
            "unlocks the heavier offline panels."
        ),
        False,
    ),
)


def _nav_specs() -> list[tuple[Any, str, bool]]:
    """Build :class:`st.Page` objects paired with tooltip text and sidebar visibility."""
    overview = st.Page(
        render_overview,
        title="Sites & SMR Setup",
        icon=":material/home:",
        default=True,
        url_path="",
    )
    overview_help = (
        "Sites & SMR Setup (home): edit the active profile inline — countries, SMRs in scope, "
        "qualification mode, top-N, near-miss gap. SMR design specs (capacity, "
        "land) are editable here too. Save persists to the DB."
    )
    specs: list[tuple[Any, str, bool]] = [(overview, overview_help, False)]
    for fname, title, blurb, hidden in _SCREEN_PAGES:
        specs.append(
            (
                st.Page(_PAGES_DIR / fname, title=title),
                blurb,
                hidden,
            )
        )
    return specs


def _sidebar_info_hover_html(blurb: str) -> str:
    """Right-aligned info SVG + :attr:`title` for browser hover (no click)."""
    title = html.escape(" ".join(blurb.split()), quote=True)
    return (
        '<div style="text-align:right;padding:0.1rem 0 0.15rem 0">'
        f'<span style="cursor:help;display:inline-flex;align-items:center;'
        f'justify-content:center" title="{title}">'
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" '
        'height="18" style="vertical-align:middle;opacity:0.72" fill="currentColor" '
        'aria-hidden="true" focusable="false">'
        '<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>'
        "</svg></span></div>"
    )


def _sidebar_screen_nav(specs: list[tuple[Any, str, bool]]) -> None:
    """One row per screen: page link, then a right column with hover title help."""
    st.sidebar.markdown("##### Screens")
    for pg_obj, blurb, hidden in specs:
        if hidden:
            continue
        c_link, c_info = st.sidebar.columns(
            (5, 1),
            gap="small",
            vertical_alignment="center",
        )
        with c_link:
            st.page_link(pg_obj, use_container_width=True)
        with c_info:
            st.html(_sidebar_info_hover_html(blurb), width="content")


def main() -> None:
    st.set_page_config(
        page_title="Atoms vs Ashes — Scoring Console",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    specs = _nav_specs()
    pg = st.navigation([s[0] for s in specs], position="hidden")

    _sidebar_screen_nav(specs)

    pg.run()


if __name__ == "__main__":
    main()
