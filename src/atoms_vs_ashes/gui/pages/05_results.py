# man_hours: 0.75
"""Page 5 — **Results**: Phase 1 tools (Coverage / Sites / Sensitivity).

Workshop-ready set from
``src/architecture/specs/09_results_tools_specification.md``:

* **Coverage** — country survivor / near-miss / hard-fail matrix.
* **Sites** — country site ledger on the left + drawer on the right.
* **Regional** — composite-with-MC-band bar + map across the scope.
* **Stability** — A–H stability bands joined with MC composite range.
* **Sensitivity** — live DB sensitivity snapshot.

For sensitivity runs, the first four tabs route through the *parent
scoring run's baseline view* (resolved via :func:`resolve_baseline_view`)
so the verdict join finds the matching ``screening_verdicts`` rows; the
Sensitivity tab keeps using the sensitivity ``run_id`` for its own
perturbation deltas.
"""

from __future__ import annotations

import streamlit as st

from atoms_vs_ashes.gui._baseline import resolve_baseline_view
from atoms_vs_ashes.gui._country_names import country_name
from atoms_vs_ashes.gui._metrics_loader import (
    LoadedMetrics,
    load_metrics_file,
    pick_metrics_file,
)
from atoms_vs_ashes.gui._results_data import (
    RunSummary,
    list_recent_runs,
)
from atoms_vs_ashes.gui._results_render_coverage import render_coverage_tab
from atoms_vs_ashes.gui._results_render_kpi import render_kpi_strip
from atoms_vs_ashes.gui._results_render_regional import render_regional_tab
from atoms_vs_ashes.gui._results_render_sens import render_sensitivity_tab
from atoms_vs_ashes.gui._results_render_sites import render_sites_tab
from atoms_vs_ashes.gui._results_render_stability import (
    render_stability_tab,
)
from atoms_vs_ashes.gui._state import get_profile
from atoms_vs_ashes.runtime.scope import RunScope, scope_from_run_profile


_COUNTRY_KEY = "results_country"
_INCLUDE_KEY = "results_include_eliminated"


def _select_run() -> RunSummary | None:
    """Render the run picker; default to the latest *completed* run."""
    runs = list_recent_runs(limit=30)
    if not runs:
        st.warning(
            "No runs persisted yet. Start a scoring or sensitivity run "
            "from the **Scoring Engine** page; this view will pick it "
            "up automatically."
        )
        return None
    completed = [r for r in runs if r.status == "completed"]
    default_idx = 0
    if completed:
        default_idx = runs.index(completed[0])
    return st.selectbox(
        "Run",
        runs,
        index=default_idx,
        format_func=lambda r: r.label,
        help=(
            "Lists every run with a persisted ``runs`` row. Cancelled / "
            "rolled-back runs are absent because their transaction was "
            "discarded."
        ),
        key="results_run_pick",
    )


def _control_row(
    baseline_run_id: str, baseline_weight_profile: str,
    *, scope: RunScope | None = None,
) -> tuple[str | None, bool]:
    """Sticky control row — country focus + include-eliminated toggle.

    The weight-profile picker is intentionally hidden: the user edits
    weights in the Scoring Engine page, and Coverage / Sites /
    Regional always render the canonical baseline view. Sensitivity
    perturbation profiles surface only inside the Sensitivity tab.
    """
    cols = st.columns([2, 2, 6])
    with cols[0]:
        country = _country_picker(
            baseline_run_id, baseline_weight_profile, scope=scope,
        )
    with cols[1]:
        include = st.toggle(
            "Include eliminated sites",
            value=st.session_state.get(_INCLUDE_KEY, True),
            key=_INCLUDE_KEY,
            help=(
                "On: ledger shows pass / floor-fail / hard-fail rows. "
                "Off: shortlist only — pairs that pass both floors."
            ),
        )
    return country, include


def _country_picker(
    run_id: str, weight_profile: str, *, scope: RunScope | None = None,
) -> str | None:
    """Country dropdown driven by Coverage's countries; persists in session."""
    from atoms_vs_ashes.gui._results_data_failure import (
        country_coverage_matrix,
    )

    rows = country_coverage_matrix(
        run_id, weight_profile=weight_profile, scope=scope,
    )
    options = ["(All)"] + [r.country_code for r in rows]
    persisted = st.session_state.get(_COUNTRY_KEY)
    if persisted not in options:
        persisted = None
    default_idx = options.index(persisted) if persisted else 0
    chosen = st.selectbox(
        "Country focus",
        options,
        index=default_idx,
        key="results_country_pick",
        format_func=lambda c: "(All)" if c == "(All)" else country_name(c),
        help=(
            "Drives the Sites tab. Pick *(All)* to see a regional "
            "top-100 fallback in the ledger when no country is "
            "selected. Click a row in **Coverage** to set this from "
            "the table."
        ),
    )
    if chosen == "(All)":
        st.session_state.pop(_COUNTRY_KEY, None)
        return None
    st.session_state[_COUNTRY_KEY] = chosen
    return chosen


def _auto_load_metrics(profile_audit_dir: str) -> LoadedMetrics | None:
    """Silently load the freshest ``*_metrics.json`` for the Sensitivity tab.

    No picker, no expander — the bundle is auto-generated at the end of
    every scoring / sensitivity run, so the Sensitivity tab simply
    reads the newest file under ``profile_audit_dir`` (or no-bundle
    when none exists yet, which the tab handles gracefully).
    """
    chosen = pick_metrics_file(profile_audit_dir)
    return load_metrics_file(chosen) if chosen else None


def _render_run_header(run: RunSummary) -> None:
    cols = st.columns(4)
    cols[0].metric("Kind", run.run_kind)
    cols[1].metric("Status", run.status)
    cols[2].metric(
        "Duration",
        f"{run.duration_s:.1f} s" if run.duration_s else "—",
    )
    when = run.completed_at or run.started_at
    cols[3].metric(
        "Finished at", when.strftime("%Y-%m-%d %H:%M") if when else "—",
    )
    st.caption(f"`run_id` = `{run.run_id}`")


def render() -> None:
    st.title("Results")
    st.caption(
        "Consolidated coverage / drill-down / sensitivity view of the "
        "latest runs. The page reads live from the database, so any "
        "successful scoring or sensitivity run appears immediately."
    )
    profile = get_profile()
    audit_dir = (
        profile.output.audit_dir
        if profile
        else "audit/post_processing/06_scoring"
    )
    run = _select_run()
    if run is None:
        return
    _render_run_header(run)

    view = resolve_baseline_view(run.run_id)
    baseline_run_id = view.run_id
    baseline_weight_profile = view.weight_profile
    if view.sensitivity_run_id is not None:
        st.caption(
            f"Coverage / Sites / Regional render the parent baseline "
            f"`{baseline_run_id}`; the Sensitivity & Stability tabs use "
            f"this sensitivity run."
        )

    scope = scope_from_run_profile(profile) if profile else RunScope()
    n_smrs_in_scope = (
        len(scope.smr_keys) if scope.smr_keys is not None else None
    )
    # region agent log
    from atoms_vs_ashes.gui._dbg_log import dbg as _dbg
    _dbg(
        "pages/05_results.py:render",
        "scope-from-active-profile",
        {
            "run_id": run.run_id,
            "baseline_run_id": baseline_run_id,
            "scope_country_codes": (
                list(scope.country_codes)
                if scope.country_codes is not None else None
            ),
            "scope_site_ids_n": (
                len(scope.site_ids) if scope.site_ids is not None else None
            ),
            "scope_smr_keys": (
                list(scope.smr_keys) if scope.smr_keys is not None else None
            ),
            "n_smrs_in_scope_displayed": n_smrs_in_scope,
        },
        "H7",
    )
    # endregion agent log

    country, include_eliminated = _control_row(
        baseline_run_id, baseline_weight_profile, scope=scope,
    )
    render_kpi_strip(
        run_id=baseline_run_id, weight_profile=baseline_weight_profile,
        scope=scope, n_smrs_in_scope=n_smrs_in_scope,
    )
    metrics = _auto_load_metrics(audit_dir)
    tabs = st.tabs(
        ["Coverage", "Sites", "Regional", "Stability", "Sensitivity"]
    )
    with tabs[0]:
        render_coverage_tab(
            run_id=baseline_run_id,
            weight_profile=baseline_weight_profile,
            country_session_key=_COUNTRY_KEY, scope=scope,
        )
    with tabs[1]:
        render_sites_tab(
            run_id=baseline_run_id,
            weight_profile=baseline_weight_profile,
            country_code=country, include_eliminated=include_eliminated,
            scope=scope,
        )
    with tabs[2]:
        render_regional_tab(
            run_id=baseline_run_id,
            weight_profile=baseline_weight_profile, scope=scope,
        )
    with tabs[3]:
        render_stability_tab(run=run)
    with tabs[4]:
        render_sensitivity_tab(run, metrics)


render()
