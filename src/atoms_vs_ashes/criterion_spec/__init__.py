# man_hours: 0.25
"""Two-layer criterion spec: frozen templates + user fail thresholds.

Public entry points:

- :func:`load_template_bundle` — read ``config/scoring_specs/*.yaml``.
- :func:`compile_bundle` — produce a runtime ``Criterion`` dict + hashes.
- :class:`CriterionTemplate` / :class:`ThresholdSpec` — schema models
  the GUI / preview service introspect for recommended values, sources,
  bounds.
"""

from atoms_vs_ashes.criterion_spec._compiler_helpers import (
    bundle_sha256,
    normalise_weights,
)
from atoms_vs_ashes.criterion_spec.compiler import (
    CompiledBundle,
    OverrideRecord,
    compile_bundle,
)
from atoms_vs_ashes.criterion_spec.loader import (
    TemplateBundle,
    canonical_template_json,
    load_template_bundle,
    load_template_file,
)
from atoms_vs_ashes.criterion_spec.preview import (
    BandPreview,
    CriterionPreview,
    FailConditionPreview,
    PreviewBundle,
    build_preview,
)
from atoms_vs_ashes.criterion_spec.schema import (
    AggregationSpec,
    BandKind,
    BandSpec,
    CriterionTemplate,
    DbFieldsSpec,
    FailConditionSpec,
    QualityFloorSpec,
    RecommendedValue,
    SubScoreSpec,
    TemplateFile,
    ThresholdBounds,
    ThresholdSpec,
)

__all__ = [
    "AggregationSpec",
    "BandKind",
    "BandPreview",
    "BandSpec",
    "CompiledBundle",
    "CriterionPreview",
    "CriterionTemplate",
    "DbFieldsSpec",
    "FailConditionPreview",
    "FailConditionSpec",
    "OverrideRecord",
    "PreviewBundle",
    "QualityFloorSpec",
    "RecommendedValue",
    "SubScoreSpec",
    "TemplateBundle",
    "TemplateFile",
    "ThresholdBounds",
    "ThresholdSpec",
    "build_preview",
    "bundle_sha256",
    "canonical_template_json",
    "compile_bundle",
    "load_template_bundle",
    "load_template_file",
    "normalise_weights",
]
