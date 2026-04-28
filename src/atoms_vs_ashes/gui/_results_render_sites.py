# man_hours: 1.0
"""Tool 3 + 4 host — Country site ledger with side-column drawer.

Left column: a selectable ledger of every (site, SMR) pair in the
chosen country (or top-100 regional fallback when no country is
picked). Right column: drawer with failed-criteria cards, strengths,
per-criterion bar and per-family contribution stack. Selection
state is keyed per-run so switching runs does not strand a stale row.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atoms_vs_ashes.gui._country_names import country_name
from atoms_vs_ashes.gui._results_data import is_single_smr
from atoms_vs_ashes.gui._results_data_failure import (
    SiteLedgerRow,
    country_site_ledger,
)
from atoms_vs_ashes.gui._live_text_input import live_text_input
from atoms_vs_ashes.gui._results_render_drawer import render_site_detail
from atoms_vs_ashes.gui._results_site_status_palette import (
    STATUS_LEDGER_LABEL,
    render_site_status_legend,
)
from atoms_vs_ashes.runtime.scope import RunScope


def render_sites_tab(
    *,
    run_id: str,
    weight_profile: str,
    country_code: str | None,
    include_eliminated: bool,
    scope: RunScope | None = None,
) -> None:
    """Render the Sites tab — ledger on the left, drawer on the right."""
    rows = country_site_ledger(
        run_id, country_code,
        weight_profile=weight_profile,
        include_eliminated=include_eliminated,
        limit=100 if not country_code else None,
        scope=scope,
    )
    if not rows:
        st.info(_no_rows_message(country_code, include_eliminated))
        return

    if not country_code:
        st.caption(
            "No country picked yet — showing top 100 (site × SMR) pairs "
            "across the whole run. Pick a country in **Coverage** or "
            "with the **Country focus** selector above to drill into one."
        )

    single_smr = is_single_smr(run_id, scope=scope)
    render_site_status_legend()
    left, right = st.columns([0.55, 0.45])
    with left:
        selected = _render_ledger_table(rows, run_id, single_smr=single_smr)
    with right:
        if selected is None:
            st.info(
                "Pick a row on the left to open the site detail drawer."
            )
        else:
            render_site_detail(
                run_id=run_id, weight_profile=weight_profile,
                site_id=selected.site_id, smr_key=selected.smr_key,
                show_smr=not single_smr,
            )


def _filter_ledger_rows(
    rows: list[SiteLedgerRow], query: str,
) -> list[SiteLedgerRow]:
    """Case-insensitive substring match on site name, country, SMR, top blocker."""
    if not (query and query.strip()):
        return rows
    q = query.strip().lower()
    out: list[SiteLedgerRow] = []
    for r in rows:
        parts = [
            r.name,
            r.country_code,
            country_name(r.country_code),
            r.smr_key,
            r.top_blocking_criterion_id or "",
        ]
        joined = " ".join(str(p) for p in parts if p is not None).lower()
        if q in joined:
            out.append(r)
    return out


def _no_rows_message(country_code: str | None, include_eliminated: bool) -> str:
    base = "No (site × SMR) rows for the current filters."
    hints: list[str] = []
    if country_code:
        hints.append(f"country = `{country_code}`")
    if not include_eliminated:
        hints.append("`include eliminated` = off")
    if hints:
        return f"{base} Active filters: {', '.join(hints)}."
    return base


def _render_ledger_table(
    rows: list[SiteLedgerRow], run_id: str, *, single_smr: bool,
) -> SiteLedgerRow | None:
    search = live_text_input(
        "Search power plants",
        key=f"_sites_ledger_search::{run_id}",
        placeholder="Filter by site name, country, SMR, or top blocker…",
        help=(
            "Filters the ledger as you type. If it only updates after Enter "
            "or defocus, add streamlit-keyup (atoms-vs-ashes[gui] includes it)."
        ),
    )
    filtered = _filter_ledger_rows(rows, search)
    if not filtered and search.strip():
        st.caption("No sites match that search. Clear the field to see the full list.")
        return None
    ledger = filtered
    df = _to_dataframe(ledger, single_smr=single_smr)
    column_config = _column_config(single_smr=single_smr)
    selection_state_key = f"_sites_ledger_select::{run_id}"
    selection = st.dataframe(
        df, hide_index=True, use_container_width=True,
        column_config=column_config,
        on_select="rerun",
        selection_mode="single-row",
        key=selection_state_key,
    )
    rows_sel = (
        getattr(selection, "selection", {}).get("rows")
        if hasattr(selection, "selection") else None
    )
    if not rows_sel:
        return None
    return ledger[rows_sel[0]]


def _to_dataframe(rows: list[SiteLedgerRow], *, single_smr: bool) -> pd.DataFrame:
    items = []
    for r in rows:
        item = {
            "rank": r.rank_position,
            "name": r.name,
            "country": country_name(r.country_code),
            "status": STATUS_LEDGER_LABEL.get(r.status, r.status),
            "composite": r.composite,
            "MC band": _mc_band(r),
            "# failed": r.n_failed_criteria,
            "top blocker": r.top_blocking_criterion_id or "—",
            "worst gap %": r.worst_gap_pct,
        }
        if not single_smr:
            item["smr_key"] = r.smr_key
        items.append(item)
    df = pd.DataFrame(items)
    if not single_smr and "smr_key" in df.columns:
        cols = ["rank", "name", "country", "smr_key", "status",
                "composite", "MC band", "# failed", "top blocker",
                "worst gap %"]
        df = df[cols]
    return df


def _mc_band(r: SiteLedgerRow) -> str:
    if r.composite_low is None or r.composite_high is None:
        return "—"
    return f"{r.composite_low:.2f} – {r.composite_high:.2f}"


def _column_config(*, single_smr: bool) -> dict:
    cfg = {
        "rank": st.column_config.NumberColumn("Rank"),
        "name": st.column_config.TextColumn("Site"),
        "country": st.column_config.TextColumn("Country"),
        "status": st.column_config.TextColumn("Status"),
        "composite": st.column_config.ProgressColumn(
            "Composite", min_value=0.0, max_value=10.0, format="%.2f",
        ),
        "MC band": st.column_config.TextColumn(
            "MC band",
            help=(
                "Monte-Carlo p05 – p95 from sensitivity runs; '—' for "
                "scoring-only runs."
            ),
        ),
        "# failed": st.column_config.NumberColumn("# failed criteria"),
        "top blocker": st.column_config.TextColumn(
            "Top blocker",
            help="Criterion with the largest gap (% off threshold).",
        ),
        "worst gap %": st.column_config.NumberColumn(
            "Worst gap %", format="%.1f",
        ),
    }
    if not single_smr:
        cfg["smr_key"] = st.column_config.TextColumn("SMR")
    return cfg


__all__ = ["render_sites_tab"]
