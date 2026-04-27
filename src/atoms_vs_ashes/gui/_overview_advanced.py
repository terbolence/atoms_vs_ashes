# man_hours: 1.0
"""'Advanced (rare)' expander on the Overview screen.

Collects the run-profile knobs that exist for power-users / regression
flows but should not crowd the home screen for typical operators:

* ``weight_profile`` — preset ±20% weight stress tests.
* ``expert_override`` — bypass threshold bounds (dangerous).
* ``notes`` — free-form annotation.
* ``scope.site_ids`` — explicit site allow-list.
* ``scoring.unscored_fallback_score`` and the ``unscored_fraction_*``
  pair — confidence-floor knobs.
* ``scoring.weight_overrides`` — per-criterion weight tweaks.
* ``output.stamp`` — manual audit-dir suffix.

Other ``RunProfile`` fields (``run_label``, ``db_profile``, ``spec_dir``,
``output.audit_dir``, ``output.report_dir``, every ``sensitivity.*``
field, and ``scope.site_status_in``) are deliberately **not** exposed
here — they are pinned to their existing values and edited only on
page 02 / page 07 when needed.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from atoms_vs_ashes.runprofile.schema import RunProfile


_WEIGHT_PROFILES = ["baseline", "w_plus_20", "w_minus_20"]


def parse_weight_overrides(text: str) -> dict[str, int]:
    """Parse ``criterion_id: weight`` lines into a validated dict."""
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


def render_advanced(profile: RunProfile) -> dict[str, Any]:
    """Render the Advanced expander; return a dict of edited values."""
    with st.expander("Advanced (rare)", expanded=False):
        cols = st.columns(2)
        weight_profile = cols[0].selectbox(
            "Weight profile",
            options=_WEIGHT_PROFILES,
            index=_WEIGHT_PROFILES.index(profile.weight_profile),
            help=(
                "Preset weight stress tests. **baseline** *(recommended)* "
                "uses the published weights. **w_plus_20** / **w_minus_20** "
                "scale every criterion weight by ±20% — useful for quick "
                "robustness checks without editing per-criterion overrides."
            ),
        )
        expert_override = cols[1].toggle(
            "Expert override (bypass threshold bounds)",
            value=bool(profile.expert_override),
            help=(
                "**Off** *(recommended)* — the loader rejects fail-threshold "
                "values outside spec bounds. Turn on only when you knowingly "
                "need an out-of-bounds value; the override is flagged in "
                "every audit MD."
            ),
        )
        notes = st.text_area(
            "Notes",
            value=profile.notes,
            help=(
                "Free-form annotation persisted with the profile. Use it to "
                "describe what makes this run different (e.g. \"stress test "
                "with 25% threshold tightening\")."
            ),
            height=70,
        )
        site_ids_text = st.text_area(
            "Site IDs allow-list (one per line, empty = all)",
            value="\n".join(profile.scope.site_ids),
            height=70,
            help=(
                "Optional explicit allow-list of ``site_id`` values that "
                "**must** appear in the run, regardless of country / status. "
                "Empty = no allow-list. Useful for regression tests against "
                "a fixed sample."
            ),
        )
        site_ids = [s.strip() for s in site_ids_text.splitlines() if s.strip()]

        cols2 = st.columns(2)
        warn = cols2[0].slider(
            "Unscored fraction WARN",
            0.0, 1.0,
            float(profile.scoring.unscored_fraction_warn),
            0.01,
            help=(
                "Soft warning threshold on the share of a site's total "
                "weight that is unscored. Recommended: **0.05** (5%)."
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

        fallback = st.slider(
            "Unscored fallback score (0–10)",
            0.0, 10.0,
            float(profile.scoring.unscored_fallback_score),
            0.5,
            help=(
                "Placeholder score for criteria with no data on this site. "
                "Recommended: **5.0** (neutral). Lower (≤3) penalises "
                "missing data; higher (≥7) is optimistic."
            ),
        )

        weight_overrides_text = st.text_area(
            "Weight overrides (`criterion_id: weight` per line, weights 1–10)",
            value="\n".join(
                f"{cid}: {w}" for cid, w in profile.scoring.weight_overrides.items()
            ),
            height=80,
            help=(
                "Optional per-criterion weight overrides. Recommended to "
                "leave **empty**; specifying overrides triggers a weight-"
                "perturbation audit row in every run."
            ),
        )
        override_error: str | None = None
        try:
            weight_overrides = parse_weight_overrides(weight_overrides_text)
        except ValueError as e:
            weight_overrides = dict(profile.scoring.weight_overrides)
            override_error = str(e)
        if override_error:
            st.error(override_error)

        stamp = st.text_input(
            "Output stamp",
            value=profile.output.stamp,
            help=(
                "Optional stamp slug appended to audit/report dirs. "
                "Recommended formats: `YYYYMMDD` or `YYYYMMDD_<suffix>`. "
                "Leave empty to inherit the current date."
            ),
        )

    return {
        "weight_profile": weight_profile,
        "expert_override": bool(expert_override),
        "notes": notes,
        "site_ids": site_ids,
        "unscored_fraction_warn": float(warn),
        "unscored_fraction_hard": float(hard),
        "unscored_fallback_score": float(fallback),
        "weight_overrides": weight_overrides,
        "stamp": stamp.strip(),
        "_override_error": override_error,
    }


__all__ = ["parse_weight_overrides", "render_advanced"]
