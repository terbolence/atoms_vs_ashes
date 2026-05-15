# man_hours: 4.0
"""Additively migrate scoring/sensitivity runs from API to merged DB.

For each ``run_id`` present in `atoms_vs_ashes.runs` but absent from
`atoms_vs_ashes_merged.runs`, copy the parent ``runs`` row plus every
dependent child row (``screening_verdicts``, ``ranking_scores``,
``composite_rankings``, etc.) into merged. The copy uses
``INSERT ... ON CONFLICT DO NOTHING`` so the script is idempotent and
safe to re-run.

A migration receipt is written to ``audit_log`` for every migrated
run with ``operation='migrate_run_from_api'`` and the per-table row
counts as JSON.

Usage
-----

Inspect the plan without writing anything (default)::

    PYTHONPATH=src .venv/bin/python -m scripts.migrate_runs_api_to_merged

Apply the migration after reviewing the dry-run output::

    PYTHONPATH=src .venv/bin/python -m scripts.migrate_runs_api_to_merged \
        --apply --audit-stamp merged_canonical_20260515

Phase 3 / operator data refresh::

    PYTHONPATH=src .venv/bin/python -m scripts.migrate_runs_api_to_merged \
        --apply --include-operator-data --audit-stamp merged_canonical_20260515
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    MetaData, Table, create_engine, select, text,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine

DB_PROFILES = {"api": "atoms_vs_ashes", "merged": "atoms_vs_ashes_merged"}

# Run-scoped child tables, in dependency order so FKs to runs.run_id and
# compiled_scoring_snapshots.snapshot_id resolve cleanly.
RUN_CHILD_TABLES: tuple[str, ...] = (
    "dataset_snapshot",
    "scoring_run_snapshots",
    "screening_verdicts",
    "ranking_scores",
    "composite_rankings",
    "composite_score_components",
    "site_bands",
    "threshold_sensitivity",
    "country_balance_check",
)

# Operator / connector tables refreshed by --include-operator-data.
# Each entry is (table_name, conflict_index_columns). Most use the PK,
# but ``data_sources`` deduplicates by ``name`` (UNIQUE) since the
# source_id may have been assigned independently in each DB.
OPERATOR_TABLES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("threshold_overrides", ("criterion_id", "code", "smr_key")),
    ("data_sources", ("name",)),
    ("site_observations", ("observation_id",)),
    ("site_raw_responses", ("id",)),
    ("audit_log", ("log_id",)),
)

BATCH = 500


def _engine(db: str) -> Engine:
    os.environ["POSTGRES_DB"] = db
    from atoms_vs_ashes.config import Settings
    return create_engine(Settings().database.url, pool_pre_ping=True)


def _api_only_runs(api: Engine, mer: Engine) -> list[str]:
    with api.connect() as a, mer.connect() as m:
        api_set = {r[0] for r in a.execute(text("SELECT run_id FROM runs"))}
        mer_set = {r[0] for r in m.execute(text("SELECT run_id FROM runs"))}
    return sorted(api_set - mer_set)


def _toposort_runs(api: Engine, run_ids: list[str]) -> list[str]:
    """Order runs so any parent in the same batch is migrated first."""
    rid_set = set(run_ids)
    parents: dict[str, str | None] = {}
    with api.connect() as c:
        rows = c.execute(
            text(
                "SELECT run_id, parent_run_id FROM runs "
                "WHERE run_id = ANY(:rids)"
            ),
            {"rids": list(rid_set)},
        ).all()
    for rid, parent in rows:
        parents[rid] = parent if parent in rid_set else None

    visited: set[str] = set()
    out: list[str] = []

    def visit(rid: str) -> None:
        if rid in visited:
            return
        parent = parents.get(rid)
        if parent:
            visit(parent)
        visited.add(rid)
        out.append(rid)

    for rid in run_ids:
        visit(rid)
    return out


def _table(engine: Engine, name: str) -> Table:
    md = MetaData()
    return Table(name, md, autoload_with=engine)


def _ensure_compiled_snapshots_for(
    api: Engine, mer: Engine, run_id: str, dry_run: bool,
) -> int:
    """Copy any `compiled_scoring_snapshots` rows referenced by this
    run's `scoring_run_snapshots` rows from API to merged. Returns the
    number of snapshot rows actually inserted (0 on dry run).
    """
    with api.connect() as a:
        snap_ids = [
            r[0] for r in a.execute(
                text(
                    "SELECT DISTINCT snapshot_id FROM scoring_run_snapshots "
                    "WHERE run_id = :rid"
                ),
                {"rid": run_id},
            )
        ]
    if not snap_ids:
        return 0
    with mer.connect() as m:
        existing = {
            r[0] for r in m.execute(
                text(
                    "SELECT snapshot_id FROM compiled_scoring_snapshots "
                    "WHERE snapshot_id = ANY(:ids)"
                ),
                {"ids": snap_ids},
            )
        }
    missing = [s for s in snap_ids if s not in existing]
    if not missing:
        return 0
    if dry_run:
        return len(missing)
    src = _table(api, "compiled_scoring_snapshots")
    tgt = _table(mer, "compiled_scoring_snapshots")
    with api.connect() as a:
        rows = a.execute(
            select(src).where(src.c.snapshot_id.in_(missing))
        ).mappings().all()
    inserted = _bulk_insert(mer, tgt, rows, ["snapshot_id"])
    return inserted


def _bulk_insert(
    target_eng: Engine, target_tbl: Table,
    rows: list[dict[str, Any]], pk_cols: list[str],
) -> int:
    if not rows:
        return 0
    inserted = 0
    with target_eng.begin() as c:
        for i in range(0, len(rows), BATCH):
            chunk = [dict(r) for r in rows[i:i + BATCH]]
            stmt = pg_insert(target_tbl).values(chunk)
            if pk_cols:
                stmt = stmt.on_conflict_do_nothing(index_elements=pk_cols)
            else:
                stmt = stmt.on_conflict_do_nothing()
            res = c.execute(stmt)
            inserted += res.rowcount or 0
    return inserted


def _copy_run_scoped_table(
    api: Engine, mer: Engine, table_name: str, run_id: str, dry_run: bool,
) -> int:
    src = _table(api, table_name)
    if "run_id" not in src.c:
        return 0
    with api.connect() as a:
        rows = a.execute(
            select(src).where(src.c.run_id == run_id)
        ).mappings().all()
    if not rows:
        return 0
    if dry_run:
        return len(rows)
    tgt = _table(mer, table_name)
    pk_cols = [c.name for c in tgt.primary_key.columns]
    return _bulk_insert(mer, tgt, rows, pk_cols)


def _migrate_run(
    api: Engine, mer: Engine, run_id: str, dry_run: bool,
    audit_stamp: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not dry_run:
        runs_src = _table(api, "runs")
        runs_tgt = _table(mer, "runs")
        with api.connect() as a:
            row = a.execute(
                select(runs_src).where(runs_src.c.run_id == run_id)
            ).mappings().first()
        if row is None:
            raise RuntimeError(f"run {run_id!r} vanished from API mid-migration")
        counts["runs"] = _bulk_insert(mer, runs_tgt, [dict(row)], ["run_id"])
    else:
        counts["runs"] = 1

    counts["compiled_scoring_snapshots"] = _ensure_compiled_snapshots_for(
        api, mer, run_id, dry_run,
    )
    for table in RUN_CHILD_TABLES:
        counts[table] = _copy_run_scoped_table(
            api, mer, table, run_id, dry_run,
        )
    if not dry_run:
        _write_audit_receipt(mer, run_id, counts, audit_stamp)
    return counts


def _write_audit_receipt(
    mer: Engine, run_id: str, counts: dict[str, int], stamp: str,
) -> None:
    audit = _table(mer, "audit_log")
    payload = {
        "log_id": uuid.uuid4(),
        "timestamp": datetime.now(timezone.utc),
        "operation": "migrate_run_from_api",
        "table_name": "runs",
        "site_id": None,
        "before_value": None,
        "after_value": counts,
        "source_file": "scripts/migrate_runs_api_to_merged.py",
        "source_row": None,
        "run_id": run_id,
        "message": (
            f"merged_db_canonical_cutover ({stamp}): copied run {run_id!r} "
            f"and {sum(counts.values())} child rows from "
            f"atoms_vs_ashes -> atoms_vs_ashes_merged."
        ),
    }
    with mer.begin() as c:
        c.execute(pg_insert(audit).values([payload]))


def _migrate_operator_table(
    api: Engine, mer: Engine, table_name: str,
    conflict_cols: tuple[str, ...], dry_run: bool,
) -> int:
    src = _table(api, table_name)
    tgt = _table(mer, table_name)
    with api.connect() as a:
        rows = a.execute(select(src)).mappings().all()
    if dry_run:
        if not conflict_cols:
            return len(rows)
        with mer.connect() as m:
            present_keys = {
                tuple(r[c] for c in conflict_cols)
                for r in m.execute(
                    select(*[tgt.c[c] for c in conflict_cols])
                ).mappings().all()
            }
        return sum(
            1 for r in rows
            if tuple(r[c] for c in conflict_cols) not in present_keys
        )
    return _bulk_insert(mer, tgt, rows, list(conflict_cols))


def _print_plan(
    plan: list[tuple[str, dict[str, int]]],
    operator_plan: dict[str, int] | None,
) -> None:
    print(f"Runs to migrate: {len(plan)}")
    total = 0
    for run_id, counts in plan:
        n = sum(counts.values())
        total += n
        print(f"  {run_id:42s} +{n:>9} rows ({_short_counts(counts)})")
    print(f"Total run-scoped rows: {total}")
    if operator_plan is not None:
        print()
        print("Operator-data refresh:")
        for table, n in operator_plan.items():
            print(f"  {table:42s} +{n:>9} rows")


def _short_counts(counts: dict[str, int]) -> str:
    return ", ".join(
        f"{t}={n}" for t, n in counts.items() if n
    ) or "all-tables-empty"


def _parse(argv: Iterable[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument(
        "--apply", action="store_true",
        help="Actually write to the merged DB. Default is dry-run.",
    )
    p.add_argument(
        "--include-operator-data", action="store_true",
        help="Also resync threshold_overrides + data_sources from API.",
    )
    p.add_argument(
        "--limit-runs", type=int, default=None,
        help="Cap the number of runs migrated (useful for staged trials).",
    )
    p.add_argument(
        "--audit-stamp",
        default=f"merged_canonical_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}",
        help="Identifier for this migration batch (written to audit_log.message).",
    )
    return p.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = _parse(argv)
    api = _engine(DB_PROFILES["api"])
    mer = _engine(DB_PROFILES["merged"])

    api_only = _api_only_runs(api, mer)
    if args.limit_runs is not None:
        api_only = api_only[: args.limit_runs]
    ordered = _toposort_runs(api, api_only)

    plan: list[tuple[str, dict[str, int]]] = []
    for rid in ordered:
        counts = _migrate_run(api, mer, rid, dry_run=not args.apply,
                              audit_stamp=args.audit_stamp)
        plan.append((rid, counts))

    operator_plan: dict[str, int] | None = None
    if args.include_operator_data:
        operator_plan = {
            tname: _migrate_operator_table(
                api, mer, tname, conflict_cols, dry_run=not args.apply,
            )
            for tname, conflict_cols in OPERATOR_TABLES
        }

    print(f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print(f"Audit stamp: {args.audit_stamp}")
    print()
    _print_plan(plan, operator_plan)
    return 0


if __name__ == "__main__":
    sys.exit(main())
