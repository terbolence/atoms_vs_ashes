# man_hours: 1.0
"""Read-side helpers the Streamlit pages call to populate selects + tables.

Every helper is small, side-effect free and DB-aware via a short-lived
:func:`session_scope`. We deliberately avoid caching DB rows in
``st.session_state`` so the GUI always reflects the live DB; Streamlit's
``@st.cache_data`` is used where the underlying data is effectively
immutable (template bundles, criterion previews) to keep the editor
snappy.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st
from sqlalchemy import distinct, select

from atoms_vs_ashes.criterion_spec.loader import (
    TemplateBundle,
    load_template_bundle,
)
from atoms_vs_ashes.criterion_spec.preview import PreviewBundle, build_preview
from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models import Site, SmrDesign
from atoms_vs_ashes.gui._metrics_loader import discover_metrics_files
from atoms_vs_ashes.runprofile.schema import RunProfile


@st.cache_data(show_spinner=False)
def list_countries() -> list[dict[str, Any]]:
    """Return ``[{country_code, n_sites}]`` for the GUI multiselect."""
    with session_scope() as session:
        rows = session.execute(
            select(Site.country_code, Site.site_id)
        ).all()
    counts: dict[str, int] = {}
    for cc, _sid in rows:
        if not cc:
            continue
        counts[cc] = counts.get(cc, 0) + 1
    return [
        {"country_code": cc, "n_sites": n}
        for cc, n in sorted(counts.items())
    ]


@st.cache_data(show_spinner=False)
def list_smrs() -> list[dict[str, Any]]:
    """Return ``[{smr_key, name, capacity_mwe, regulatory_status}]``."""
    with session_scope() as session:
        rows = session.execute(
            select(
                SmrDesign.smr_key,
                SmrDesign.name,
                SmrDesign.capacity_mwe,
                SmrDesign.regulatory_status,
            ).order_by(SmrDesign.smr_key)
        ).all()
    out = []
    for smr_key, name, capacity, reg in rows:
        out.append(
            {
                "smr_key": smr_key,
                "name": name,
                "capacity_mwe": float(capacity) if capacity is not None else None,
                "regulatory_status": reg,
            }
        )
    return out


@st.cache_data(show_spinner=False)
def list_site_statuses() -> list[str]:
    """Distinct site statuses present in the DB (for the scope filter)."""
    with session_scope() as session:
        rows = session.execute(select(distinct(Site.status))).scalars().all()
    return sorted({s for s in rows if s})


@st.cache_resource(show_spinner=False)
def load_template_bundle_cached(spec_dir: str) -> TemplateBundle:
    """Cached :func:`load_template_bundle` keyed on the spec dir path."""
    return load_template_bundle(Path(spec_dir))


def build_live_preview(profile: RunProfile, spec_dir: str) -> PreviewBundle:
    """Re-compile the rubric for the current profile state. No DB hit."""
    bundle = load_template_bundle_cached(spec_dir)
    return build_preview(bundle, profile, spec_dir=spec_dir)


def list_run_profiles() -> list[Path]:
    """All ``config/run_profiles/*.yaml`` under the repo root."""
    root = Path("config/run_profiles")
    if not root.is_dir():
        return []
    return sorted(root.glob("*.yaml"))


__all__ = [
    "build_live_preview",
    "discover_metrics_files",
    "list_countries",
    "list_run_profiles",
    "list_site_statuses",
    "list_smrs",
    "load_template_bundle_cached",
]
