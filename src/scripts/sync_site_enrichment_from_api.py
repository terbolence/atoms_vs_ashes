# man_hours: 0.6
"""Copy one site's enrichment (+ optional scoring runs) from API DB into merged.

The May 2026 Iernut CCGT work wrote connector output to ``atoms_vs_ashes``
(``--db-profile api``). The GUI and default Settings target
``atoms_vs_ashes_merged``. :mod:`sync_merged_from_source` only *updates* rows
that already exist in both DBs; it does not insert new per-site enrichment
rows, so a site like Iernut that exists in merged but has no hazard rows
never received the API data.

Usage::

    PYTHONPATH=src python -m scripts.sync_site_enrichment_from_api \\
        --site-id af7f107f-71b5-5a33-8125-9ccb7060f895 --dry-run

    PYTHONPATH=src python -m scripts.sync_site_enrichment_from_api \\
        --site-id af7f107f-71b5-5a33-8125-9ccb7060f895 --apply \\
        --migrate-runs iernut-score-20260517T1141
"""

from __future__ import annotations

import argparse
import sys
import uuid
from typing import Any

from sqlalchemy import MetaData, Table, create_engine, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine

from atoms_vs_ashes.db.profiles import DB_PROFILES

SITE_TABLES = (
    "sites",
    "site_natural_hazards",
    "site_human_hazards",
    "site_radiological",
    "site_emergency_planning",
    "site_infrastructure_v2",
)

MERGE_STAMP = "sync_site_from_api"


def _engine(profile: str) -> Engine:
    import os

    os.environ["POSTGRES_DB"] = DB_PROFILES[profile]
    from atoms_vs_ashes.config import Settings

    return create_engine(Settings().database.url, pool_pre_ping=True)


def _table(engine: Engine, name: str) -> Table:
    md = MetaData()
    return Table(name, md, autoload_with=engine)


def _upsert_site_rows(
    api: Engine,
    mer: Engine,
    table_name: str,
    site_id: uuid.UUID,
    *,
    dry_run: bool,
) -> int:
    src = _table(api, table_name)
    tgt = _table(mer, table_name)
    with api.connect() as a:
        row = a.execute(
            select(src).where(src.c.site_id == site_id)
        ).mappings().first()
    if row is None:
        return 0
    payload = dict(row)
    if dry_run:
        return 1
    payload["source_db"] = "api"
    payload["merge_run_id"] = MERGE_STAMP
    pk = [c.name for c in tgt.primary_key.columns]
    stmt = pg_insert(tgt).values(payload)
    if pk:
        update_cols = {
            c.name: stmt.excluded[c.name]
            for c in tgt.columns
            if c.name not in pk and c.name in payload
        }
        if "source_db" in tgt.c:
            update_cols["source_db"] = "api"
        if "merge_run_id" in tgt.c:
            update_cols["merge_run_id"] = MERGE_STAMP
        stmt = stmt.on_conflict_do_update(index_elements=pk, set_=update_cols)
    else:
        stmt = stmt.on_conflict_do_nothing()
    with mer.begin() as m:
        m.execute(stmt)
    return 1


RUN_CHILD_TABLES = (
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


def _copy_run_rows_for_site(
    api: Engine,
    mer: Engine,
    table_name: str,
    run_id: str,
    site_id: uuid.UUID,
    *,
    dry_run: bool,
) -> int:
    from scripts.migrate_runs_api_to_merged import _bulk_insert

    src = _table(api, table_name)
    if "run_id" not in src.c:
        return 0
    stmt = select(src).where(src.c.run_id == run_id)
    if "site_id" in src.c:
        stmt = stmt.where(src.c.site_id == site_id)
    with api.connect() as a:
        rows = a.execute(stmt).mappings().all()
    if not rows:
        return 0
    if dry_run:
        return len(rows)
    tgt = _table(mer, table_name)
    pk_cols = [c.name for c in tgt.primary_key.columns]
    return _bulk_insert(mer, tgt, rows, pk_cols)


def _ensure_run_row(api: Engine, mer: Engine, run_id: str, *, dry_run: bool) -> int:
    from scripts.migrate_runs_api_to_merged import _bulk_insert, _ensure_compiled_snapshots_for

    if dry_run:
        return 1
    runs_src = _table(api, "runs")
    runs_tgt = _table(mer, "runs")
    with api.connect() as a:
        row = a.execute(
            select(runs_src).where(runs_src.c.run_id == run_id)
        ).mappings().first()
    if row is None:
        return 0
    inserted = _bulk_insert(mer, runs_tgt, [dict(row)], ["run_id"])
    _ensure_compiled_snapshots_for(api, mer, run_id, dry_run=False)
    return inserted


def _purge_run_from_merged(mer: Engine, run_id: str, *, dry_run: bool) -> dict[str, int]:
    counts: dict[str, int] = {}
    if dry_run:
        with mer.connect() as m:
            for table in ("runs", *RUN_CHILD_TABLES):
                if table == "runs":
                    n = m.execute(
                        text("SELECT COUNT(*) FROM runs WHERE run_id = :rid"),
                        {"rid": run_id},
                    ).scalar()
                else:
                    n = m.execute(
                        text(f"SELECT COUNT(*) FROM {table} WHERE run_id = :rid"),
                        {"rid": run_id},
                    ).scalar()
                counts[table] = int(n or 0)
        return counts
    with mer.begin() as m:
        for table in reversed(RUN_CHILD_TABLES):
            res = m.execute(
                text(f"DELETE FROM {table} WHERE run_id = :rid"),
                {"rid": run_id},
            )
            counts[table] = res.rowcount or 0
        res = m.execute(
            text("DELETE FROM runs WHERE run_id = :rid"),
            {"rid": run_id},
        )
        counts["runs"] = res.rowcount or 0
    return counts


def _migrate_runs_for_site(
    api: Engine,
    mer: Engine,
    run_ids: list[str],
    site_id: uuid.UUID,
    *,
    dry_run: bool,
) -> dict[str, Any]:
    """Copy only rows for ``site_id`` — never a whole multi-site API run."""
    totals: dict[str, int] = {}
    purged: dict[str, dict[str, int]] = {}
    for rid in run_ids:
        purged[rid] = _purge_run_from_merged(mer, rid, dry_run=dry_run)
        if not dry_run:
            totals["runs"] = totals.get("runs", 0) + _ensure_run_row(
                api, mer, rid, dry_run=False,
            )
        else:
            totals["runs"] = totals.get("runs", 0) + 1
        for table in RUN_CHILD_TABLES:
            n = _copy_run_rows_for_site(
                api, mer, table, rid, site_id, dry_run=dry_run,
            )
            totals[table] = totals.get(table, 0) + n
    return {"purged": purged, "inserted": totals}


def sync_site(
    site_id: uuid.UUID,
    *,
    apply: bool,
    migrate_runs: list[str],
) -> dict[str, Any]:
    api = _engine("api")
    mer = _engine("merged")
    dry_run = not apply
    report: dict[str, Any] = {
        "site_id": str(site_id),
        "mode": "apply" if apply else "dry-run",
        "site_tables": {},
    }
    with mer.connect() as m:
        exists = m.execute(
            text("SELECT name FROM sites WHERE site_id = :sid"),
            {"sid": str(site_id)},
        ).first()
        if not exists:
            report["error"] = "site_id not found in merged DB — run alembic 049 first"
            return report
    for table in SITE_TABLES:
        report["site_tables"][table] = _upsert_site_rows(
            api, mer, table, site_id, dry_run=dry_run,
        )
    if migrate_runs:
        report["runs"] = _migrate_runs_for_site(
            api, mer, migrate_runs, site_id, dry_run=dry_run,
        )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-id", type=uuid.UUID, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--migrate-runs",
        nargs="*",
        default=[],
        help="Scoring/sensitivity run_ids to copy from API (e.g. iernut-score-...)",
    )
    args = parser.parse_args(argv)
    report = sync_site(
        args.site_id,
        apply=args.apply,
        migrate_runs=list(args.migrate_runs),
    )
    import json

    print(json.dumps(report, indent=2))
    if report.get("error"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
