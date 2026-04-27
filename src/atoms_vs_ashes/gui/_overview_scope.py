# man_hours: 1.0
"""Scope controls for the Sites & SMR Setup screen."""

from __future__ import annotations

from typing import Any

import streamlit as st
from sqlalchemy import func, select

from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models import Site
from atoms_vs_ashes.gui._data import list_countries, list_site_statuses, list_smrs
from atoms_vs_ashes.runprofile.schema import RunProfile

_COAL_FLEET_DEFAULTS = ["operating", "retired", "mothballed"]


def render_scope_sections(profile: RunProfile) -> dict[str, Any]:
    """Render Countries, Sites and SMR technology filters."""
    countries = list_countries()
    smrs = list_smrs()
    statuses = _status_options(profile)
    chosen_countries = _countries_section(profile, countries)
    chosen_statuses, chosen_site_ids = _sites_section(
        profile, chosen_countries, statuses
    )
    chosen_smrs = _smr_section(profile, smrs)
    return {
        "countries": chosen_countries,
        "site_status_in": chosen_statuses,
        "site_ids": chosen_site_ids,
        "smr_keys": chosen_smrs,
    }


def _countries_section(
    profile: RunProfile, countries: list[dict[str, Any]]
) -> list[str]:
    st.subheader("Countries")
    country_codes = [c["country_code"] for c in countries]
    labels = {
        c["country_code"]: f"{c['country_code']} ({c['n_sites']} sites)"
        for c in countries
    }
    return st.multiselect(
        "Countries (empty = all)",
        options=country_codes,
        default=[c for c in profile.scope.countries if c in country_codes],
        format_func=lambda c: labels.get(c, c),
        help="ISO-2 country codes. Empty means every country in the DB participates.",
    )


def _sites_section(
    profile: RunProfile,
    chosen_countries: list[str],
    statuses: list[str],
) -> tuple[list[str], list[str]]:
    st.subheader("Sites")
    key = "overview_site_statuses"
    if key not in st.session_state:
        st.session_state[key] = [
            s for s in profile.scope.site_status_in if s in statuses
        ]
    cols = st.columns([1, 1, 4])
    if cols[0].button("Include all statuses"):
        st.session_state[key] = list(statuses)
        st.rerun()
    if cols[1].button("Coal fleet defaults"):
        st.session_state[key] = [s for s in _COAL_FLEET_DEFAULTS if s in statuses]
        st.rerun()
    chosen_statuses = st.multiselect(
        "Site statuses (empty = all)",
        options=statuses,
        key=key,
        help=(
            "Controls which `sites.status` values are scored. Include all "
            "statuses for full coal-to-nuclear opportunity discovery; use "
            "coal-fleet defaults for mature operating/retired/mothballed assets."
        ),
    )
    site_ids_text = st.text_area(
        "Site IDs allow-list (one per line, empty = all)",
        value="\n".join(profile.scope.site_ids),
        height=70,
        help="Optional explicit allow-list; empty means no site-id filter.",
    )
    chosen_site_ids = [s.strip() for s in site_ids_text.splitlines() if s.strip()]
    count = _count_sites(chosen_countries, chosen_statuses, chosen_site_ids)
    st.caption(f"Current site filter includes **{count}** sites.")
    return chosen_statuses, chosen_site_ids


def _smr_section(profile: RunProfile, smrs: list[dict[str, Any]]) -> list[str]:
    st.subheader("SMR technologies")
    keys = [s["smr_key"] for s in smrs]
    labels = {s["smr_key"]: f"{s['smr_key']} — {s['name']}" for s in smrs}
    return st.multiselect(
        "SMR technologies (empty = all)",
        options=keys,
        default=[k for k in profile.scope.smr_keys if k in keys],
        format_func=lambda k: labels.get(k, k),
        help="Selected technologies drive the SMR design-parameter table below.",
    )


def _status_options(profile: RunProfile) -> list[str]:
    return sorted({*list_site_statuses(), *profile.scope.site_status_in})


def _count_sites(
    countries: list[str],
    statuses: list[str],
    site_ids: list[str],
) -> int:
    with session_scope() as session:
        stmt = select(func.count()).select_from(Site)
        if countries:
            stmt = stmt.where(Site.country_code.in_(countries))
        if statuses:
            stmt = stmt.where(Site.status.in_(statuses))
        if site_ids:
            stmt = stmt.where(Site.site_id.in_(site_ids))
        return int(session.execute(stmt).scalar() or 0)


__all__ = ["render_scope_sections"]
