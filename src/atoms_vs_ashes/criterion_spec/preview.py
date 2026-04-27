# man_hours: 3.0
"""DB-free preview of how a :class:`RunProfile` lands on the rubric.

Implements §7's ``score preview`` and ``GET /preview`` endpoint:

- Compiles ``config/scoring_specs/`` with the user's ``fail_thresholds``
  and ``weight_overrides``.
- Returns a structured :class:`PreviewBundle` containing the scoring
  matrix per criterion (band edges, descriptors, score ranges), the
  pass mark, the (un-normalised + normalised) weights, the resolved
  exclusionary / avoidance thresholds with their recommended-value
  metadata, and a ``diff_vs_recommended`` block listing every override
  that changed a value.
- Surfaces validation warnings (unknown criterion/code, out-of-bounds
  values) so the GUI can render them inline above the editor without
  hitting Postgres.

The output is intentionally JSON-serialisable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from atoms_vs_ashes.criterion_spec._preview_helpers import (
    diff_vs_recommended,
    override_for,
    pass_mark_lookup,
    safe_thresholds,
    validation_warnings,
)
from atoms_vs_ashes.criterion_spec.compiler import (
    CompiledBundle,
    OverrideRecord,
    compile_bundle,
)
from atoms_vs_ashes.criterion_spec.loader import TemplateBundle
from atoms_vs_ashes.criterion_spec.schema import (
    CriterionTemplate,
    FailConditionSpec,
)
from atoms_vs_ashes.runprofile.schema import RunProfile


@dataclass
class BandPreview:
    """One band row as the GUI's threshold editor renders it."""

    score_range: tuple[int, int]
    descriptor: str
    condition_expr: str


@dataclass
class FailConditionPreview:
    """Compiled view of a single E/A code, with recommended-value metadata."""

    code: str
    action: str
    metric: str
    op: str
    value: Any
    units: str | None
    label: str | None
    condition_expr: str
    recommended_value: Any
    recommended_rationale: str | None
    recommended_sources: list[str]
    bounds_min: float | None
    bounds_max: float | None
    user_editable: bool
    modified_from_recommended: bool
    deviation_pct: float | None
    out_of_bounds: bool


@dataclass
class CriterionPreview:
    """One criterion's full editor row: weight, bands, fail codes."""

    criterion_id: str
    name: str
    band_kind: str | None
    primary_metric: str | None
    weight_factor: int
    weight_normalised: float
    pass_mark: float
    is_exclusionary: bool
    exclusion_pass_mark: float | None
    bands: list[BandPreview]
    fail_codes: list[FailConditionPreview]


@dataclass
class PreviewBundle:
    """Top-level preview payload — JSON-serialisable, no DB hits."""

    spec_dir: str
    spec_sha256: str
    compiled_sha256: str
    weight_profile: str
    qualification_mode: str
    criteria: list[CriterionPreview]
    diff_vs_recommended: list[dict[str, Any]]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _fail_condition_preview(
    template: CriterionTemplate,
    fc: FailConditionSpec,
    overrides: list[OverrideRecord],
    runtime_expr: str,
) -> FailConditionPreview:
    spec = fc.threshold
    user_editable = spec is not None
    ov = (
        override_for(template.criterion_id, fc.code, overrides)
        if user_editable
        else None
    )
    rec = spec.recommended.value if user_editable else None
    value = (ov.user_value if ov else (rec if user_editable else None))
    sources = list(spec.recommended.sources) if user_editable else []
    bounds_min = (
        float(spec.bounds.min)
        if user_editable and spec.bounds.min is not None
        else None
    )
    bounds_max = (
        float(spec.bounds.max)
        if user_editable and spec.bounds.max is not None
        else None
    )
    return FailConditionPreview(
        code=fc.code,
        action=fc.action,
        metric=(spec.metric if user_editable else ""),
        op=(spec.op if user_editable else ""),
        value=value,
        units=(spec.units if user_editable else None),
        label=(spec.label if user_editable else None),
        condition_expr=runtime_expr,
        recommended_value=rec,
        recommended_rationale=(
            spec.recommended.rationale if user_editable else None
        ),
        recommended_sources=sources,
        bounds_min=bounds_min,
        bounds_max=bounds_max,
        user_editable=user_editable,
        modified_from_recommended=bool(ov and ov.user_value != ov.recommended_value),
        deviation_pct=(ov.deviation_pct if ov else None),
        out_of_bounds=bool(ov and ov.out_of_bounds),
    )


def _criterion_preview(
    template: CriterionTemplate,
    compiled: CompiledBundle,
    *,
    pass_mark_default: float,
) -> CriterionPreview:
    runtime = compiled.criteria[template.criterion_id]
    bands = [
        BandPreview(
            score_range=tuple(b.score_range),
            descriptor=b.descriptor,
            condition_expr=b.condition_expr,
        )
        for b in runtime.bands
    ]
    fail_codes: list[FailConditionPreview] = [
        _fail_condition_preview(
            template, fc, compiled.overrides, runtime_fc.condition_expr
        )
        for fc, runtime_fc in zip(template.fail_conditions, runtime.fail_conditions)
    ]
    exclude_fcs = [fc for fc in template.fail_conditions if fc.action == "exclude"]
    is_exclusionary = bool(exclude_fcs)
    exclusion_pass_mark: float | None = None
    if is_exclusionary:
        pms = [float(fc.pass_mark) for fc in exclude_fcs if fc.pass_mark is not None]
        exclusion_pass_mark = pms[0] if pms else None
    return CriterionPreview(
        criterion_id=template.criterion_id,
        name=template.name,
        band_kind=template.band_kind,
        primary_metric=template.primary_metric,
        weight_factor=runtime.weight_factor,
        weight_normalised=compiled.weights_normalised.get(
            template.criterion_id, 0.0
        ),
        pass_mark=pass_mark_default,
        is_exclusionary=is_exclusionary,
        exclusion_pass_mark=exclusion_pass_mark,
        bands=bands,
        fail_codes=fail_codes,
    )


def build_preview(
    template_bundle: TemplateBundle,
    profile: RunProfile,
    *,
    spec_dir: str,
) -> PreviewBundle:
    """Compile the spec + profile into a JSON-ready preview payload.

    Failures during compilation (unknown codes / criterion ids,
    out-of-bounds values without ``expert_override``) become user-facing
    ``warnings`` so the GUI can keep rendering. When the user-supplied
    overrides cause a hard error we fall back to a no-overrides baseline
    so the editor still has something to show.
    """
    warnings = validation_warnings(template_bundle, profile)
    safe_th = safe_thresholds(template_bundle, profile)
    try:
        compiled = compile_bundle(
            template_bundle,
            fail_thresholds=safe_th,
            weight_overrides=profile.scoring.weight_overrides,
            weight_profile=profile.weight_profile,
            expert_override=profile.expert_override,
        )
    except ValueError as exc:
        warnings.append(f"compile_failed={exc}")
        compiled = compile_bundle(
            template_bundle, weight_profile=profile.weight_profile
        )
    pass_marks = pass_mark_lookup(template_bundle)
    criteria = [
        _criterion_preview(
            template_bundle.by_id[cid],
            compiled,
            pass_mark_default=pass_marks.get(cid, 5.0),
        )
        for cid in sorted(template_bundle.by_id)
    ]
    return PreviewBundle(
        spec_dir=spec_dir,
        spec_sha256=template_bundle.sha256,
        compiled_sha256=compiled.sha256,
        weight_profile=profile.weight_profile,
        qualification_mode=profile.scoring.qualification_mode,
        criteria=criteria,
        diff_vs_recommended=diff_vs_recommended(compiled),
        warnings=warnings,
    )


__all__ = [
    "BandPreview",
    "CriterionPreview",
    "FailConditionPreview",
    "PreviewBundle",
    "build_preview",
]
