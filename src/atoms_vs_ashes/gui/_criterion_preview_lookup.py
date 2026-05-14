# man_hours: 0.3
"""Cached criterion-preview lookup for result-side info popovers."""

from __future__ import annotations

import streamlit as st

from atoms_vs_ashes.criterion_spec.preview import CriterionPreview
from atoms_vs_ashes.gui._data import build_live_preview
from atoms_vs_ashes.runprofile.schema import RunProfile


@st.cache_data(show_spinner=False)
def criterion_preview_lookup(
    weight_profile: str,
    spec_dir: str = "config/scoring_specs",
) -> dict[str, CriterionPreview]:
    """Return criterion previews keyed by criterion id for result drawers."""
    profile = RunProfile(run_label="site-detail", weight_profile=weight_profile)
    preview = build_live_preview(profile, spec_dir)
    return {c.criterion_id: c for c in preview.criteria}


__all__ = ["criterion_preview_lookup"]
