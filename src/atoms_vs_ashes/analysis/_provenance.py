# man_hours: 2.0
"""Shared provenance and quality-flag utilities for analysis modules.

Ensures DataSource records exist before linking SiteAttribute rows,
and provides helpers for writing DataQualityFlag records consistently.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models import DataQualityFlag, DataSource
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
    """Write a DataQualityFlag record."""
    session.add(
        DataQualityFlag(
            site_id=site_id,
            dataset=dataset,
            dimension=dimension,
            level=level,
            detail=detail,
            run_id=run_id,
        )
    )
