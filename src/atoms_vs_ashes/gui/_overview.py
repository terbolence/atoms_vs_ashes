# man_hours: 1.5
"""Sites & SMR Setup (home) — primary control surface of the GUI.

This is the screen users land on. It exposes the *user-meaningful*
slice of the active :class:`RunProfile` directly as inline widgets,
together with a focused mini-editor for the in-scope SMR designs.

What is editable:

* ``scope.countries`` — multiselect.
* ``scope.smr_keys`` — multiselect; selected designs feed the SMR
  sub-editor below for ``name`` / ``capacity_mwe`` / ``land_requirement_ha``.
* ``scoring.qualification_mode`` — ``normal`` / ``strict`` (with a
  rich info-icon explanation).
* ``scoring.top_n_per_country`` — number input.
* ``scoring.near_miss_gap_pct`` — slider (with a rich info-icon
  explanation).
* The Advanced expander surfaces ``weight_profile``, ``expert_override``,
  ``notes``, ``scope.site_ids``, the ``unscored_*`` knobs,
  ``weight_overrides``, and ``output.stamp``.

Hidden / passed through unchanged: ``run_label``, ``db_profile`` (always
``merged``), ``spec_dir``, ``output.audit_dir``, ``output.report_dir``,
all ``sensitivity.*``, and ``scope.site_status_in``. They are persisted
verbatim from the existing DB row when Save is clicked. Edit them on
page 02 (Run Profile) when truly needed.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import streamlit as st

from atoms_vs_ashes.gui._data import list_countries, list_smrs
from atoms_vs_ashes.gui._overview_advanced import render_advanced
from atoms_vs_ashes.gui._overview_smr import (
    render_smr_subeditor,
    save_smr_subeditor,
)
from atoms_vs_ashes.gui._state import (
    commit_active_profile,
    get_profile,
    reload_active_profile,
)
from atoms_vs_ashes.runprofile.schema import (
    OutputBlock,
    RunProfile,
    ScopeBlock,
    ScoringBlock,
)


_QUALIFICATION_MODES = ["normal", "strict"]
_QUALIFICATION_HELP = (
    "Which sites are eligible for the top-N shortlist.\n\n"
    "**normal** *(recommended)* — a site is qualified if it passes "
    "every safety floor (eliminator codes do not trip). All such sites "
    "compete for the top-N.\n\n"
    "**strict** — same safety floors **plus** sites with avoidance "
    "penalties (soft-fail / risk-flag conditions) are dropped from the "
    "top-N shortlist, even if they would otherwise rank well."
)
_NEAR_MISS_HELP = (
    "How close to passing counts as a 'near miss' on the Near-Miss "
    "page.\n\n"
    "A site/SMR pair is recorded as a near miss when it failed exactly "
    "**one** criterion by no more than this percentage of the "
    "threshold.\n\n"
    "Recommended: **10%** — surfaces only the close calls. Raising the "
    "value (e.g. 25%) widens the net to also include borderline fails."
)


def _scope_section(profile: RunProfile) -> dict[str, Any]:
    st.subheader("Scope")
    countries = list_countries()
    smrs = list_smrs()

    country_codes = [c["country_code"] for c in countries]
    country_labels = {
        c["country_code"]: f"{c['country_code']} ({c['n_sites']} sites)"
        for c in countries
    }
    smr_keys_avail = [s["smr_key"] for s in smrs]
    smr_labels = {
        s["smr_key"]: f"{s['smr_key']} — {s['name']}"
        for s in smrs
    }

    cols = st.columns(2)
    chosen_countries = cols[0].multiselect(
        "Countries (empty = all)",
        options=country_codes,
        default=[c for c in profile.scope.countries if c in country_codes],
        format_func=lambda c: country_labels.get(c, c),
        help=(
            "ISO-2 country codes. **Empty = no filter** (every country "
            "in the DB participates). Filter early to keep run times "
            "down during exploration; expand later for a final ranking pass."
        ),
    )
    chosen_smrs = cols[1].multiselect(
        "SMR designs (empty = all)",
        options=smr_keys_avail,
        default=[k for k in profile.scope.smr_keys if k in smr_keys_avail],
        format_func=lambda k: smr_labels.get(k, k),
        help=(
            "Which SMR designs the engine evaluates. **Empty = all** "
            "designs. Recommended starting point: pick one design "
            "(e.g. ``nuscale_voygr6``) so the SMR sub-editor below and "
            "the Threshold rubric stay focused."
        ),
    )
    return {"countries": chosen_countries, "smr_keys": chosen_smrs}


def _scoring_section(profile: RunProfile) -> dict[str, Any]:
    st.subheader("Scoring")
    cols = st.columns(2)
    qualification_mode = cols[0].radio(
        "Qualification mode",
        options=_QUALIFICATION_MODES,
        index=_QUALIFICATION_MODES.index(profile.scoring.qualification_mode),
        help=_QUALIFICATION_HELP,
    )
    top_n = cols[1].number_input(
        "Top-N per country",
        min_value=1,
        max_value=200,
        value=int(profile.scoring.top_n_per_country),
        step=1,
        help=(
            "Maximum number of sites kept per country in the shortlist. "
            "Recommended: **10** for a publishable shortlist; raise to "
            "20–50 for exploratory work."
        ),
    )
    near_miss = st.slider(
        "Near-miss gap (% of threshold)",
        min_value=0.0,
        max_value=100.0,
        value=float(profile.scoring.near_miss_gap_pct),
        step=1.0,
        help=_NEAR_MISS_HELP,
    )
    return {
        "qualification_mode": qualification_mode,
        "top_n_per_country": int(top_n),
        "near_miss_gap_pct": float(near_miss),
    }


def _build_candidate(
    profile: RunProfile,
    scope: dict[str, Any],
    scoring: dict[str, Any],
    advanced: dict[str, Any],
) -> RunProfile:
    """Assemble a candidate RunProfile from form state, preserving hidden fields."""
    return profile.model_copy(
        update={
            "weight_profile": advanced["weight_profile"],
            "expert_override": advanced["expert_override"],
            "notes": advanced["notes"],
            "scope": ScopeBlock(
                countries=scope["countries"],
                smr_keys=scope["smr_keys"],
                site_status_in=list(profile.scope.site_status_in),
                site_ids=advanced["site_ids"],
            ),
            "scoring": ScoringBlock(
                qualification_mode=scoring["qualification_mode"],
                top_n_per_country=scoring["top_n_per_country"],
                near_miss_gap_pct=scoring["near_miss_gap_pct"],
                unscored_fallback_score=advanced["unscored_fallback_score"],
                unscored_fraction_warn=advanced["unscored_fraction_warn"],
                unscored_fraction_hard=advanced["unscored_fraction_hard"],
                weight_overrides=advanced["weight_overrides"],
            ),
            "sensitivity": profile.sensitivity,
            "output": OutputBlock(
                stamp=advanced["stamp"],
                audit_dir=profile.output.audit_dir,
                report_dir=profile.output.report_dir,
            ),
            "fail_thresholds": deepcopy(profile.fail_thresholds),
            "run_label": profile.run_label,
            "db_profile": profile.db_profile,
            "spec_dir": profile.spec_dir,
        }
    )


def _profiles_differ(a: RunProfile, b: RunProfile) -> bool:
    return a.model_dump(mode="json") != b.model_dump(mode="json")


def _summary_metrics(scope: dict[str, Any], scoring: dict[str, Any]) -> None:
    cols = st.columns(4)
    cols[0].metric("Countries", len(scope["countries"]) or "all")
    cols[1].metric("SMRs", len(scope["smr_keys"]) or "all")
    cols[2].metric("Qualification", scoring["qualification_mode"])
    cols[3].metric("Top-N / country", scoring["top_n_per_country"])


def _save_controls(
    profile: RunProfile,
    candidate: RunProfile | None,
    build_error: str | None,
) -> None:
    cols = st.columns([1, 1, 2])
    if candidate is not None and _profiles_differ(profile, candidate):
        cols[0].markdown(":orange[**Unsaved changes**]")
    else:
        cols[0].markdown(":green[Saved]")
    save_clicked = cols[1].button(
        "Save active profile",
        type="primary",
        disabled=candidate is None,
        help="Persist the current form values to the DB.",
    )
    if cols[2].button("Discard changes & reload from DB"):
        reload_active_profile()
        st.toast("Reloaded active profile from DB.")
        st.rerun()

    if build_error is not None:
        st.error(f"Validation failed: {build_error}")

    if save_clicked and candidate is not None:
        try:
            commit_active_profile(candidate, updated_by="gui:overview")
        except Exception as exc:  # noqa: BLE001 — surface validation errors inline
            st.error(f"Save failed: {exc}")
        else:
            st.success("Active run profile saved to database.")
            st.rerun()


def render() -> None:
    st.title("Sites & SMR Setup")
    st.caption(
        "Atoms vs Ashes — Scoring Console. Pick countries and SMR designs, set the "
        "qualification mode and shortlist size, then start a scoring run from "
        "**Scoring Engine**. Everything below writes to the active run profile in the database."
    )

    profile = get_profile()
    if profile is None:
        st.error(
            "Active run profile is missing from the database. "
            "Run `./.venv/bin/python -m alembic upgrade head` to seed it."
        )
        return

    scope = _scope_section(profile)

    st.subheader("SMR design parameters (in scope)")
    st.caption(
        "Edit the core specs of the selected designs right here. The full "
        "catalogue (cooling, EPZ, regulatory status, …) is hidden from the "
        "sidebar; reach it at `/smr_catalogue` when you need the long form."
    )
    edited_smr = render_smr_subeditor(scope["smr_keys"])
    if edited_smr is not None:
        if st.button(
            "Save SMR designs",
            help="Persist the edits above to the ``smr_designs`` table.",
        ):
            if save_smr_subeditor(edited_smr):
                st.success("SMR designs saved. Catalogue cache cleared.")

    scoring = _scoring_section(profile)
    advanced = render_advanced(profile)

    st.divider()
    _summary_metrics(scope, scoring)

    candidate: RunProfile | None = None
    build_error: str | None = None
    try:
        candidate = _build_candidate(profile, scope, scoring, advanced)
    except Exception as exc:  # noqa: BLE001
        build_error = str(exc)

    _save_controls(profile, candidate, build_error)


__all__ = ["render"]
