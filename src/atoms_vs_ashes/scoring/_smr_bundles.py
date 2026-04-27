# man_hours: 1.0
"""Build per-SMR compiled criterion bundles when overrides are SMR-scoped."""

from __future__ import annotations

from atoms_vs_ashes.criterion_spec.compiler import compile_bundle
from atoms_vs_ashes.criterion_spec.loader import TemplateBundle
from atoms_vs_ashes.db.models import SmrDesign
from atoms_vs_ashes.runprofile.schema import RunProfile
from atoms_vs_ashes.scoring.rubric import Criterion


def smr_aware_criteria_bundles(
    template_bundle: TemplateBundle,
    profile: RunProfile,
    smrs: list[SmrDesign],
) -> dict[str, dict[str, Criterion]]:
    """One ``dict[str, Criterion]`` per ``smr_key`` (required export + thresholds)."""
    out: dict[str, dict[str, Criterion]] = {}
    for s in smrs:
        mwe = float(s.capacity_mwe) if s.capacity_mwe is not None else None
        out[s.smr_key] = compile_bundle(
            template_bundle,
            fail_thresholds=dict(profile.fail_thresholds),
            weight_overrides=profile.scoring.weight_overrides,
            weight_profile=profile.weight_profile,
            expert_override=profile.expert_override,
            smr_key=s.smr_key,
            smr_grid_export_mw=mwe,
        ).criteria
    return out


__all__ = ["smr_aware_criteria_bundles"]
