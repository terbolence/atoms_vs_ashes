"""Extract run-profile-tunable threshold values from a stored scoring snapshot.

The site / country bundle JSON carries a ``provenance`` block that records
the criterion thresholds that were active when the parent scoring run was
executed. Downstream renderers (site profile prose, country profile prose,
report tables) read this block instead of importing a Python constant, so a
user override of a UI-tunable threshold (e.g. NH-02 E1 screening radius)
propagates end-to-end without code changes.

Today only NH-02 E1 is wired (per v1.03 Phase 1, feedback #104 + #105). The
helper is generic so adding the next UI-tunable threshold is a one-line
extension.

Resolution order
----------------
1. Read the ``CompiledScoringSnapshot`` linked to the run via
   ``ScoringRunSnapshot``; extract the threshold from the stored compiled
   bundle's ``fail_conditions[<code>].condition_expr``.
2. If no snapshot is linked (older runs predating snapshot persistence, or
   ad-hoc bundle exports against a run that was never committed), fall back
   to ``config/scoring_specs/threshold_metadata.yaml`` ``default_value``.
3. If neither source resolves, return ``None``; the renderer is expected to
   degrade gracefully (e.g. by omitting the verdict line).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models_scoring_definitions import (
    CompiledScoringSnapshot,
    ScoringRunSnapshot,
)


_THRESHOLD_METADATA_PATH = (
    Path(__file__).resolve().parents[3]
    / "config"
    / "scoring_specs"
    / "threshold_metadata.yaml"
)

_LT_PATTERN = re.compile(r"<\s*([0-9]+(?:\.[0-9]+)?)")


def _threshold_from_condition_expr(expr: str | None) -> float | None:
    """Parse ``nearest_fault_km < 8.0`` style expressions to ``8.0``."""

    if not expr:
        return None
    match = _LT_PATTERN.search(expr)
    if match is None:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _threshold_from_snapshot(
    session: Session, *, run_id: str, criterion_id: str, fc_code: str
) -> float | None:
    """Pull the threshold from the compiled-scoring snapshot for this run."""

    link = session.get(ScoringRunSnapshot, run_id)
    if link is None:
        return None
    snap = session.get(CompiledScoringSnapshot, link.snapshot_id)
    if snap is None or not snap.bundles_by_smr:
        return None
    for bundle in snap.bundles_by_smr.values():
        criterion = bundle.get(criterion_id)
        if not isinstance(criterion, dict):
            continue
        for fc in criterion.get("fail_conditions", []) or []:
            if isinstance(fc, dict) and fc.get("code") == fc_code:
                value = _threshold_from_condition_expr(fc.get("condition_expr"))
                if value is not None:
                    return value
    return None


def _threshold_from_metadata_yaml(criterion_id: str, fc_code: str) -> float | None:
    """Fall back to the norm-default value in ``threshold_metadata.yaml``.

    Layout is ``<criterion_id>: { <fc_code>: { default_value: ... } }``.
    """

    try:
        data = yaml.safe_load(_THRESHOLD_METADATA_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    if not isinstance(data, dict):
        return None
    criterion_block = data.get(criterion_id)
    if not isinstance(criterion_block, dict):
        return None
    fc_block = criterion_block.get(fc_code)
    if not isinstance(fc_block, dict):
        return None
    value = fc_block.get("default_value")
    return float(value) if value is not None else None


def nh02_e1_threshold_km(session: Session, *, run_id: str) -> float | None:
    """Return the NH-02 E1 (Surface Rupture) screening radius for this run."""

    snapshot_value = _threshold_from_snapshot(
        session, run_id=run_id, criterion_id="NH-02", fc_code="E1",
    )
    if snapshot_value is not None:
        return snapshot_value
    return _threshold_from_metadata_yaml("NH-02", "E1")


def run_profile_provenance(session: Session, *, run_id: str) -> dict[str, Any]:
    """Compose the provenance block surfaced on every site / country bundle.

    Extend this function (not its callers) when adding the next UI-tunable
    threshold.
    """

    return {
        "nh02_e1_threshold_km": nh02_e1_threshold_km(session, run_id=run_id),
    }


__all__ = [
    "nh02_e1_threshold_km",
    "run_profile_provenance",
]
