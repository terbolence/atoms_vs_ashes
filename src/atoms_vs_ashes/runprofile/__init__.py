# man_hours: 0.25
"""Run-profile package: schema + loader + persistence helpers.

A *run profile* (``config/run_profiles/<slug>.yaml``) is the user-
editable Layer-2 configuration for one execution of the scoring +
sensitivity pipeline. The schema is the contract between the GUI / CLI
and the engine.
"""

from atoms_vs_ashes.runprofile.loader import (
    LoadedRunProfile,
    load_run_profile,
    parse_run_profile,
    validate_against_db,
    validate_against_specs,
)
from atoms_vs_ashes.runprofile.persist import (
    build_scope_summary,
    dataset_meta_for_profile,
    expert_override_diffs,
    file_sha256,
    render_provenance_md,
)
from atoms_vs_ashes.runprofile.schema import (
    DbProfile,
    OutputBlock,
    QualificationMode,
    RunProfile,
    RunProfileWithPath,
    ScopeBlock,
    ScoringBlock,
    SensitivityBlock,
    SensitivityStage,
    SiteStatus,
    WeightProfile,
)

__all__ = [
    "DbProfile",
    "LoadedRunProfile",
    "OutputBlock",
    "QualificationMode",
    "RunProfile",
    "RunProfileWithPath",
    "ScopeBlock",
    "ScoringBlock",
    "SensitivityBlock",
    "SensitivityStage",
    "SiteStatus",
    "WeightProfile",
    "build_scope_summary",
    "dataset_meta_for_profile",
    "expert_override_diffs",
    "file_sha256",
    "load_run_profile",
    "parse_run_profile",
    "render_provenance_md",
    "validate_against_db",
    "validate_against_specs",
]
