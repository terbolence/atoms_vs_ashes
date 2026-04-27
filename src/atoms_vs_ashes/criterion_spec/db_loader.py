# man_hours: 2.0
"""DB-backed scoring definition loader.

The YAML specs remain a seed artifact during rollout. Once the DB registry
has rows for the current source hash, callers reconstruct the existing
``TemplateBundle`` shape entirely from database objects.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from atoms_vs_ashes.criterion_spec.loader import TemplateBundle, load_template_bundle
from atoms_vs_ashes.criterion_spec.schema import CriterionTemplate, TemplateFile
from atoms_vs_ashes.db.models_scoring_definitions import (
    ScoringBandDefinition,
    ScoringBandRecipeDefinition,
    ScoringCriterionDefinition,
    ScoringDefinitionState,
    ScoringFailConditionDefinition,
    ScoringSubScoreDefinition,
)


def _json(obj) -> dict | list:
    return obj.model_dump(mode="json") if obj is not None else None


def db_definition_revision(session: Session) -> tuple[int, str | None]:
    state = session.get(ScoringDefinitionState, "active")
    if state is None:
        return 0, None
    return int(state.revision), state.source_sha256


def _db_bundle_sha(templates: list[CriterionTemplate]) -> str:
    payload = [t.model_dump(mode="json") for t in sorted(templates, key=lambda x: x.criterion_id)]
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def sync_template_bundle_to_db(session: Session, bundle: TemplateBundle) -> None:
    """Replace DB definitions when the seed bundle changed."""
    count = session.execute(select(func.count()).select_from(ScoringCriterionDefinition)).scalar_one()
    state = session.get(ScoringDefinitionState, "active")
    if state is not None and state.source_sha256 == bundle.sha256 and count:
        return

    for table in (
        ScoringBandRecipeDefinition,
        ScoringSubScoreDefinition,
        ScoringBandDefinition,
        ScoringFailConditionDefinition,
        ScoringCriterionDefinition,
    ):
        session.execute(delete(table))

    for family, tf in bundle.families.items():
        for template in tf.criteria:
            data = template.model_dump(mode="json")
            session.add(
                ScoringCriterionDefinition(
                    criterion_id=template.criterion_id,
                    family=family,
                    name=template.name,
                    phases=data["phases"],
                    weight_factor=template.weight_factor,
                    normalised_weight_pct=template.normalised_weight_pct,
                    primary_metric=template.primary_metric,
                    band_kind=template.band_kind,
                    db_fields=_json(template.db_fields),
                    aggregation=_json(template.aggregation),
                    quality_floor=_json(template.quality_floor),
                    template_json=data,
                    updated_at=datetime.now(timezone.utc),
                )
            )
            session.flush()
            for fc in template.fail_conditions:
                session.add(
                    ScoringFailConditionDefinition(
                        criterion_id=template.criterion_id,
                        code=fc.code,
                        action=fc.action,
                        condition_expr=fc.condition_expr,
                        descriptor=fc.descriptor,
                        pass_mark=fc.pass_mark,
                        threshold=_json(fc.threshold),
                        threshold_affects_expr=fc.threshold_affects_expr,
                    )
                )
            for idx, band in enumerate(template.bands):
                lo, hi = band.score_range
                session.add(
                    ScoringBandDefinition(
                        criterion_id=template.criterion_id,
                        ordinal=idx,
                        score_low=lo,
                        score_high=hi,
                        condition_expr=band.condition_expr,
                        descriptor=band.descriptor,
                    )
                )
            for sub in template.sub_scores:
                session.add(
                    ScoringSubScoreDefinition(
                        criterion_id=template.criterion_id,
                        key=sub.key,
                        weight=sub.weight,
                        primary_metric=sub.primary_metric,
                        bands_json=[b.model_dump(mode="json") for b in sub.bands],
                    )
                )
            if template.band_recipe is not None:
                recipe = template.band_recipe
                session.add(
                    ScoringBandRecipeDefinition(
                        criterion_id=template.criterion_id,
                        kind=recipe.kind,
                        fail_code=recipe.fail_code,
                        metric=recipe.metric,
                        elevation_pass_m=recipe.elevation_pass_m,
                    )
                )

    revision = 1 if state is None else int(state.revision) + 1
    session.merge(
        ScoringDefinitionState(
            id="active",
            revision=revision,
            source_sha256=bundle.sha256,
            updated_at=datetime.now(timezone.utc),
        )
    )
    session.flush()


def load_template_bundle_from_db(
    session: Session,
    *,
    spec_dir: str | Path = "config/scoring_specs",
    seed_if_empty: bool = True,
) -> TemplateBundle:
    """Return a ``TemplateBundle`` reconstructed from DB scoring definitions."""
    if seed_if_empty:
        seed = load_template_bundle(spec_dir)
        sync_template_bundle_to_db(session, seed)

    rows = list(
        session.execute(
            select(ScoringCriterionDefinition).order_by(
                ScoringCriterionDefinition.family,
                ScoringCriterionDefinition.criterion_id,
            )
        ).scalars()
    )
    if not rows:
        raise ValueError("No DB scoring definitions are available.")

    templates = [CriterionTemplate.model_validate(row.template_json) for row in rows]
    families: dict[str, TemplateFile] = {}
    by_id: dict[str, CriterionTemplate] = {}
    for row, template in zip(rows, templates):
        by_id[template.criterion_id] = template
        families.setdefault(
            row.family,
            TemplateFile(family=row.family, criteria=[]),
        )
        existing = list(families[row.family].criteria)
        families[row.family] = TemplateFile(family=row.family, criteria=[*existing, template])

    return TemplateBundle(
        spec_dir=Path("db://scoring_definitions"),
        families=families,
        by_id=by_id,
        sha256=_db_bundle_sha(templates),
    )


__all__ = [
    "db_definition_revision",
    "load_template_bundle_from_db",
    "sync_template_bundle_to_db",
]
