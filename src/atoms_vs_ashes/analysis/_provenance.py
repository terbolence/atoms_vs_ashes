# man_hours: 2.0
"""Shared provenance and observation utilities for analysis modules.

Ensures DataSource records exist before linking domain-table rows,
and provides helpers for writing SiteObservation records consistently.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models import DataSource, SiteObservation
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


def ensure_data_source(
    session: Session,
    name: str,
    url: str,
    description: str | None = None,
) -> uuid.UUID:
    """Ensure a DataSource row exists, return its source_id."""
    existing = session.query(DataSource).filter_by(name=name).first()
    if existing:
        existing.last_fetched = datetime.now(timezone.utc)
        return existing.source_id
    ds = DataSource(
        source_id=uuid.uuid4(),
        name=name,
        url=url,
        description=description,
        last_fetched=datetime.now(timezone.utc),
    )
    session.add(ds)
    session.flush()
    return ds.source_id


def write_observation(
    session: Session,
    *,
    site_id: uuid.UUID,
    criterion_id: str,
    observation: str,
    run_id: str,
    source_type: str = "api",
    impact: str = "neutral",
    confidence: str = "medium",
    smr_key: str | None = None,
    author: str | None = None,
) -> None:
    """Write a SiteObservation record (replaces the old write_quality_flag)."""
    session.add(
        SiteObservation(
            site_id=site_id,
            criterion_id=criterion_id,
            smr_key=smr_key,
            source_type=source_type,
            observation=observation,
            impact=impact,
            confidence=confidence,
            author=author,
            run_id=run_id,
        )
    )


# Backwards-compatible alias during migration
def write_quality_flag(
    session: Session,
    *,
    site_id: uuid.UUID,
    dataset: str,
    dimension: str,
    level: str,
    detail: str,
    run_id: str,
) -> None:
    """Deprecated wrapper — maps old quality-flag calls to SiteObservation."""
    _level_to_confidence = {
        "high": "high",
        "medium": "medium",
        "low": "low",
        "insufficient": "low",
    }
    _level_to_impact = {
        "high": "neutral",
        "medium": "neutral",
        "low": "negative",
        "insufficient": "blocking",
    }
    session.add(
        SiteObservation(
            site_id=site_id,
            criterion_id=dimension,
            source_type="api",
            observation=f"[{dataset}] {detail}",
            impact=_level_to_impact.get(level, "neutral"),
            confidence=_level_to_confidence.get(level, "medium"),
            run_id=run_id,
        )
    )
