# man_hours: 4.5
"""Compile spec templates plus user controls into runtime criteria.

Structured fail-threshold edits regenerate the matching fail-condition
expression. Criteria that declare ``band_recipe`` also rebuild their
0-10 bands from the same threshold pivot, including the recommended
default when the user has not overridden it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from atoms_vs_ashes.criterion_spec._band_recipes import (
    _metric_for_recipe,
    bands_from_recipe,
)
from atoms_vs_ashes.criterion_spec._compiler_helpers import (
    band_to_runtime,
    bundle_sha256,
    deviation_pct,
    normalise_weights,
    render_condition,
    sub_score_to_runtime,
)
from atoms_vs_ashes.criterion_spec._excl_from_pivot import excl_expr_from_recipe
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
    """Compiler output: criterion dict + provenance + override audit.

    ``derived_exclusion_exprs`` records the rewritten hard-exclusion
    ``condition_expr`` for each criterion that opted in to single-pivot
    exclusion via ``FailConditionSpec.derive_expr_from_recipe = True``.
    The compiler regenerates these from the same pivot that drives the
    0-10 bands, so the band-5 boundary and the hard exclusion can never
    drift apart at runtime. Criteria that did not opt in are absent.
    """

    criteria: dict[str, Criterion]
    weights_normalised: dict[str, float]
    overrides: list[OverrideRecord]
    sha256: str
    spec_sha256: str
    derived_exclusion_exprs: dict[str, str] = field(default_factory=dict)


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
    """Compile templates + user fail_thresholds into a runtime bundle."""
    fail_thresholds = fail_thresholds or {}
    weight_overrides = weight_overrides or {}

    _validate_template_exclusion_drift(template_bundle)

    overrides: list[OverrideRecord] = []
    compiled: dict[str, Criterion] = {}
    derived_exprs: dict[str, str] = {}

    for cid, template in template_bundle.by_id.items():
        crit_overrides = fail_thresholds.get(cid, {})
        weight = weight_overrides.get(cid, template.weight_factor)
        criterion, derived_expr = _compile_criterion(
            template,
            crit_overrides,
            weight_factor=weight,
            overrides_log=overrides,
            expert_override=expert_override,
            smr_key=smr_key,
            smr_grid_export_mw=smr_grid_export_mw,
        )
        compiled[cid] = criterion
        if derived_expr is not None:
            derived_exprs[cid] = derived_expr

    _validate_unknown_overrides(template_bundle, fail_thresholds)

    weights = normalise_weights(compiled, profile=weight_profile)
    sha = bundle_sha256(compiled)

    return CompiledBundle(
        criteria=compiled,
        weights_normalised=weights,
        overrides=overrides,
        sha256=sha,
        spec_sha256=template_bundle.sha256,
        derived_exclusion_exprs=derived_exprs,
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
) -> tuple[Criterion, str | None]:
    """Translate one :class:`CriterionTemplate` into a runtime ``Criterion``.

    Returns ``(criterion, derived_exclusion_expr)``. The second element
    is the rewritten hard-exclusion ``condition_expr`` when this
    criterion's recipe-linked exclusionary fail_condition has opted in
    to single-pivot derivation; ``None`` otherwise.
    """
    raw = _band_recipe_pivot(template, crit_overrides, smr_key)
    derived_expr = _derive_exclusion_expr(template, raw)
    fail_conditions = [
        _compile_fail_condition(
            template.criterion_id,
            fc,
            crit_overrides,
            overrides_log=overrides_log,
            expert_override=expert_override,
            smr_key=smr_key,
            derived_excl_expr=(
                derived_expr
                if (
                    template.band_recipe is not None
                    and fc.code == template.band_recipe.fail_code
                    and fc.action == "exclude"
                    and fc.derive_expr_from_recipe
                )
                else None
            ),
        )
        for fc in template.fail_conditions
    ]
    if template.band_recipe is not None and isinstance(raw, (int, float)):
        bspecs = bands_from_recipe(
            template,
            template.band_recipe,
            float(raw),
            smr_grid_export_mw=smr_grid_export_mw,
        )
        runtime_bands = [band_to_runtime(b) for b in bspecs]
    else:
        runtime_bands = [band_to_runtime(b) for b in template.bands]
    extra = template.model_extra or {}
    criterion = Criterion(
        criterion_id=template.criterion_id,
        name=template.name,
        phases=list(template.phases),
        weight_factor=weight_factor,
        normalised_weight_pct=template.normalised_weight_pct,
        weight_factors=extra.get("weight_factors"),
        weight_basis_source=extra.get("weight_basis_source"),
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
        notes=template.notes,
    )
    return criterion, derived_expr


def _derive_exclusion_expr(
    template: CriterionTemplate, pivot: Any
) -> str | None:
    """Return the recipe-derived hard-exclusion ``condition_expr`` or ``None``.

    ``None`` when any of the following hold:

    * the criterion has no ``band_recipe``;
    * the resolved pivot is not numeric;
    * no matching exclusionary fail_condition exists;
    * the matching fail_condition has ``derive_expr_from_recipe=False``
      (the default — opt-in protects compound exclusions like EP-01 E8);
    * the recipe kind is composite and rejects automatic derivation.
    """
    if template.band_recipe is None or not isinstance(pivot, (int, float)):
        return None
    excl_fc = next(
        (
            fc
            for fc in template.fail_conditions
            if fc.code == template.band_recipe.fail_code
            and fc.action == "exclude"
        ),
        None,
    )
    if excl_fc is None or not excl_fc.derive_expr_from_recipe:
        return None
    metric = _metric_for_recipe(template, template.band_recipe)
    try:
        return excl_expr_from_recipe(
            template.band_recipe.kind, metric, float(pivot)
        )
    except ValueError as exc:
        raise ValueError(
            f"Criterion {template.criterion_id}: band_recipe.kind "
            f"{template.band_recipe.kind!r} is wired to an exclusionary "
            f"fail_condition ({excl_fc.code}) with "
            "derive_expr_from_recipe=true, but the recipe kind does not "
            "support automatic exclusion derivation. Either change the "
            "recipe kind or clear the derive_expr_from_recipe flag."
        ) from exc


def _band_recipe_pivot(
    template: CriterionTemplate,
    crit_overrides: dict[str, Any],
    smr_key: str | None,
) -> Any:
    if template.band_recipe is None:
        return None
    code = template.band_recipe.fail_code
    raw = _resolve_code_override(crit_overrides, code, smr_key)
    if raw is not None:
        return raw
    if template.band_recipe.score5_pivot is not None:
        return template.band_recipe.score5_pivot
    for fc in template.fail_conditions:
        if fc.code == code and fc.threshold is not None:
            return fc.threshold.default_value
    return None


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
    derived_excl_expr: str | None = None,
) -> FailCondition:
    """Apply user override (if any) to a single fail_condition.

    When ``derived_excl_expr`` is supplied (set by ``_compile_criterion``
    only for recipe-linked exclusionary codes that opted in to
    single-pivot derivation) it wins over both the YAML ``condition_expr``
    and any threshold-rendered expression: the same pivot that drives
    the bands also drives the exclusion.
    """
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

    if derived_excl_expr is not None:
        expr = derived_excl_expr

    return FailCondition(
        code=fc.code,
        action=fc.action,
        condition_expr=expr,
        descriptor=fc.descriptor,
        pass_mark=fc.pass_mark,
        null_pass_condition_expr=fc.null_pass_condition_expr,
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


def _validate_template_exclusion_drift(bundle: TemplateBundle) -> None:
    """Reject template YAML where the hand-written exclusion expression
    disagrees with what the band_recipe would derive.

    Run once per :func:`compile_bundle` invocation, against the template
    as written (no user overrides). Catches the failure mode this guard
    was built for: a YAML author edits ``score5_pivot`` but forgets to
    keep ``condition_expr`` in sync. Only fires for exclusionary
    fail_conditions that opted in via ``derive_expr_from_recipe=true``;
    composites and compound expressions (which keep their hand-written
    form) are untouched.
    """
    for cid, template in bundle.by_id.items():
        if template.band_recipe is None:
            continue
        excl_fc = next(
            (
                fc
                for fc in template.fail_conditions
                if fc.code == template.band_recipe.fail_code
                and fc.action == "exclude"
                and fc.derive_expr_from_recipe
            ),
            None,
        )
        if excl_fc is None:
            continue
        pivot = _template_pivot(template)
        if not isinstance(pivot, (int, float)):
            raise ValueError(
                f"{cid}/{excl_fc.code}: derive_expr_from_recipe=true but "
                "no numeric pivot is declared on band_recipe.score5_pivot "
                "or threshold.default_value."
            )
        metric = _metric_for_recipe(template, template.band_recipe)
        expected = excl_expr_from_recipe(
            template.band_recipe.kind, metric, float(pivot)
        )
        actual = excl_fc.condition_expr.strip()
        if actual != expected:
            raise ValueError(
                f"Drift detected on {cid}/{excl_fc.code}: stored "
                f"condition_expr {actual!r} does not match the expression "
                f"derived from the score-5 pivot {pivot!r} ({expected!r}). "
                "Edit the YAML so they agree, or clear "
                "derive_expr_from_recipe on the fail_condition."
            )


def _template_pivot(template: CriterionTemplate) -> Any:
    """Return the template-as-written pivot (no overrides).

    Mirrors :func:`_band_recipe_pivot` but only looks at fields stored
    on the template itself — used by the drift guard to validate YAML
    self-consistency before any user input is applied.
    """
    if template.band_recipe is None:
        return None
    if template.band_recipe.score5_pivot is not None:
        return template.band_recipe.score5_pivot
    for fc in template.fail_conditions:
        if fc.code == template.band_recipe.fail_code and fc.threshold is not None:
            return fc.threshold.default_value
    return None


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
