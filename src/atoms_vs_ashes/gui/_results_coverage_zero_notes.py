# man_hours: 0.5
"""Zero in-scope site explanations for the country coverage matrix."""

from __future__ import annotations

import streamlit as st
from sqlalchemy import func, select

from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models import Site
from atoms_vs_ashes.gui._country_names import country_name
from atoms_vs_ashes.gui._results_data_failure import CountryCoverage
from atoms_vs_ashes.runtime.scope import RunScope


def db_site_counts_unscoped(country_codes: list[str]) -> dict[str, int]:
    """Distinct site counts per country, ignoring the active scope."""
    if not country_codes:
        return {}
    with session_scope() as session:
        rows = session.execute(
            select(Site.country_code, func.count(Site.site_id))
            .where(Site.country_code.in_(country_codes))
            .group_by(Site.country_code)
        ).all()
    return {str(cc): int(n) for cc, n in rows}


def zero_site_explanations(
    rows: list[CountryCoverage], scope: RunScope | None,
) -> dict[str, str]:
    """Per-country short text for 0 in-scope sites (empty if not applicable)."""
    zero = [r.country_code for r in rows if r.n_sites == 0]
    if not zero:
        return {}
    db_totals = db_site_counts_unscoped(zero)
    status_in = (
        ", ".join(scope.site_status_in)
        if scope and scope.site_status_in else "—"
    )
    out: dict[str, str] = {}
    for r in rows:
        if r.n_sites != 0:
            continue
        cc = r.country_code
        n_db = db_totals.get(cc, 0)
        name = country_name(cc)
        if n_db > 0:
            out[cc] = (
                f"{name}: all {n_db} Merged DB site(s) for this country are "
                f"excluded by the active site_status_in filter "
                f"([{status_in}]). "
                "Add cancelled / shelved / pre-permit, etc. in **Site "
                "Selection Criteria** to include them."
            )
        else:
            out[cc] = (
                f"{name}: absent from the Merged DB (GEM coal-plant tracker "
                "has no rows for this country, verified against "
                "`Global-Coal-Plant-Tracker-January-2026.xlsx`)."
            )
    return out


def render_zero_sites_caption(
    rows: list[CountryCoverage], scope: RunScope | None,
) -> None:
    """Caption summarizing in-scope countries with zero sites (two causes)."""
    zero = [r.country_code for r in rows if r.n_sites == 0]
    if not zero:
        return
    db_totals = db_site_counts_unscoped(zero)
    no_db = [c for c in zero if db_totals.get(c, 0) == 0]
    filtered = [c for c in zero if db_totals.get(c, 0) > 0]
    bits: list[str] = []
    if filtered:
        status_in = (
            ", ".join(scope.site_status_in)
            if scope and scope.site_status_in else "—"
        )
        labels = ", ".join(
            f"{country_name(c)} ({db_totals[c]} excluded)" for c in filtered
        )
        bits.append(
            f"**Filtered out by `site_status_in = [{status_in}]`**: "
            f"{labels}. Add `cancelled` / `shelved` / `pre-permit` etc. "
            f"to the filter in **Site Selection Criteria** to include them."
        )
    if no_db:
        labels = ", ".join(country_name(c) for c in no_db)
        bits.append(
            f"**Absent from the Merged DB**: {labels}. The GEM coal-plant "
            f"tracker has no rows for these countries (verified against "
            f"`Global-Coal-Plant-Tracker-January-2026.xlsx`)."
        )
    st.caption(
        f"⚠️ {len(zero)} / {len(rows)} countries show **0 in-scope sites**. "
        + " ".join(bits)
    )


__all__ = [
    "db_site_counts_unscoped",
    "render_zero_sites_caption",
    "zero_site_explanations",
]
