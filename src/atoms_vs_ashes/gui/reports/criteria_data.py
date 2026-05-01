"""Data collector for the Site Selection Criteria PDF."""

from __future__ import annotations

from atoms_vs_ashes.gui._data import build_live_preview
from atoms_vs_ashes.gui.reports.models import CriteriaReport
from atoms_vs_ashes.runprofile.schema import RunProfile


def build_criteria_report(profile: RunProfile) -> CriteriaReport:
    """Return the active compiled criteria preview as a report payload."""
    preview = build_live_preview(profile, profile.spec_dir)
    return CriteriaReport(
        spec_dir=preview.spec_dir,
        compiled_sha256=preview.compiled_sha256,
        weight_profile=preview.weight_profile,
        qualification_mode=preview.qualification_mode,
        criteria=preview.criteria,
        warnings=list(preview.warnings),
    )


__all__ = ["build_criteria_report"]

