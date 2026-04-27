# man_hours: 1.0
"""Tool 2 — Country coverage matrix tab.

One row per country with survivor / near-miss / hard-fail counts so
the user sees at a glance where the run yields a viable shortlist.
Selecting a row sets ``st.session_state["results_country"]`` so the
**Sites** tab pivots to that country.
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from atoms_vs_ashes.gui._country_names import country_name
from atoms_vs_ashes.gui._results_data_failure import (
    CountryCoverage,
    country_coverage_matrix,
)
from atoms_vs_ashes.runtime.scope import RunScope


_COVERAGE_HELP = (
    "Pick a row to focus the **Sites** tab on that country.\n\n"
    "- 🟢 *Survivors*: pass both exclusionary and avoidance floors\n"
    "- 🟧 *Near-miss*: pass exclusionary, miss avoidance\n"
    "- 🟥 *Hard-fail*: blocked by an exclusionary criterion"
)


def render_coverage_tab(
    *,
    run_id: str,
    weight_profile: str,
    country_session_key: str = "results_country",
    scope: RunScope | None = None,
) -> None:
    """Render the per-country coverage matrix tab."""
    rows = country_coverage_matrix(
        run_id, weight_profile=weight_profile, scope=scope,
    )
    if not rows:
        st.info(
            "No `composite_rankings` rows for this run × weight profile. "
            "Re-run the scoring engine to populate the table."
        )
        return

    st.caption(_COVERAGE_HELP)
    _render_stacked_bar(rows)
    _render_zero_note(rows, scope)
    _render_dataframe(rows, run_id, country_session_key)


def _render_zero_note(
    rows: list[CountryCoverage], scope: RunScope | None,
) -> None:
    """Explain why some in-scope countries show zero sites.

    Distinguishes two causes by querying the unfiltered ``sites``
    table: (a) rows exist but all are excluded by the active
    ``site_status_in`` filter, vs (b) the country has no rows at all
    in the Merged DB (the GEM coal-plant tracker has no entries).
    """
    zero = [r.country_code for r in rows if r.n_sites == 0]
    if not zero:
        return
    db_totals = _db_site_counts(zero)
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


def _db_site_counts(country_codes: list[str]) -> dict[str, int]:
    """Distinct site counts per country, ignoring the active scope."""
    from sqlalchemy import func, select
    from atoms_vs_ashes.db.engine import session_scope
    from atoms_vs_ashes.db.models import Site
    if not country_codes:
        return {}
    with session_scope() as session:
        rows = session.execute(
            select(Site.country_code, func.count(Site.site_id))
            .where(Site.country_code.in_(country_codes))
            .group_by(Site.country_code)
        ).all()
    return {str(cc): int(n) for cc, n in rows}


def _render_stacked_bar(rows: list[CountryCoverage]) -> None:
    df = pd.DataFrame([
        {
            "country": country_name(r.country_code),
            "country_code": r.country_code,
            "survivors": r.n_survivors,
            "near-miss": r.n_near_miss,
            "hard-fail": r.n_hard_fail,
        }
        for r in rows
    ])
    melted = df.melt(
        id_vars=["country", "country_code"],
        value_vars=["survivors", "near-miss", "hard-fail"],
        var_name="status",
        value_name="n",
    )
    chart = (
        alt.Chart(melted)
        .mark_bar()
        .encode(
            x=alt.X("country:N", sort=alt.SortField("country")),
            y=alt.Y("n:Q", title="# (site × SMR) pairs"),
            color=alt.Color(
                "status:N",
                scale=alt.Scale(
                    domain=["survivors", "near-miss", "hard-fail"],
                    range=["#3a7", "#e9a73a", "#c0392b"],
                ),
                title=None,
            ),
            tooltip=["country", "country_code", "status", "n"],
        )
        .properties(height=240)
    )
    st.altair_chart(chart, use_container_width=True)


def _render_dataframe(
    rows: list[CountryCoverage], run_id: str, session_key: str,
) -> None:
    df = pd.DataFrame([
        {
            "country": country_name(r.country_code),
            "country_code": r.country_code,
            "n_sites": r.n_sites,
            "survivors": r.n_survivors,
            "near_miss": r.n_near_miss,
            "hard_fail": r.n_hard_fail,
            "max_composite_survivors": r.max_composite_survivors,
            "status": _status_emoji(r),
        }
        for r in rows
    ])
    selection_state_key = f"_coverage_select::{run_id}"
    selection = st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        column_order=[
            "country", "n_sites", "survivors", "near_miss", "hard_fail",
            "max_composite_survivors", "status",
        ],
        column_config={
            "country": st.column_config.TextColumn("Country"),
            "country_code": None,
            "n_sites": st.column_config.NumberColumn("# sites"),
            "survivors": st.column_config.NumberColumn("✅ survivors"),
            "near_miss": st.column_config.NumberColumn("🟧 near-miss"),
            "hard_fail": st.column_config.NumberColumn("🟥 hard-fail"),
            "max_composite_survivors": st.column_config.NumberColumn(
                "Max composite (survivors)", format="%.2f",
            ),
            "status": st.column_config.TextColumn("Status"),
        },
        on_select="rerun",
        selection_mode="single-row",
        key=selection_state_key,
    )
    rows_sel = (
        getattr(selection, "selection", {}).get("rows")
        if hasattr(selection, "selection") else None
    )
    if rows_sel:
        cc = str(df.iloc[rows_sel[0]]["country_code"])
        st.session_state[session_key] = cc
        st.toast(f"Country focus set to {country_name(cc)}", icon="🌍")


def _status_emoji(r: CountryCoverage) -> str:
    if r.n_survivors > 0:
        return "🟢 has shortlist"
    if r.n_near_miss > 0:
        return "🟧 near-miss only"
    return "🟥 no coverage"


__all__ = ["render_coverage_tab"]
