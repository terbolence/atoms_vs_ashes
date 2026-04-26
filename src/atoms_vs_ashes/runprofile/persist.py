# man_hours: 2.0
"""Provenance helpers turning a :class:`RunProfile` into ``DatasetMeta``.

Implements §5 of ``scoring_control_gui_872d4eb7``: every run records
the path + sha256 of the user-edited :class:`RunProfile`, the path +
sha256 of the compiled :class:`Criterion` bundle the engine actually
saw, the resolved scope cardinalities, and a structured
``scope_summary`` (resolved scope, fail-threshold overrides,
expert-override deviations). The same helper is reused by the
audit-MD writers, so on-disk audits and DB rows agree by construction.

Two runs with the same profile (and therefore the same compiled
bundle) emit identical hashes — that is the reproducibility contract
the GUI relies on.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from atoms_vs_ashes.criterion_spec import (
    CompiledBundle,
    bundle_sha256,
)
from atoms_vs_ashes.db.runs import DatasetMeta
from atoms_vs_ashes.runprofile.schema import RunProfile, RunProfileWithPath


def file_sha256(path: Path) -> str:
    """Stable SHA256 of a single file. Empty string when missing."""
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def expert_override_diffs(
    profile: RunProfile, compiled: CompiledBundle
) -> dict[str, dict[str, Any]]:
    """Return ``{criterion_id: {code: {value, recommended_value, deviation_pct}}}``.

    Deviations are computed against the recommended values harvested
    from the spec templates. Only entries whose user value differs
    from the recommended value appear; the GUI uses these to render
    the "modified from recommended" badge and the audit MD prints
    them so out-of-bounds inputs (which require ``expert_override``)
    are obvious in the regulator-grade trail.
    """
    diffs: dict[str, dict[str, Any]] = {}
    for ov in compiled.overrides:
        if ov.user_value == ov.recommended_value:
            continue
        diffs.setdefault(ov.criterion_id, {})[ov.code] = {
            "value": ov.user_value,
            "recommended_value": ov.recommended_value,
            "deviation_pct": ov.deviation_pct,
            "out_of_bounds": ov.out_of_bounds,
        }
    return diffs


def build_scope_summary(
    profile: RunProfile, compiled: CompiledBundle
) -> dict[str, Any]:
    """Render the JSON blob persisted to ``dataset_snapshot.scope_summary``."""
    return {
        "qualification_mode": profile.scoring.qualification_mode,
        "weight_profile": profile.weight_profile,
        "scope": {
            "country_codes": list(profile.scope.countries),
            "smr_keys": list(profile.scope.smr_keys),
            "site_ids": list(profile.scope.site_ids),
            "site_status_in": list(profile.scope.site_status_in),
        },
        "fail_thresholds": profile.fail_thresholds,
        "expert_override": profile.expert_override,
        "expert_overrides": expert_override_diffs(profile, compiled),
    }


def dataset_meta_for_profile(
    *,
    profile_with_path: RunProfileWithPath,
    compiled: CompiledBundle,
    spec_dir: Path,
    n_sites_total: int | None = None,
    n_sites_screened_in: int | None = None,
    n_smrs: int | None = None,
    n_criteria_exclusionary: int | None = None,
    n_criteria_avoidance: int | None = None,
    n_criteria_ranking: int | None = None,
) -> DatasetMeta:
    """Return a :class:`DatasetMeta` ready for :func:`start_run`."""
    profile = profile_with_path.profile
    return DatasetMeta(
        rubric_file_path=str(spec_dir),
        n_sites_total=n_sites_total,
        n_sites_screened_in=n_sites_screened_in,
        n_smrs=n_smrs,
        n_criteria_exclusionary=n_criteria_exclusionary,
        n_criteria_avoidance=n_criteria_avoidance,
        n_criteria_ranking=n_criteria_ranking,
        weight_normalisation_profile=profile.weight_profile,
        run_profile_path=str(profile_with_path.path),
        run_profile_sha256=file_sha256(profile_with_path.path),
        spec_bundle_path=str(spec_dir),
        spec_bundle_sha256=bundle_sha256(compiled.criteria),
        n_countries_in_scope=len(profile.scope.countries),
        n_smrs_in_scope=len(profile.scope.smr_keys),
        scope_summary=build_scope_summary(profile, compiled),
    )


def render_provenance_md(meta: DatasetMeta) -> str:
    """Return the audit MD header block reused by every audit writer."""
    lines: list[str] = ["## Provenance", ""]
    if meta.run_profile_path:
        lines.append(f"- Run profile: `{meta.run_profile_path}`")
    if meta.run_profile_sha256:
        lines.append(f"- Run profile sha256: `{meta.run_profile_sha256}`")
    if meta.spec_bundle_path:
        lines.append(f"- Spec bundle: `{meta.spec_bundle_path}`")
    if meta.spec_bundle_sha256:
        lines.append(f"- Compiled bundle sha256: `{meta.spec_bundle_sha256}`")
    if meta.n_countries_in_scope is not None:
        lines.append(f"- Countries in scope: {meta.n_countries_in_scope}")
    if meta.n_smrs_in_scope is not None:
        lines.append(f"- SMRs in scope: {meta.n_smrs_in_scope}")
    if meta.scope_summary and meta.scope_summary.get("expert_overrides"):
        lines.append(
            "- Expert overrides: "
            f"{meta.scope_summary['expert_overrides']!r}"
        )
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "build_scope_summary",
    "dataset_meta_for_profile",
    "expert_override_diffs",
    "file_sha256",
    "render_provenance_md",
]
