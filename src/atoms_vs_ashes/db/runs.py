# man_hours: 1.5
"""Run-provenance helpers for the analytics tables (Alembic rev 034).

A "run" is the unit of provenance shared by every analytics row in
``site_bands``, ``country_rankings_summary``, ``oat_importance``,
``failure_outcomes`` and friends. ``start_run`` writes a row in
``runs`` (status ``running``) plus a ``dataset_snapshot`` row with
the rubric / sites / SMR cardinalities; ``complete_run`` flips the
status to ``completed`` (or ``failed``).

If a caller cannot reach Postgres (e.g. unit tests) ``start_run``
returns a stub object holding the freshly-minted ``run_id`` so the rest
of the pipeline can still write CSVs.

Pre-revision-034 ``run_id`` strings stay valid: the FKs from
``composite_rankings`` / ``ranking_scores`` / ``screening_verdicts``
were created ``NOT VALID`` so historical rows are exempt.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models_analytics import DatasetSnapshot, Run
from atoms_vs_ashes.logging import get_logger, new_run_id

log = get_logger(__name__)


@dataclass
class RunHandle:
    """Lightweight handle returned by :func:`start_run`.

    Carries the ``run_id`` so callers that share a write-only
    interface (e.g. CSV writers) don't need an active SQLAlchemy
    session.
    """

    run_id: str
    run_kind: str
    parent_run_id: str | None = None
    persisted: bool = True


@dataclass
class DatasetMeta:
    """Cardinality + provenance for the dataset behind a run."""

    rubric_file_path: str | None = None
    n_sites_total: int | None = None
    n_sites_screened_in: int | None = None
    n_smrs: int | None = None
    n_criteria_exclusionary: int | None = None
    n_criteria_avoidance: int | None = None
    n_criteria_ranking: int | None = None
    weight_normalisation_profile: str | None = None


def _git_sha() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=2, check=False,
        )
        if out.returncode == 0:
            return out.stdout.strip()[:40]
    except Exception:  # pragma: no cover -- best-effort provenance only
        pass
    return None


def _rubric_sha256(rubric_path: str | None) -> str | None:
    if not rubric_path:
        return None
    p = Path(rubric_path)
    if not p.exists():
        return None
    h = hashlib.sha256()
    if p.is_dir():
        for child in sorted(p.rglob("*")):
            if child.is_file():
                h.update(child.relative_to(p).as_posix().encode())
                h.update(child.read_bytes())
    else:
        h.update(p.read_bytes())
    return h.hexdigest()


def start_run(
    session: Session | None,
    *,
    run_kind: str,
    cli_command: str | None = None,
    notes: str | None = None,
    parent_run_id: str | None = None,
    run_id: str | None = None,
    dataset_meta: DatasetMeta | None = None,
) -> RunHandle:
    """Insert a ``runs`` row (status ``running``) and a ``dataset_snapshot``.

    If ``session`` is ``None`` (tests, dry-runs) only the ``RunHandle``
    is returned and ``persisted`` is set to ``False`` -- callers should
    treat the returned ``run_id`` as authoritative either way so that
    CSV / Markdown filenames stay aligned with the DB row when one is
    eventually written.
    """
    rid = run_id or new_run_id()
    if session is None:
        return RunHandle(
            run_id=rid, run_kind=run_kind,
            parent_run_id=parent_run_id, persisted=False,
        )

    run = Run(
        run_id=rid,
        run_kind=run_kind,
        parent_run_id=parent_run_id,
        started_at=datetime.now(timezone.utc),
        status="running",
        cli_command=cli_command or _safe_cli(),
        git_sha=_git_sha(),
        notes=notes,
    )
    session.add(run)
    session.flush()

    if dataset_meta is not None:
        snap = DatasetSnapshot(
            run_id=rid,
            rubric_file_path=dataset_meta.rubric_file_path,
            rubric_sha256=_rubric_sha256(dataset_meta.rubric_file_path),
            n_sites_total=dataset_meta.n_sites_total,
            n_sites_screened_in=dataset_meta.n_sites_screened_in,
            n_smrs=dataset_meta.n_smrs,
            n_criteria_exclusionary=dataset_meta.n_criteria_exclusionary,
            n_criteria_avoidance=dataset_meta.n_criteria_avoidance,
            n_criteria_ranking=dataset_meta.n_criteria_ranking,
            weight_normalisation_profile=dataset_meta.weight_normalisation_profile,
        )
        session.add(snap)
    session.flush()

    log.info(
        "run_started",
        run_id=rid, run_kind=run_kind, parent_run_id=parent_run_id,
    )
    return RunHandle(
        run_id=rid, run_kind=run_kind, parent_run_id=parent_run_id,
        persisted=True,
    )


def complete_run(
    session: Session | None,
    handle: RunHandle,
    *,
    status: str = "completed",
    notes: str | None = None,
) -> None:
    """Flip ``runs.status`` and stamp ``completed_at``.

    No-op when the original ``start_run`` could not write to the DB.
    """
    if session is None or not handle.persisted:
        return
    row = session.execute(
        select(Run).where(Run.run_id == handle.run_id)
    ).scalar_one_or_none()
    if row is None:
        log.warning("complete_run_missing", run_id=handle.run_id)
        return
    row.status = status
    row.completed_at = datetime.now(timezone.utc)
    if notes:
        row.notes = (row.notes + "\n" + notes) if row.notes else notes
    session.flush()
    log.info(
        "run_completed",
        run_id=handle.run_id, run_kind=handle.run_kind, status=status,
    )


@contextmanager
def run_scope(
    session: Session | None,
    *,
    run_kind: str,
    cli_command: str | None = None,
    notes: str | None = None,
    parent_run_id: str | None = None,
    run_id: str | None = None,
    dataset_meta: DatasetMeta | None = None,
) -> Generator[RunHandle, None, None]:
    """Context manager that calls ``start_run`` / ``complete_run``.

    On ``Exception`` the run is marked ``failed`` before the exception
    is re-raised so the ``runs`` row is never left dangling at
    ``running``.
    """
    handle = start_run(
        session,
        run_kind=run_kind,
        cli_command=cli_command,
        notes=notes,
        parent_run_id=parent_run_id,
        run_id=run_id,
        dataset_meta=dataset_meta,
    )
    try:
        yield handle
    except Exception as exc:
        complete_run(session, handle, status="failed", notes=f"error={exc!r}")
        raise
    else:
        complete_run(session, handle, status="completed")


def _safe_cli() -> str | None:
    """Best-effort recovery of the executing CLI command."""
    try:
        argv = os.environ.get("AV_CLI_COMMAND")
        if argv:
            return argv[:2000]
        import sys
        return " ".join(sys.argv)[:2000]
    except Exception:  # pragma: no cover
        return None
