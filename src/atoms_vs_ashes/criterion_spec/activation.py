# man_hours: 1.2
"""Load and apply ``config/scoring_specs/criterion_activation.yaml``.

Single source of truth for whether a criterion participates in scoring,
sensitivity, and result charts. Criteria not listed default to ``active: true``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

CRITERION_ACTIVATION_FILENAME = "criterion_activation.yaml"


class CriterionActivationEntry(BaseModel):
    """Per-criterion activation metadata from the registry sidecar."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    active: bool = True
    inactive_reason: str | None = None
    pending_implementation: str | None = None
    required_improvement: str | None = None


class CriterionActivationRegistry(BaseModel):
    """Validated activation registry."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    criteria: dict[str, CriterionActivationEntry] = Field(default_factory=dict)

    def entry_for(self, criterion_id: str) -> CriterionActivationEntry:
        return self.criteria.get(
            criterion_id,
            CriterionActivationEntry(active=True),
        )

    def inactive_ids(self) -> frozenset[str]:
        return frozenset(
            cid for cid, e in self.criteria.items() if not e.active
        )


def _read_yaml(path: Path) -> dict[str, Any]:
    with open(path) as fh:
        return yaml.safe_load(fh) or {}


def load_activation_registry(spec_dir: str | Path) -> CriterionActivationRegistry:
    """Load ``criterion_activation.yaml``; empty registry if file missing."""
    path = Path(spec_dir) / CRITERION_ACTIVATION_FILENAME
    if not path.is_file():
        return CriterionActivationRegistry()
    data = _read_yaml(path)
    if not isinstance(data, dict):
        raise ValueError(
            f"{CRITERION_ACTIVATION_FILENAME} must be a mapping; got {type(data)}"
        )
    raw_criteria = data.get("criteria") or {}
    if not isinstance(raw_criteria, dict):
        raise ValueError(
            f"{CRITERION_ACTIVATION_FILENAME} 'criteria' must be a mapping"
        )
    parsed: dict[str, CriterionActivationEntry] = {}
    for cid, row in raw_criteria.items():
        if not isinstance(row, dict):
            raise ValueError(
                f"{CRITERION_ACTIVATION_FILENAME}: criteria[{cid!r}] must be a mapping"
            )
        parsed[str(cid)] = CriterionActivationEntry.model_validate(row)
    return CriterionActivationRegistry(criteria=parsed)


def validate_activation_registry(
    registry: CriterionActivationRegistry,
    criterion_ids: set[str],
) -> None:
    """Ensure every registry key exists in the rubric bundle."""
    unknown = set(registry.criteria) - criterion_ids
    if unknown:
        raise ValueError(
            f"{CRITERION_ACTIVATION_FILENAME} lists unknown criterion_id(s): "
            f"{sorted(unknown)}"
        )


def apply_activation_to_criterion(
    criterion: Any,
    entry: CriterionActivationEntry,
) -> Any:
    """Return a copy of ``criterion`` with activation fields set (Pydantic)."""
    return criterion.model_copy(
        update={
            "active": entry.active,
            "inactive_reason": entry.inactive_reason,
            "pending_implementation": entry.pending_implementation,
            "required_improvement": entry.required_improvement,
        },
    )


def filter_active_criterion_ids(
    ordered_ids: list[str],
    bundle: dict[str, Any],
) -> list[str]:
    """Drop inactive criteria while preserving order."""
    return [
        cid
        for cid in ordered_ids
        if bundle.get(cid) is not None and getattr(bundle[cid], "active", True)
    ]


def filter_active_from_snapshot_data(
    ordered_ids: list[str],
    bundle_data: dict[str, dict[str, Any]],
    *,
    fallback_inactive: frozenset[str] | None = None,
) -> list[str]:
    """Filter using serialized snapshot criterion dicts (``active`` key).

    When ``active`` is absent (pre-registry snapshots), use
    ``fallback_inactive`` from the current registry so charts stay aligned
    with today's deactivation policy.
    """
    inactive = fallback_inactive or frozenset()
    out: list[str] = []
    for cid in ordered_ids:
        row = bundle_data.get(cid)
        if row is None:
            continue
        if "active" in row:
            if row["active"]:
                out.append(cid)
        elif cid not in inactive:
            out.append(cid)
    return out


def default_inactive_criterion_ids(
    spec_dir: str | Path | None = None,
) -> frozenset[str]:
    """Inactive IDs from the repo registry (cached)."""
    root = Path(spec_dir or "config/scoring_specs")
    reg = load_activation_registry(root)
    return reg.inactive_ids()


__all__ = [
    "CRITERION_ACTIVATION_FILENAME",
    "CriterionActivationEntry",
    "CriterionActivationRegistry",
    "apply_activation_to_criterion",
    "filter_active_criterion_ids",
    "default_inactive_criterion_ids",
    "filter_active_from_snapshot_data",
    "load_activation_registry",
    "validate_activation_registry",
]
