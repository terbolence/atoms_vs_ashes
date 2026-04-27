# man_hours: 1.0
"""Persist compiled scoring-definition snapshots for reproducible runs."""

from __future__ import annotations

import hashlib
import json

from sqlalchemy.orm import Session

from atoms_vs_ashes.criterion_spec.compiler import compile_bundle
from atoms_vs_ashes.criterion_spec.db_loader import db_definition_revision
from atoms_vs_ashes.criterion_spec.db_loader import load_template_bundle_from_db
from atoms_vs_ashes.db.models_scoring_definitions import (
    CompiledScoringSnapshot,
    ScoringRunSnapshot,
)
from atoms_vs_ashes.scoring.rubric import Criterion


def _bundle_payload(bundles_by_smr: dict[str, dict[str, Criterion]]) -> dict:
    return {
        smr_key: {
            cid: criterion.model_dump(mode="json")
            for cid, criterion in sorted(bundle.items())
        }
        for smr_key, bundle in sorted(bundles_by_smr.items())
    }


def compiled_snapshot_hash(
    bundles_by_smr: dict[str, dict[str, Criterion]],
    threshold_overrides: dict | None = None,
) -> tuple[str, dict]:
    payload = {
        "bundles_by_smr": _bundle_payload(bundles_by_smr),
        "threshold_overrides": threshold_overrides or {},
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest(), payload


def persist_compiled_scoring_snapshot(
    session: Session,
    *,
    run_id: str,
    bundles_by_smr: dict[str, dict[str, Criterion]],
    threshold_overrides: dict | None = None,
) -> str:
    """Store compiled criteria once and link the run to the snapshot."""
    compiled_hash, payload = compiled_snapshot_hash(
        bundles_by_smr,
        threshold_overrides=threshold_overrides,
    )
    revision, _ = db_definition_revision(session)
    snapshot_id = f"scdef-{compiled_hash[:16]}"
    if session.get(CompiledScoringSnapshot, snapshot_id) is None:
        session.add(
            CompiledScoringSnapshot(
                snapshot_id=snapshot_id,
                compiled_sha256=compiled_hash,
                definition_revision=revision,
                threshold_overrides=payload["threshold_overrides"],
                bundles_by_smr=payload["bundles_by_smr"],
            )
        )
    session.merge(ScoringRunSnapshot(run_id=run_id, snapshot_id=snapshot_id))
    session.flush()
    return snapshot_id


def load_bundle_for_run_snapshot(
    session: Session,
    *,
    parent_run_id: str | None,
    weight_profile: str,
    rubric_dir: str,
) -> tuple[dict[str, Criterion], str | None]:
    """Load the compiled bundle used by the parent run, falling back to DB compile."""
    if parent_run_id:
        link = session.get(ScoringRunSnapshot, parent_run_id)
        if link is not None:
            snap = session.get(CompiledScoringSnapshot, link.snapshot_id)
            if snap is not None and snap.bundles_by_smr:
                first = next(iter(snap.bundles_by_smr.values()))
                bundle = {
                    cid: Criterion.model_validate(data)
                    for cid, data in first.items()
                }
                return bundle, snap.snapshot_id

    templates = load_template_bundle_from_db(session, spec_dir=rubric_dir)
    bundle = compile_bundle(
        templates, weight_profile=weight_profile, expert_override=True
    ).criteria
    return bundle, None


def link_run_to_snapshot(
    session: Session, *, run_id: str, snapshot_id: str | None
) -> None:
    if snapshot_id is not None:
        session.merge(ScoringRunSnapshot(run_id=run_id, snapshot_id=snapshot_id))


__all__ = [
    "compiled_snapshot_hash",
    "link_run_to_snapshot",
    "load_bundle_for_run_snapshot",
    "persist_compiled_scoring_snapshot",
]
