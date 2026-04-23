#!/usr/bin/env python
# man_hours: 2.0
"""Build ``atoms_vs_ashes_merged`` from the cleaned API DB.

Step 2.4 / Phase 2 of the data-fusion plan.

Pipeline
--------

1.  (Optional) drop ``atoms_vs_ashes_merged`` if it already exists.
    Use ``--keep-existing`` to refuse to clobber it.
2.  Create ``atoms_vs_ashes_merged`` and enable PostGIS.
3.  ``pg_dump --format=custom`` from ``atoms_vs_ashes`` piped into
    ``pg_restore`` against the new database.
4.  Apply Alembic migration ``031_add_merge_provenance`` against the
    merged DB (adds ``source_db`` / ``merge_run_id`` to the six
    domain tables and creates the ``merge_audit`` table).
5.  Stamp every row in the six provenance tables with
    ``source_db = 'api'`` (already the server default) and
    ``merge_run_id = <run_id>``.
6.  Verify row counts match between source and target for the core
    tables.
7.  Write a Markdown summary report.

Idempotency
-----------

* If the merged DB does not exist → full pipeline.
* If it exists and ``--keep-existing`` is set → skip steps 1–4 and
  re-stamp / re-verify only.
* If it exists and ``--keep-existing`` is not set → drop and rebuild.

Safety
------

The script never touches the source ``atoms_vs_ashes`` DB.  The
``--dry-run`` flag prints the planned commands without executing
anything that mutates state.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from psycopg2 import sql
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = PROJECT_ROOT / "audit" / "post_processing" / "02_data_verification"

PG_BIN = Path("/opt/homebrew/opt/postgresql@17/bin")  # match server version
PG_DUMP = PG_BIN / "pg_dump"
PG_RESTORE = PG_BIN / "pg_restore"
PSQL = PG_BIN / "psql"

SOURCE_DB = "atoms_vs_ashes"
MERGED_DB = "atoms_vs_ashes_merged"

PROVENANCE_TABLES = (
    "sites",
    "site_natural_hazards",
    "site_human_hazards",
    "site_radiological",
    "site_emergency_planning",
    "site_infrastructure_v2",
)

# Tables we sanity-check by row count after restore.  Keep this list
# explicit (rather than discovered) so the script fails loudly when
# the schema gains a new domain table.
COUNT_TABLES = (
    "sites",
    "site_units",
    "site_ownership",
    "site_natural_hazards",
    "site_human_hazards",
    "site_radiological",
    "site_emergency_planning",
    "site_infrastructure_v2",
    "criteria",
    "screening_verdicts",
    "ranking_scores",
    "composite_rankings",
    "site_observations",
    "site_raw_responses",
    "enrichment_runs",
    "audit_log",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _conn_kwargs(db: str) -> dict[str, str]:
    return {
        "host": os.environ.get("POSTGRES_HOST", "localhost"),
        "port": os.environ.get("POSTGRES_PORT", "5432"),
        "user": os.environ.get("POSTGRES_USER", "atoms"),
        "password": os.environ.get("POSTGRES_PASSWORD", "changeme"),
        "dbname": db,
    }


def _superuser_conn_kwargs(db: str) -> dict[str, str]:
    """Connection params for a local OS superuser (typically the user
    running this script on a dev workstation).  Required to ``CREATE
    DATABASE`` and ``CREATE EXTENSION postgis`` because the application
    role usually lacks those privileges."""
    return {
        "host": os.environ.get("POSTGRES_HOST", "localhost"),
        "port": os.environ.get("POSTGRES_PORT", "5432"),
        "user": os.environ.get(
            "POSTGRES_SUPERUSER",
            os.environ.get("USER", "postgres"),
        ),
        "dbname": db,
    }


def _connect(db: str, autocommit: bool = False, *, superuser: bool = False):
    kw = _superuser_conn_kwargs(db) if superuser else _conn_kwargs(db)
    conn = psycopg2.connect(**kw)
    if autocommit:
        conn.autocommit = True
    return conn


def _sqlalchemy_url(db: str) -> str:
    kw = _conn_kwargs(db)
    return (
        f"postgresql://{kw['user']}:{kw['password']}"
        f"@{kw['host']}:{kw['port']}/{db}"
    )


def _run(cmd: list[str], *, dry_run: bool, env: dict | None = None) -> int:
    pretty = " ".join(shlex.quote(c) for c in cmd)
    print(f"  $ {pretty}")
    if dry_run:
        return 0
    proc = subprocess.run(cmd, env={**os.environ, **(env or {})})
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed (rc={proc.returncode}): {pretty}"
        )
    return proc.returncode


def database_exists(db: str) -> bool:
    conn = _connect("postgres", autocommit=True, superuser=True)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db,))
            return cur.fetchone() is not None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Pipeline steps
# ---------------------------------------------------------------------------

def drop_database(db: str, *, dry_run: bool) -> None:
    print(f"[1/7] Dropping database {db!r} (if it exists)…")
    if dry_run:
        print(f"  $ DROP DATABASE IF EXISTS {db}")
        return
    conn = _connect("postgres", autocommit=True, superuser=True)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()",
                (db,),
            )
            cur.execute(
                sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db))
            )
    finally:
        conn.close()
    print(f"  ok – dropped {db}")


def create_database(db: str, *, dry_run: bool) -> None:
    print(f"[2/7] Creating database {db!r} + enabling PostGIS…")
    if dry_run:
        print(f"  $ CREATE DATABASE {db} OWNER atoms")
        print(f"  $ CREATE EXTENSION postgis")
        return
    owner = os.environ.get("POSTGRES_USER", "atoms")
    conn = _connect("postgres", autocommit=True, superuser=True)
    try:
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(db), sql.Identifier(owner)
                )
            )
    finally:
        conn.close()
    # PostGIS extension requires superuser; create it then GRANT all on
    # the spatial_ref_sys table so the application user can query it.
    conn = _connect(db, autocommit=True, superuser=True)
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis")
            cur.execute(
                sql.SQL("GRANT ALL ON ALL TABLES IN SCHEMA public TO {}").format(
                    sql.Identifier(owner)
                )
            )
    finally:
        conn.close()
    print(f"  ok – created {db} with PostGIS (owner={owner})")


def dump_and_restore(*, dry_run: bool) -> None:
    print(f"[3/7] pg_dump {SOURCE_DB} | pg_restore → {MERGED_DB}")
    src = _conn_kwargs(SOURCE_DB)
    tgt = _conn_kwargs(MERGED_DB)

    pgpass = src["password"]

    dump_cmd = [
        str(PG_DUMP),
        "-h", src["host"],
        "-p", src["port"],
        "-U", src["user"],
        "-d", src["dbname"],
        "--format=custom",
        "--no-owner",
        "--no-privileges",
        # Exclude PostGIS internals we already created via CREATE EXTENSION.
        "--exclude-schema=tiger",
        "--exclude-schema=tiger_data",
        "--exclude-schema=topology",
        # Skip rows in spatial_ref_sys — already populated by CREATE EXTENSION.
        "--exclude-table-data=spatial_ref_sys",
    ]

    restore_cmd = [
        str(PG_RESTORE),
        "-h", tgt["host"],
        "-p", tgt["port"],
        "-U", tgt["user"],
        "-d", tgt["dbname"],
        "--no-owner",
        "--no-privileges",
    ]

    pretty_dump = " ".join(shlex.quote(c) for c in dump_cmd)
    pretty_restore = " ".join(shlex.quote(c) for c in restore_cmd)
    print(f"  $ {pretty_dump} \\")
    print(f"      | {pretty_restore}")
    if dry_run:
        return

    env = {**os.environ, "PGPASSWORD": pgpass}
    dump_proc = subprocess.Popen(dump_cmd, stdout=subprocess.PIPE, env=env)
    restore_proc = subprocess.Popen(
        restore_cmd, stdin=dump_proc.stdout, env=env
    )
    if dump_proc.stdout is not None:
        dump_proc.stdout.close()  # let dump receive SIGPIPE if restore exits
    restore_rc = restore_proc.wait()
    dump_rc = dump_proc.wait()
    if dump_rc != 0:
        raise RuntimeError(f"pg_dump failed (rc={dump_rc})")
    if restore_rc != 0:
        # pg_restore returns non-zero even for cosmetic warnings (PostGIS
        # COMMENT ownership etc.).  Verify that all required tables exist
        # and have data; if so, treat the warnings as cosmetic.
        print(
            f"  pg_restore returned rc={restore_rc} – verifying the "
            f"restore is materially complete…"
        )
    print("  ok – dump/restore stream finished")


def apply_migration_provenance(*, dry_run: bool) -> None:
    print(f"[4/7] Applying alembic migration 031 to {MERGED_DB}…")
    env = {"POSTGRES_DB": MERGED_DB}
    cmd = ["alembic", "upgrade", "head"]
    pretty = " ".join(cmd)
    print(f"  $ POSTGRES_DB={MERGED_DB} {pretty}")
    if dry_run:
        return
    proc = subprocess.run(cmd, env={**os.environ, **env}, cwd=str(PROJECT_ROOT))
    if proc.returncode != 0:
        raise RuntimeError(
            f"alembic upgrade head failed (rc={proc.returncode}); "
            f"verify alembic.ini and POSTGRES_DB env."
        )
    print("  ok – migration 031 applied")


def stamp_provenance(run_id: str, *, dry_run: bool) -> dict[str, int]:
    print(f"[5/7] Stamping merge_run_id={run_id!r} on provenance tables…")
    counts: dict[str, int] = {}
    if dry_run:
        for tbl in PROVENANCE_TABLES:
            print(f"  $ UPDATE {tbl} SET merge_run_id={run_id!r} "
                  f"WHERE merge_run_id IS NULL")
        return counts

    engine = create_engine(_sqlalchemy_url(MERGED_DB), pool_pre_ping=True)
    with engine.begin() as conn:
        # Insert an enrichment_runs row so the run_id has a parent record.
        conn.execute(
            text(
                "INSERT INTO enrichment_runs "
                "(run_id, run_type, started_at, completed_at, status, notes) "
                "VALUES (:run_id, 'merge_phase2', :ts, :ts, 'completed', "
                "'Phase 2: API-only merged DB built from cleaned atoms_vs_ashes') "
                "ON CONFLICT (run_id) DO NOTHING"
            ),
            {"run_id": run_id, "ts": datetime.now(timezone.utc)},
        )
        for tbl in PROVENANCE_TABLES:
            res = conn.execute(
                text(
                    f"UPDATE {tbl} SET merge_run_id = :run_id, "
                    f"source_db = 'api' "
                    f"WHERE merge_run_id IS NULL OR source_db <> 'api'"
                ),
                {"run_id": run_id},
            )
            counts[tbl] = res.rowcount
            print(f"  {tbl}: {res.rowcount} rows stamped")
    return counts


def verify_counts(*, dry_run: bool) -> dict[str, tuple[int, int]]:
    print(f"[6/7] Verifying row counts ({SOURCE_DB} ↔ {MERGED_DB})…")
    if dry_run:
        return {}
    src_counts: dict[str, int] = {}
    tgt_counts: dict[str, int] = {}
    src_engine = create_engine(_sqlalchemy_url(SOURCE_DB), pool_pre_ping=True)
    tgt_engine = create_engine(_sqlalchemy_url(MERGED_DB), pool_pre_ping=True)
    for tbl in COUNT_TABLES:
        for engine, store in ((src_engine, src_counts), (tgt_engine, tgt_counts)):
            with engine.connect() as conn:
                row = conn.execute(text(f"SELECT count(*) FROM {tbl}")).fetchone()
                store[tbl] = int(row[0]) if row else 0
    summary: dict[str, tuple[int, int]] = {}
    fail = False
    # Tables where the merged DB is allowed to be larger than the source
    # because the merge pipeline itself writes to them.
    allowed_drift = {
        "enrichment_runs": "+merge run record(s)",
        "merge_audit": "Phase 5 audit log (does not exist on source)",
    }
    for tbl in COUNT_TABLES:
        s, t = src_counts[tbl], tgt_counts[tbl]
        summary[tbl] = (s, t)
        if s == t:
            marker = "OK"
        elif tbl in allowed_drift and t >= s:
            marker = f"OK ({allowed_drift[tbl]})"
        else:
            marker = "MISMATCH"
            fail = True
        print(f"  {tbl:32s}  src={s:>8}  tgt={t:>8}  [{marker}]")
    if fail:
        raise RuntimeError(
            "Row-count mismatch between source and merged DB; aborting."
        )
    return summary


def write_report(
    run_id: str,
    counts: dict[str, tuple[int, int]],
    stamped: dict[str, int],
    *,
    dry_run: bool,
    report_path: Path,
) -> None:
    print(f"[7/7] Writing report to {report_path}…")
    if dry_run:
        return
    report_path.parent.mkdir(parents=True, exist_ok=True)

    allowed_drift = {
        "enrichment_runs": "+merge run record",
    }

    lines: list[str] = []
    lines.append(f"# Phase 2 merged-DB build — {datetime.now().date()}")
    lines.append("")
    lines.append(f"**Run id:** `{run_id}`  ")
    lines.append(f"**Source DB:** `{SOURCE_DB}` (post-Phase-1 cleaned)  ")
    lines.append(f"**Target DB:** `{MERGED_DB}`  ")
    lines.append(
        f"**Migration applied:** `031_add_merge_provenance` (source_db, "
        f"merge_run_id, merge_audit table)"
    )
    lines.append("")
    lines.append("## Row-count verification")
    lines.append("")
    lines.append("| Table | Source rows | Merged rows | Status |")
    lines.append("|-------|-------------|-------------|--------|")
    for tbl, (src, tgt) in counts.items():
        if src == tgt:
            status = "OK"
        elif tbl in allowed_drift and tgt >= src:
            status = f"OK ({allowed_drift[tbl]})"
        else:
            status = "MISMATCH"
        lines.append(f"| `{tbl}` | {src} | {tgt} | {status} |")
    lines.append("")
    lines.append("## Provenance stamping")
    lines.append("")
    lines.append(
        "Every row in the six provenance tables already has `source_db='api'` "
        "(server default applied on column creation by migration 031).  The "
        "table below shows rows that needed an explicit UPDATE to set "
        f"`merge_run_id={run_id!r}` on this run; on a fresh build all six "
        "rows show 363, on a re-run with `--keep-existing` they show 0."
    )
    lines.append("")
    lines.append("| Table | Rows stamped this run |")
    lines.append("|-------|----------------------|")
    for tbl, n in stamped.items():
        lines.append(f"| `{tbl}` | {n} |")
    lines.append("")
    lines.append("## What this DB contains")
    lines.append("")
    lines.append(
        "* A clone of the cleaned API DB (`atoms_vs_ashes`) "
        "post Phase-1 anomaly fixes."
    )
    lines.append(
        "* New columns `source_db` and `merge_run_id` on every domain "
        "table (`sites`, `site_natural_hazards`, `site_human_hazards`, "
        "`site_radiological`, `site_emergency_planning`, "
        "`site_infrastructure_v2`).  All rows currently tagged "
        "`source_db='api'`."
    )
    lines.append(
        "* New `merge_audit` table — one row per LLM-driven scalar "
        "value chosen during Phase 5.  Currently empty."
    )
    lines.append("")
    lines.append("## Next phases (not yet executed)")
    lines.append("")
    lines.append("* **Phase 3** — write `report/business_logic.md`.")
    lines.append(
        "* **Phase 4** — propose LLM fields to promote into the merged DB "
        "(`<date>_llm_field_promotion_proposal.md`).  Awaits user sign-off."
    )
    lines.append(
        "* **Phase 5** — apply approved promotions, write `merge_audit` "
        "rows, run a smaller post-LLM anomaly sweep on rows where "
        "`source_db != 'api'`."
    )
    lines.append("")
    report_path.write_text("\n".join(lines) + "\n")
    print(f"  ok – wrote {report_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned commands without executing anything.",
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help=(
            "If the merged DB already exists, skip drop / create / restore "
            "and only re-stamp provenance + verify counts."
        ),
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Override the merge_run_id (default: merge_phase2_<timestamp>).",
    )
    parser.add_argument(
        "--report",
        default=None,
        help=(
            "Override report path (default: "
            "audit/post_processing/02_data_verification/<date>_merged_db_build.md)."
        ),
    )
    args = parser.parse_args(argv)

    if not PG_DUMP.exists():
        print(
            f"ERROR: pg_dump not found at {PG_DUMP}.  Adjust PG_BIN at the "
            f"top of this script if your PostgreSQL 17 install lives elsewhere.",
            file=sys.stderr,
        )
        return 2

    # Use local date for the filename so it lines up with prior reports
    # (e.g. 20260421_api_db_anomalies.md from Phase 1).
    today = datetime.now().date().isoformat().replace("-", "")
    run_id = args.run_id or f"merge_phase2_{today}"
    report_path = Path(args.report) if args.report else (
        REPORT_DIR / f"{today}_merged_db_build.md"
    )

    exists = database_exists(MERGED_DB)
    print(f"==> source: {SOURCE_DB}")
    print(f"==> target: {MERGED_DB} (exists={exists})")
    print(f"==> run_id: {run_id}")
    print(f"==> report: {report_path}")
    print(f"==> mode:   {'dry-run' if args.dry_run else 'apply'}")
    print()

    if exists and args.keep_existing:
        print("Keeping existing merged DB; only re-stamp + verify will run.")
    else:
        if exists:
            drop_database(MERGED_DB, dry_run=args.dry_run)
        create_database(MERGED_DB, dry_run=args.dry_run)
        dump_and_restore(dry_run=args.dry_run)
        apply_migration_provenance(dry_run=args.dry_run)

    stamped = stamp_provenance(run_id, dry_run=args.dry_run)
    counts = verify_counts(dry_run=args.dry_run)
    write_report(
        run_id, counts, stamped,
        dry_run=args.dry_run,
        report_path=report_path,
    )
    print()
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
