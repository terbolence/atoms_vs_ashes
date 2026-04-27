# man_hours: 2.0
"""Static inventory for exclusionary and avoidance audit rules."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from atoms_vs_ashes.db import models
from atoms_vs_ashes.scoring.merge_context_derivations import (
    DERIVED_CONTEXT_NAMES,
    column_aliases,
)
from atoms_vs_ashes.scoring.rubric import Criterion, FailCondition, load_rubric_bundle

_IGNORED_NAMES = {"true", "false", "null", "None"}
_SITE_CONTEXT = {"site_area_ha", "elevation_m", "installed_capacity_mw", "country_code"}
_TABLE_MODELS = {
    "sites": models.Site,
    "site_natural_hazards": models.SiteNaturalHazards,
    "site_human_induced": models.SiteHumanHazards,
    "site_human_hazards": models.SiteHumanHazards,
    "site_radiological": models.SiteRadiological,
    "site_emergency": models.SiteEmergencyPlanning,
    "site_emergency_planning": models.SiteEmergencyPlanning,
    "site_infrastructure_v2": models.SiteInfrastructureV2,
    "site_socioeconomic": models.SiteInfrastructureV2,
}


@dataclass(frozen=True)
class AuditRule:
    """One exclusionary or avoidance rule to audit end-to-end."""

    code: str
    action: str
    criterion_id: str
    criterion_name: str
    condition_expr: str
    descriptor: str
    pass_mark: float | None
    db_fields: tuple[str, ...]
    expr_names: tuple[str, ...]
    missing_context_names: tuple[str, ...]
    missing_model_fields: tuple[str, ...]
    threshold_default: Any | None
    threshold_units: str | None
    threshold_op: str | None


def collect_audit_rules(
    rubric_dir: str | Path = "config/scoring_rubrics",
    threshold_metadata_path: str | Path = "config/scoring_specs/threshold_metadata.yaml",
) -> list[AuditRule]:
    """Return every YAML ``exclude`` / ``avoidance_penalty`` rule."""
    bundle = load_rubric_bundle(rubric_dir)
    thresholds = _load_thresholds(Path(threshold_metadata_path))
    rules: list[AuditRule] = []
    for criterion in bundle.values():
        for fc in criterion.fail_conditions:
            if fc.action not in {"exclude", "avoidance_penalty"}:
                continue
            meta = thresholds.get(criterion.criterion_id, {}).get(fc.code, {})
            rules.append(_build_rule(criterion, fc, meta))
    return sorted(rules, key=lambda r: (r.action != "exclude", r.criterion_id, r.code))


def _build_rule(
    criterion: Criterion,
    fc: FailCondition,
    threshold_meta: dict[str, Any],
) -> AuditRule:
    db_fields = tuple(criterion.db_fields.api)
    expr_names = tuple(sorted(_expression_names(fc.condition_expr)))
    available = _available_context_names(db_fields)
    missing_context = tuple(n for n in expr_names if n not in available)
    missing_model = tuple(f for f in db_fields if not _field_exists(f))
    return AuditRule(
        code=fc.code,
        action=fc.action,
        criterion_id=criterion.criterion_id,
        criterion_name=criterion.name,
        condition_expr=fc.condition_expr,
        descriptor=fc.descriptor,
        pass_mark=fc.pass_mark,
        db_fields=db_fields,
        expr_names=expr_names,
        missing_context_names=missing_context,
        missing_model_fields=missing_model,
        threshold_default=threshold_meta.get("default_value"),
        threshold_units=threshold_meta.get("units"),
        threshold_op=threshold_meta.get("op"),
    )


def _load_thresholds(path: Path) -> dict[str, dict[str, dict[str, Any]]]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _expression_names(expr: str) -> set[str]:
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        return set()
    return {
        node.id for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id not in _IGNORED_NAMES
    }


def _available_context_names(db_fields: tuple[str, ...]) -> set[str]:
    names = set(_SITE_CONTEXT) | set(DERIVED_CONTEXT_NAMES)
    for anchor in db_fields:
        _table, _dot, column = anchor.partition(".")
        if column:
            names.add(column)
            stripped = _strip_prefix(column)
            if stripped:
                names.add(stripped)
    return names


def _field_exists(anchor: str) -> bool:
    table, _dot, column = anchor.partition(".")
    model = _TABLE_MODELS.get(table)
    if model is None or not column:
        return False
    if hasattr(model, column):
        return True
    stripped = _strip_prefix(column)
    if stripped and hasattr(model, stripped):
        return True
    return any(hasattr(model, alias) for alias in column_aliases(table, column))


def _strip_prefix(column: str) -> str | None:
    parts = column.split("_", 1)
    if len(parts) == 2 and len(parts[0]) in {4, 5} and parts[0][:2].isalpha():
        if parts[0][2:].isdigit():
            return parts[1]
    return None
