# man_hours: 2.5
"""Page 2 — inline Run Profile editor (DB-backed, no YAML).

Every section of :class:`RunProfile` is exposed as a Streamlit widget
with an inline ``help=`` tooltip carrying the recommended value and a
short explanation. Edits are kept in widget-local state until the user
clicks **Save active profile**, at which point the new
:class:`RunProfile` is validated and persisted to the
``active_run_profile`` DB row via
:func:`atoms_vs_ashes.gui._state.commit_active_profile`.

``fail_thresholds`` deliberately stays on Site Selection Criteria (page 03)
since that page already provides per-row preview, bounds-checking, and
recommended-vs-current diffing.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import streamlit as st
import yaml

from atoms_vs_ashes.gui._data import (
    list_countries,
    list_site_statuses,
    list_smrs,
)
from atoms_vs_ashes.gui._state import commit_active_profile, get_profile
from atoms_vs_ashes.runprofile.schema import (
    OutputBlock,
    RunProfile,
    ScopeBlock,
    ScoringBlock,
    SensitivityBlock,
)


_SENSITIVITY_STAGES = ["weights", "mc", "threshold", "country"]
_SITE_STATUSES_ALL = ["operating", "retired", "mothballed", "construction", "cancelled"]
_DB_PROFILES = ["api", "llm", "merged"]
_WEIGHT_PROFILES = ["baseline", "w_plus_20", "w_minus_20"]
_QUALIFICATION_MODES = ["normal", "strict"]


def _identity_section(profile: RunProfile) -> dict[str, Any]:
    with st.expander("Run identity", expanded=True):
        run_label = st.text_input(
            "Run label",
            value=profile.run_label,
            help=(
                "Short slug embedded in audit paths and run rows. "
                "Recommended: lowercase + underscores (e.g. `baseline`, "
                "`ro_focus`). Max 128 chars."
            ),
        )
        notes = st.text_area(
            "Notes",
            value=profile.notes,
            help=(
                "Free-form annotation persisted with the profile. Useful for "
                "describing what makes this run different (e.g. *“stress test "
                "with 25% threshold tightening”*)."
            ),
            height=80,
        )
    return {"run_label": run_label.strip(), "notes": notes}


def _pipeline_section(profile: RunProfile) -> dict[str, Any]:
    with st.expander("Pipeline", expanded=False):
        cols = st.columns(2)
        db_profile = cols[0].selectbox(
            "DB profile",
            options=_DB_PROFILES,
            index=_DB_PROFILES.index(profile.db_profile),
            help=(
                "Which staging dataset the engine reads.\n"
                "- `merged` *(recommended)* — the merged API + LLM facts.\n"
                "- `api` — only structured/source-of-truth API rows.\n"
                "- `llm` — LLM-derived enrichment in isolation (debug only)."
            ),
        )
        weight_profile = cols[1].selectbox(
            "Weight profile",
            options=_WEIGHT_PROFILES,
            index=_WEIGHT_PROFILES.index(profile.weight_profile),
            help=(
                "Which weight column the engine normalises against.\n"
                "- `baseline` *(recommended)* — published weights.\n"
                "- `w_plus_20` / `w_minus_20` — preset stress tests "
                "(±20% on every weight)."
            ),
        )
        spec_dir = st.text_input(
            "Spec dir",
            value=profile.spec_dir,
            help=(
                "Directory of authored criterion specs. Recommended: "
                "`config/scoring_specs` (modern templates). "
                "`config/scoring_rubrics` is the legacy A/B target."
            ),
        )
        expert_override = st.toggle(
            "Expert override (bypass threshold bounds)",
            value=bool(profile.expert_override),
            help=(
                "When **off** *(recommended)* the loader rejects "
                "fail-threshold values outside the spec bounds. Turn on "
                "only when you knowingly need an out-of-bounds value — "
                "the override is flagged in every audit MD."
            ),
        )
    return {
        "db_profile": db_profile,
        "weight_profile": weight_profile,
        "spec_dir": spec_dir.strip(),
        "expert_override": bool(expert_override),
    }


def _scope_section(profile: RunProfile) -> dict[str, Any]:
    with st.expander("Scope", expanded=True):
        countries = list_countries()
        smrs = list_smrs()
        statuses = list_site_statuses()

        country_codes = [c["country_code"] for c in countries]
        country_labels = {
            c["country_code"]: f"{c['country_code']} ({c['n_sites']} sites)"
            for c in countries
        }
        smr_keys = [s["smr_key"] for s in smrs]
        smr_labels = {
            s["smr_key"]: (
                f"{s['smr_key']} — {s['name']} | "
                f"{(s.get('capacity_mwe') or 0):.0f} MWe | "
                f"{(s.get('land_requirement_ha') or 0):.0f} ha"
            )
            for s in smrs
        }

        chosen_countries = st.multiselect(
            "Countries (empty = all)",
            options=country_codes,
            default=[c for c in profile.scope.countries if c in country_codes],
            format_func=lambda c: country_labels.get(c, c),
            help=(
                "ISO-2 country codes. **Empty = no filter** (every country in "
                "the DB participates). Filter early to keep run times down "
                "during exploration; expand later for a final ranking pass."
            ),
        )
        chosen_smrs = st.multiselect(
            "SMR designs (empty = all)",
            options=smr_keys,
            default=[k for k in profile.scope.smr_keys if k in smr_keys],
            format_func=lambda k: smr_labels.get(k, k),
            help=(
                "Which SMR designs the engine evaluates. **Empty = all** "
                "designs. Recommended starting point: pick one design "
                "(e.g. `nuscale_voygr6`) so the SMR Catalogue and threshold "
                "rubric stay focused."
            ),
        )
        status_options = sorted({*_SITE_STATUSES_ALL, *statuses, *profile.scope.site_status_in})
        chosen_status = st.multiselect(
            "Site statuses",
            options=status_options,
            default=list(profile.scope.site_status_in),
            help=(
                "Which `sites.status` values qualify. Recommended: "
                "`operating`, `retired`, `mothballed` (ex-fleet candidates "
                "that already cleared site licensing). Add `construction` "
                "or `cancelled` for hypothetical brownfield expansions."
            ),
        )
        site_ids_text = st.text_area(
            "Site IDs allow-list (one per line, empty = all)",
            value="\n".join(profile.scope.site_ids),
            help=(
                "Optional explicit allow-list of `site_id` values that "
                "**must** appear in the run, regardless of country / status. "
                "Empty = no allow-list. Useful for regression tests against "
                "a fixed sample."
            ),
            height=70,
        )
        chosen_site_ids = [s.strip() for s in site_ids_text.splitlines() if s.strip()]
    return {
        "countries": chosen_countries,
        "smr_keys": chosen_smrs,
        "site_status_in": chosen_status,
        "site_ids": chosen_site_ids,
    }


def _scoring_section(profile: RunProfile) -> dict[str, Any]:
    with st.expander("Scoring", expanded=False):
        cols = st.columns(2)
        qualification_mode = cols[0].radio(
            "Qualification mode",
            options=_QUALIFICATION_MODES,
            index=_QUALIFICATION_MODES.index(profile.scoring.qualification_mode),
            help=(
                "**normal** *(recommended)* — passes safety floors only.  \n"
                "**strict** — also drops sites with avoidance penalties from "
                "the top-N shortlist."
            ),
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
            help=(
                "A pair counts as near-miss if it failed exactly one criterion "
                "by no more than this percentage of the threshold. "
                "Recommended: **10%**."
            ),
        )
        fallback = st.slider(
            "Unscored fallback score (0–10)",
            min_value=0.0,
            max_value=10.0,
            step=0.5,
            value=float(profile.scoring.unscored_fallback_score),
            help=(
                "Placeholder score for criteria with no data on this site. "
                "Recommended: **5.0** (neutral). Lower (≤3) penalises missing "
                "data; higher (≥7) is optimistic and only sensible if HARD "
                "is tight."
            ),
        )
        cols2 = st.columns(2)
        warn = cols2[0].slider(
            "Unscored fraction WARN",
            0.0, 1.0,
            float(profile.scoring.unscored_fraction_warn),
            0.01,
            help=(
                "Soft warning threshold on the share of a site's total weight "
                "that is unscored. Recommended: **0.05** (5%)."
            ),
        )
        hard = cols2[1].slider(
            "Unscored fraction HARD",
            0.0, 1.0,
            float(profile.scoring.unscored_fraction_hard),
            0.01,
            help=(
                "Hard threshold on unscored share — if exceeded the site's "
                "confidence is forced low. Must be ≥ WARN. "
                "Recommended: **0.20** (20%)."
            ),
        )
        if hard < warn:
            st.warning("HARD must be ≥ WARN — values will be clamped on Save.")
            hard = max(hard, warn)
        st.caption(
            "**Per-criterion weight overrides** are advanced — recommended to "
            "leave empty unless you are running a deliberate stress test."
        )
        weight_overrides_text = st.text_area(
            "Weight overrides (`criterion_id: weight` per line, weights in 1–10)",
            value="\n".join(
                f"{cid}: {w}" for cid, w in profile.scoring.weight_overrides.items()
            ),
            height=80,
            help=(
                "Optional. Each line `<criterion_id>: <int 1-10>`. Recommended "
                "to leave **empty**; specifying overrides here triggers a "
                "weight-perturbation audit row in every run."
            ),
        )
        weight_overrides = _parse_weight_overrides(weight_overrides_text)
    return {
        "qualification_mode": qualification_mode,
        "top_n_per_country": int(top_n),
        "near_miss_gap_pct": float(near_miss),
        "unscored_fallback_score": float(fallback),
        "unscored_fraction_warn": float(warn),
        "unscored_fraction_hard": float(hard),
        "weight_overrides": weight_overrides,
    }


def _parse_weight_overrides(text: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"weight_overrides line missing colon: {line!r}")
        cid, _, w_str = line.partition(":")
        cid = cid.strip()
        if not cid:
            raise ValueError(f"weight_overrides missing criterion id: {line!r}")
        try:
            w = int(w_str.strip())
        except ValueError as e:
            raise ValueError(
                f"weight_overrides[{cid}] must be int in [1,10]; got {w_str!r}"
            ) from e
        if not 1 <= w <= 10:
            raise ValueError(
                f"weight_overrides[{cid}] must be int in [1,10]; got {w}"
            )
        out[cid] = w
    return out


def _sensitivity_section(profile: RunProfile) -> dict[str, Any]:
    with st.expander("Sensitivity", expanded=False):
        enabled = st.multiselect(
            "Enabled stages",
            options=_SENSITIVITY_STAGES,
            default=list(profile.sensitivity.enabled),
            help=(
                "Which sub-suites the sensitivity engine runs. Recommended: "
                "`weights, mc, threshold, oat, country` (everything). Drop "
                "stages to shorten runtime during exploration."
            ),
        )
        cols = st.columns(3)
        mc_iter = cols[0].number_input(
            "MC iterations",
            min_value=100,
            max_value=1_000_000,
            value=int(profile.sensitivity.mc_iterations),
            step=500,
            help=(
                "Monte-Carlo draws per site. Recommended: **5_000** for "
                "exploratory runs, **10_000+** for publishable stability "
                "bands. Linear cost in iterations."
            ),
        )
        mc_seed = cols[1].number_input(
            "MC seed",
            value=int(profile.sensitivity.mc_seed),
            step=1,
            help="Random seed. Keep at 42 for reproducibility unless A/B testing.",
        )
        weight_pct = cols[2].slider(
            "Weight perturbation %",
            0.0, 100.0,
            float(profile.sensitivity.weight_perturbation_pct),
            1.0,
            help=(
                "± perturbation applied to each criterion weight in the weights "
                "stage. Recommended: **20%**."
            ),
        )
        cols2 = st.columns(2)
        thr_pct_text = cols2[0].text_input(
            "Threshold targeted % (comma-separated)",
            value=", ".join(
                f"{x:g}" for x in profile.sensitivity.threshold_targeted_pct
            ),
            help=(
                "Per-threshold tightening + loosening percentages explored "
                "in the threshold stage. Recommended: **10, 25**."
            ),
        )
        thr_global = cols2[1].toggle(
            "Threshold global stress",
            value=bool(profile.sensitivity.threshold_global_stress),
            help=(
                "When on, also runs an all-thresholds-at-once stress on top "
                "of the per-threshold sweep. Recommended: **on**."
            ),
        )
        cols3 = st.columns(3)
        top_n_country = cols3[0].number_input(
            "Top-N per country (sensitivity)",
            min_value=1,
            max_value=200,
            value=int(profile.sensitivity.top_n_country),
            step=1,
            help="Recommended: **20**.",
        )
        country_balance = cols3[1].slider(
            "Country balance max share",
            0.0, 1.0,
            float(profile.sensitivity.country_balance_max_share),
            0.05,
            help=(
                "Maximum allowed share of a single country in the shortlist "
                "during the country-balance stage. Recommended: **0.40** (40%)."
            ),
        )
        mc_band = cols3[2].slider(
            "MC stability band width",
            0.0, 10.0,
            float(profile.sensitivity.mc_stability_band_width),
            0.1,
            help=(
                "Score-units window used to flag stable rankings in the MC "
                "stage. Recommended: **1.0**."
            ),
        )
        thr_targeted = _parse_pct_list(thr_pct_text)
    return {
        "enabled": list(enabled),
        "mc_iterations": int(mc_iter),
        "mc_seed": int(mc_seed),
        "weight_perturbation_pct": float(weight_pct),
        "threshold_targeted_pct": thr_targeted,
        "threshold_global_stress": bool(thr_global),
        "top_n_country": int(top_n_country),
        "country_balance_max_share": float(country_balance),
        "mc_stability_band_width": float(mc_band),
    }


def _parse_pct_list(text: str) -> list[float]:
    out: list[float] = []
    for raw in text.replace(";", ",").split(","):
        s = raw.strip()
        if not s:
            continue
        try:
            v = float(s)
        except ValueError as e:
            raise ValueError(
                f"threshold_targeted_pct entry must be a number; got {s!r}"
            ) from e
        if v <= 0 or v > 100:
            raise ValueError(
                f"threshold_targeted_pct entry {v} must be in (0, 100]"
            )
        out.append(v)
    return out


def _output_section(profile: RunProfile) -> dict[str, Any]:
    with st.expander("Output", expanded=False):
        stamp = st.text_input(
            "Stamp",
            value=profile.output.stamp,
            help=(
                "Optional stamp slug appended to audit/report directories. "
                "Recommended formats: `YYYYMMDD` or `YYYYMMDD_<suffix>`. "
                "Leave empty to inherit the current date."
            ),
        )
        cols = st.columns(2)
        audit_dir = cols[0].text_input(
            "Audit dir",
            value=profile.output.audit_dir,
            help=(
                "Where engine audit MDs land. Recommended: "
                "`audit/post_processing/06_scoring`."
            ),
        )
        report_dir = cols[1].text_input(
            "Report dir",
            value=profile.output.report_dir,
            help=(
                "Where the rendered sensitivity reports land. Recommended: "
                "`report/output/sensitivity`."
            ),
        )
    return {
        "stamp": stamp.strip(),
        "audit_dir": audit_dir.strip(),
        "report_dir": report_dir.strip(),
    }


def _build_candidate(
    profile: RunProfile,
    identity: dict[str, Any],
    pipeline: dict[str, Any],
    scope: dict[str, Any],
    scoring: dict[str, Any],
    sensitivity: dict[str, Any],
    output: dict[str, Any],
) -> RunProfile:
    return profile.model_copy(
        update={
            "run_label": identity["run_label"],
            "notes": identity["notes"],
            "db_profile": pipeline["db_profile"],
            "weight_profile": pipeline["weight_profile"],
            "spec_dir": pipeline["spec_dir"],
            "expert_override": pipeline["expert_override"],
            "scope": ScopeBlock(**scope),
            "scoring": ScoringBlock(**scoring),
            "sensitivity": SensitivityBlock(**sensitivity),
            "output": OutputBlock(**output),
            "fail_thresholds": deepcopy(profile.fail_thresholds),
        }
    )


def _profiles_differ(saved: RunProfile, candidate: RunProfile) -> bool:
    return saved.model_dump(mode="json") != candidate.model_dump(mode="json")


def render() -> None:
    st.title("Run Profile")
    st.caption(
        "The active run profile is stored in the `active_run_profile` "
        "DB row (alembic 039). Edit anything below and click **Save active "
        "profile** to persist; the new values then drive every other page."
    )

    profile = get_profile()
    if profile is None:
        st.error(
            "Could not bootstrap the active run profile from the DB. "
            "Run `./.venv/bin/python -m alembic upgrade head` to seed it."
        )
        return

    identity = _identity_section(profile)
    pipeline = _pipeline_section(profile)
    scope = _scope_section(profile)
    scoring = _scoring_section(profile)
    sensitivity = _sensitivity_section(profile)
    output = _output_section(profile)

    st.divider()

    candidate: RunProfile | None = None
    build_error: str | None = None
    try:
        candidate = _build_candidate(
            profile, identity, pipeline, scope, scoring, sensitivity, output,
        )
    except Exception as exc:  # noqa: BLE001 — show validation errors inline
        build_error = str(exc)

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
        from atoms_vs_ashes.gui._state import reload_active_profile

        reload_active_profile()
        st.toast("Reloaded active profile from DB.")
        st.rerun()

    if build_error is not None:
        st.error(f"Validation failed: {build_error}")

    if save_clicked and candidate is not None:
        try:
            commit_active_profile(candidate, updated_by="gui:run_profile_page")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Save failed: {exc}")
        else:
            st.success("Active run profile saved to database.")
            st.rerun()

    if candidate is not None:
        with st.expander("Pending YAML preview (not yet saved)"):
            st.code(
                yaml.safe_dump(candidate.model_dump(mode="json"), sort_keys=False),
                language="yaml",
            )


render()
