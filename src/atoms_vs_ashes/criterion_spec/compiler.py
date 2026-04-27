# man_hours: 4.0
"""Deterministic compiler: ``(template + user fail_thresholds)`` → ``Criterion``.

The compiler is the only place that knows how to translate a
:class:`CriterionTemplate` into the runtime
:class:`atoms_vs_ashes.scoring.rubric.Criterion`. Two contracts:

1. **Parity**: with an empty ``fail_thresholds`` map every compiled
   criterion is structurally identical to today's
   :func:`load_rubric_bundle` output (same ``condition_expr`` strings on
   bands and fail_conditions, same ``score_range`` tuples, same
   ``weight_factor``). This is what guards the verbatim migration of the
   five rubric YAMLs.
2. **Targeted overrides**: when a user supplies a value in
   ``fail_thresholds[criterion_id][code]`` *and* the matching
   :class:`FailConditionSpec` carries a structured ``threshold`` block,
   the compiler regenerates *only* that fail_condition's
   ``condition_expr`` from ``"{metric} {op} {value}"``. Bands are never
   re-derived from threshold edits in this iteration (per plan §13 out
   of scope).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from atoms_vs_ashes.criterion_spec._band_recipes import bands_from_recipe
from atoms_vs_ashes.criterion_spec._compiler_helpers import (
    band_to_runtime,
    bundle_sha256,
    deviation_pct,
    normalise_weights,
    render_condition,
    sub_score_to_runtime,
)
from atoms_vs_ashes.criterion_spec.loader import TemplateBundle
from atoms_vs_ashes.criterion_spec.schema import (
    CriterionTemplate,
    FailConditionSpec,
    ThresholdSpec,
)
from atoms_vs_ashes.scoring.rubric import (
    Aggregation,
    Criterion,
    DbFields,
    FailCondition,
    QualityFloor,
)


@dataclass
class OverrideRecord:
    """Tracked diff vs. recommended for one user-supplied threshold."""

    criterion_id: str
    code: str
    metric: str
    op: str
    user_value: Any
    recommended_value: Any
    deviation_pct: float | None
    out_of_bounds: bool


@dataclass
class CompiledBundle:
    """Compiler output: criterion dict + provenance + override audit."""

    criteria: dict[str, Criterion]
    weights_normalised: dict[str, float]
    overrides: list[OverrideRecord]
    sha256: str
    spec_sha256: str


def compile_bundle(
    template_bundle: TemplateBundle,
    *,
    fail_thresholds: dict[str, dict[str, Any]] | None = None,
    weight_overrides: dict[str, int] | None = None,
    weight_profile: str = "baseline",
    expert_override: bool = False,
    smr_key: str | None = None,
    smr_grid_export_mw: float | None = None,
) -> CompiledBundle:
    """Compile templates + user fail_thresholds into a runtime bundle.

    Args:
        template_bundle: Output of
            :func:`atoms_vs_ashes.criterion_spec.loader.load_template_bundle`.
        fail_thresholds: ``{criterion_id: {code: value}}`` user override
            map. Anything missing falls back to the template's
            ``threshold.default_value`` (which equals
            ``recommended.value`` in the v1 templates).
        weight_overrides: ``{criterion_id: int}`` integer 1..10 weight
            overrides. Applied before normalisation.
        weight_profile: ``baseline | w_plus_20 | w_minus_20`` — same
            semantics as today's :func:`weight_normalisation`.
        expert_override: Allow out-of-bounds threshold values. Without
            this flag any out-of-bounds value raises :class:`ValueError`.

    Raises:
        ValueError: unknown criterion_id, unknown code, or out-of-bounds
            value when ``expert_override`` is False.
    """
    fail_thresholds = fail_thresholds or {}
    weight_overrides = weight_overrides or {}

    overrides: list[OverrideRecord] = []
    compiled: dict[str, Criterion] = {}

    for cid, template in template_bundle.by_id.items():
        crit_overrides = fail_thresholds.get(cid, {})
        weight = weight_overrides.get(cid, template.weight_factor)
        compiled[cid] = _compile_criterion(
            template,
            crit_overrides,
            weight_factor=weight,
            overrides_log=overrides,
            expert_override=expert_override,
            smr_key=smr_key,
            smr_grid_export_mw=smr_grid_export_mw,
        )

    _validate_unknown_overrides(template_bundle, fail_thresholds)

    weights = normalise_weights(compiled, profile=weight_profile)
    sha = bundle_sha256(compiled)

    return CompiledBundle(
        criteria=compiled,
        weights_normalised=weights,
        overrides=overrides,
        sha256=sha,
        spec_sha256=template_bundle.sha256,
    )


def _compile_criterion(
    template: CriterionTemplate,
    crit_overrides: dict[str, Any],
    *,
    weight_factor: int,
    overrides_log: list[OverrideRecord],
    expert_override: bool,
    smr_key: str | None,
    smr_grid_export_mw: float | None,
) -> Criterion:
    """Translate one :class:`CriterionTemplate` into a runtime ``Criterion``."""
    fail_conditions = [
        _compile_fail_condition(
            template.criterion_id,
            fc,
            crit_overrides,
            overrides_log=overrides_log,
            expert_override=expert_override,
            smr_key=smr_key,
        )
        for fc in template.fail_conditions
    ]
    if (
        template.band_recipe is not None
        and template.band_recipe.fail_code in crit_overrides
    ):
        raw = _resolve_code_override(
            crit_overrides, template.band_recipe.fail_code, smr_key
        )
    else:
        raw = None
    if (
        template.band_recipe is not None
        and raw is not None
        and isinstance(raw, (int, float))
    ):
        bspecs = bands_from_recipe(
            template,
            template.band_recipe,
            float(raw),
            smr_grid_export_mw=smr_grid_export_mw,
        )
        runtime_bands = [band_to_runtime(b) for b in bspecs]
    else:
        runtime_bands = [band_to_runtime(b) for b in template.bands]
    return Criterion(
        criterion_id=template.criterion_id,
        name=template.name,
        phases=list(template.phases),
        weight_factor=weight_factor,
        normalised_weight_pct=template.normalised_weight_pct,
        primary_metric=template.primary_metric,
        db_fields=DbFields(
            api=list(template.db_fields.api),
            llm=template.db_fields.llm,
        ),
        bands=runtime_bands,
        sub_scores=[sub_score_to_runtime(s) for s in template.sub_scores],
        aggregation=(
            Aggregation(
                method=template.aggregation.method,
                round_to=template.aggregation.round_to,
                cap_if_any_sub_score_below=(
                    dict(template.aggregation.cap_if_any_sub_score_below)
                    if template.aggregation.cap_if_any_sub_score_below
                    else None
                ),
            )
            if template.aggregation
            else None
        ),
        fail_conditions=fail_conditions,
        quality_floor=QualityFloor(
            low_quality_uncertainty_bands=(
                template.quality_floor.low_quality_uncertainty_bands
            )
        ),
    )


def _resolve_code_override(
    crit_overrides: dict[str, Any], code: str, smr_key: str | None
) -> Any:
    if code not in crit_overrides:
        return None
    v = crit_overrides[code]
    if smr_key and isinstance(v, dict) and v and all(isinstance(k, str) for k in v):
        if smr_key in v:
            return v[smr_key]
        if "" in v:
            return v[""]
        if len(v) == 1:
            return next(iter(v.values()))
    return v


def _compile_fail_condition(
    criterion_id: str,
    fc: FailConditionSpec,
    crit_overrides: dict[str, Any],
    *,
    overrides_log: list[OverrideRecord],
    expert_override: bool,
    smr_key: str | None = None,
) -> FailCondition:
    """Apply user override (if any) to a single fail_condition."""
    if fc.code in crit_overrides:
        user_value = _resolve_code_override(crit_overrides, fc.code, smr_key)
    else:
        user_value = None
    expr = fc.condition_expr

    if user_value is not None:
        if fc.threshold is None:
            raise ValueError(
                f"User override for {criterion_id}/{fc.code} but template "
                f"has no `threshold` block — code is not user-controllable."
            )
        if not expert_override and not fc.threshold.is_in_bounds(user_value):
            raise ValueError(
                f"Override {criterion_id}/{fc.code}={user_value!r} is "
                f"outside bounds {fc.threshold.bounds.model_dump()}; "
                f"set expert_override=true to bypass."
            )
        if fc.threshold_affects_expr:
            expr = render_condition(fc.threshold, user_value)
        overrides_log.append(
            _override_record(criterion_id, fc.code, fc.threshold, user_value)
        )

    return FailCondition(
        code=fc.code,
        action=fc.action,
        condition_expr=expr,
        descriptor=fc.descriptor,
        pass_mark=fc.pass_mark,
    )


def _override_record(
    criterion_id: str, code: str, spec: ThresholdSpec, value: Any
) -> OverrideRecord:
    rec = spec.recommended.value
    dev = deviation_pct(value, rec) if spec.kind == "numeric" else None
    return OverrideRecord(
        criterion_id=criterion_id,
        code=code,
        metric=spec.metric,
        op=spec.op,
        user_value=value,
        recommended_value=rec,
        deviation_pct=dev,
        out_of_bounds=not spec.is_in_bounds(value),
    )


def _validate_unknown_overrides(
    bundle: TemplateBundle,
    fail_thresholds: dict[str, dict[str, Any]],
) -> None:
    for cid, codes in fail_thresholds.items():
        template = bundle.by_id.get(cid)
        if template is None:
            raise ValueError(
                f"Unknown criterion_id '{cid}' in fail_thresholds"
            )
        known = {fc.code for fc in template.fail_conditions}
        if template.band_recipe is not None:
            known.add(template.band_recipe.fail_code)
        for code in codes:
            if code not in known:
                raise ValueError(
                    f"Unknown code '{code}' on criterion '{cid}' "
                    f"(known: {sorted(known)})"
                )


__all__ = [
    "CompiledBundle",
    "OverrideRecord",
    "compile_bundle",
]
