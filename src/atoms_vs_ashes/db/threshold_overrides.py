# man_hours: 1.0
"""Load / persist :class:`ThresholdOverride` rows for GUI fail-threshold edits."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models import ThresholdOverride


def fetch_all_rows(session: Session) -> list[ThresholdOverride]:
    return list(session.execute(select(ThresholdOverride)).scalars().all())


def merge_db_over_yaml(
    base_fail_thresholds: dict[str, dict[str, Any]],
    session: Session,
) -> dict[str, dict[str, Any]]:
    """Merge DB overrides on top of YAML profile fail_thresholds (DB wins)."""
    rows = fetch_all_rows(session)
    out: dict[str, dict[str, Any]] = {k: dict(v) for k, v in base_fail_thresholds.items()}
    for r in rows:
        out.setdefault(r.criterion_id, {})
        if r.smr_key == "":
            out[r.criterion_id][r.code] = r.value
        else:
            cur = out[r.criterion_id].get(r.code)
            if isinstance(cur, dict) and cur and all(
                isinstance(k, str) for k in cur
            ):
                merged = dict(cur)
            else:
                merged = {}
                if cur is not None and not isinstance(cur, dict):
                    merged[""] = cur
            merged[r.smr_key] = r.value
            out[r.criterion_id][r.code] = merged
    return out


def save_threshold_rows(
    session: Session,
    rows: list[tuple[str, str, Any, str | None]],
    *,
    updated_by: str | None = None,
) -> None:
    """Upsert (criterion_id, code, smr_key) rows."""
    for criterion_id, code, value, smr_key in rows:
        sk = smr_key or ""
        row = session.get(ThresholdOverride, (criterion_id, code, sk))
        if row is None:
            row = ThresholdOverride(
                criterion_id=criterion_id,
                code=code,
                smr_key=sk,
                value=value,
                updated_by=updated_by,
            )
            session.add(row)
        else:
            row.value = value
            row.updated_by = updated_by
    session.flush()


def delete_threshold_rows(
    session: Session,
    rows: list[tuple[str, str, str | None]],
) -> None:
    """Delete persisted overrides for ``(criterion_id, code, smr_key)`` rows."""
    for criterion_id, code, smr_key in rows:
        row = session.get(ThresholdOverride, (criterion_id, code, smr_key or ""))
        if row is not None:
            session.delete(row)
    session.flush()


def snapshot_to_profile_dict(
    profile_fail_thresholds: dict[str, dict[str, Any]],
    session: Session,
) -> dict[str, dict[str, Any]]:
    """Return merged fail_thresholds for session state."""
    return deepcopy(merge_db_over_yaml(profile_fail_thresholds, session))
