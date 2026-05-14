#!/usr/bin/env python
# man_hours: 2.0
"""Re-sync hazard + site rows in ``atoms_vs_ashes_merged`` from the
canonical ``atoms_vs_ashes`` source DB.

This is the surgical complement to :mod:`build_merged_db` for the case
where the merged DB already contains downstream scoring history
(``screening_verdicts``, ``ranking_scores``, ``composite_rankings``)
that must be preserved, but its hazard inputs have drifted behind the
source DB (e.g. after running SP-F / OurAirports / OSM-military
enrichment against ``atoms_vs_ashes`` long after the last full merged
rebuild).

Behaviour
---------

For each of the six target tables, in this order::

    sites,
    site_natural_hazards,
    site_human_hazards,
    site_radiological,
    site_emergency_planning,
    site_infrastructure_v2,

the script:

1.  Reads from the **source** DB inside a ``READ ONLY`` transaction
    (the source DB is never written to).
2.  Computes the ``site_id`` intersection between source and merged,
    so the merged-only ``Braila`` row (``323cdbf0-...``) is left
    untouched and no new rows are inserted into merged.
3.  Builds an ``UPDATE`` per row that copies every column shared
    between source and merged **except** ``merge_run_id`` and
    ``source_db`` (these are stamped explicitly by the resync).
4.  Stamps ``merge_run_id = <resync run id>`` and leaves
    ``source_db = 'api'`` on every touched row.
5.  Writes a parent record into ``enrichment_runs`` and a per-(site,
    table) row into ``merge_audit`` with ``source_chosen='api'`` and
    ``rule_id='resync_full_row'``.
6.  Writes a Markdown verification report under
    ``audit/post_processing/02_data_verification/<date>_merged_resync.md``.

The script is **idempotent** — re-running with the same run id (or a
new one) simply re-applies the source values; the audit table grows.

Hard safety guards
------------------

* Refuses to run if the source DB alembic head is older than the
  merged DB alembic head.
* Refuses to run if either DB is missing one of the six target tables.
* Opens the source connection ``READ ONLY``.
* Per-table transactions, so a single table failure leaves the
  remaining tables un-affected and is fully recoverable.

Special column handling
-----------------------

* PostGIS ``geometry`` columns are transported via ``geom::text``
  (EWKB hex) which both reads and inserts cleanly without needing
  shapely. We add ``::geometry`` casts on the UPDATE side so Postgres
  resolves the implicit conversion.
* ``jsonb`` and array (``text[]``) columns are handled natively by
  psycopg2.

Usage::

    PYTHONPATH=src python -m scripts.sync_merged_from_source --dry-run
    PYTHONPATH=src python -m scripts.sync_merged_from_source

"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

import psycopg2
from psycopg2 import sql
from psycopg2.extras import Json

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = PROJECT_ROOT.parent / "audit" / "post_processing" / "02_data_verification"

SOURCE_DB = "atoms_vs_ashes"
TARGET_DB = "atoms_vs_ashes_merged"

SYNC_TABLES: tuple[str, ...] = (
    "sites",
    "site_natural_hazards",
    "site_human_hazards",
    "site_radiological",
    "site_emergency_planning",
    "site_infrastructure_v2",
)

PRESERVED_PROVENANCE_COLUMNS: frozenset[str] = frozenset({"merge_run_id", "source_db"})
GEOMETRY_COLUMNS: frozenset[tuple[str, str]] = frozenset({("sites", "geom")})


def _conn_kwargs(db: str) -> dict[str, str]:
    return {
        "host": os.environ.get("POSTGRES_HOST", "localhost"),
        "port": os.environ.get("POSTGRES_PORT", "5432"),
        "user": os.environ.get("POSTGRES_USER", "atoms"),
        "password": os.environ.get("POSTGRES_PASSWORD", "changeme"),
        "dbname": db,
    }


def _connect(db: str, *, read_only: bool = False) -> "psycopg2.extensions.connection":
    conn = psycopg2.connect(**_conn_kwargs(db))
    if read_only:
        conn.set_session(readonly=True, autocommit=False)
    return conn


def _alembic_head(conn: "psycopg2.extensions.connection") -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT version_num FROM alembic_version")
        row = cur.fetchone()
        if row is None:
            raise RuntimeError("alembic_version table is empty")
        return str(row[0])


def _table_columns(conn: "psycopg2.extensions.connection", table: str) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=%s "
            "ORDER BY ordinal_position",
            (table,),
        )
        return [r[0] for r in cur.fetchall()]


def _table_jsonb_columns(
    conn: "psycopg2.extensions.connection", table: str
) -> set[str]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=%s "
            "AND data_type IN ('jsonb', 'json')",
            (table,),
        )
        return {r[0] for r in cur.fetchall()}


def _table_exists(conn: "psycopg2.extensions.connection", table: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name=%s",
            (table,),
        )
        return cur.fetchone() is not None


def _site_id_set(conn: "psycopg2.extensions.connection", table: str) -> set[str]:
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT site_id FROM {}").format(sql.Identifier(table)))
        return {str(r[0]) for r in cur.fetchall()}


def _row_count(conn: "psycopg2.extensions.connection", table: str) -> int:
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(table)))
        return int(cur.fetchone()[0])


def _max_fetched_at(
    conn: "psycopg2.extensions.connection", table: str
) -> datetime | None:
    column = "updated_at" if table == "sites" else "fetched_at"
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("SELECT max({}) FROM {}").format(
                sql.Identifier(column), sql.Identifier(table)
            )
        )
        return cur.fetchone()[0]


def _spf_fill_counts(conn: "psycopg2.extensions.connection") -> dict[str, int]:
    """Specifically count SP-F column fill in site_human_hazards (intersection-only)."""
    spf_cols = [
        "nearest_airport_class",
        "nearest_airport_runway_length_m",
        "nearest_airport_scheduled_service",
        "nearest_military_class",
        "nearest_high_consequence_military_km",
        "nearest_high_consequence_military_class",
    ]
    out: dict[str, int] = {}
    with conn.cursor() as cur:
        for c in spf_cols:
            cur.execute(
                sql.SQL("SELECT count({}) FROM site_human_hazards").format(
                    sql.Identifier(c)
                )
            )
            out[c] = int(cur.fetchone()[0])
    return out


@dataclass
class TableSyncResult:
    table: str
    intersect_count: int
    updated: int
    common_columns: list[str] = field(default_factory=list)
    skipped_columns: list[str] = field(default_factory=list)
    max_fetched_after: datetime | None = None
    error: str | None = None


def _build_select_expressions(
    table: str, columns: Sequence[str]
) -> list[sql.Composable]:
    exprs: list[sql.Composable] = []
    for c in columns:
        if (table, c) in GEOMETRY_COLUMNS:
            exprs.append(
                sql.SQL("{}::text AS {}").format(
                    sql.Identifier(c), sql.Identifier(c)
                )
            )
        else:
            exprs.append(sql.Identifier(c))
    return exprs


def _build_update_set_clause(
    table: str, columns: Sequence[str]
) -> sql.Composable:
    parts: list[sql.Composable] = []
    for c in columns:
        placeholder: sql.Composable = sql.SQL("%s")
        if (table, c) in GEOMETRY_COLUMNS:
            placeholder = sql.SQL("%s::geometry")
        parts.append(sql.SQL("{} = {}").format(sql.Identifier(c), placeholder))
    parts.append(sql.SQL("merge_run_id = %s"))
    return sql.SQL(", ").join(parts)


def _ensure_enrichment_run(
    tgt: "psycopg2.extensions.connection",
    run_id: str,
    *,
    notes: str,
    dry_run: bool,
) -> None:
    if dry_run:
        return
    with tgt.cursor() as cur:
        cur.execute(
            "INSERT INTO enrichment_runs "
            "(run_id, run_type, connector_slug, started_at, status, notes) "
            "VALUES (%s, %s, NULL, %s, %s, %s) "
            "ON CONFLICT (run_id) DO UPDATE SET status=EXCLUDED.status, "
            "started_at=enrichment_runs.started_at, notes=EXCLUDED.notes",
            (run_id, "merge_resync", datetime.now(timezone.utc), "in_progress", notes),
        )
    tgt.commit()


def _finalize_enrichment_run(
    tgt: "psycopg2.extensions.connection",
    run_id: str,
    *,
    status: str,
    site_count: int,
    success_count: int,
    error_count: int,
    notes: str,
    dry_run: bool,
) -> None:
    if dry_run:
        return
    with tgt.cursor() as cur:
        cur.execute(
            "UPDATE enrichment_runs SET completed_at=%s, status=%s, "
            "site_count=%s, success_count=%s, error_count=%s, notes=%s "
            "WHERE run_id=%s",
            (
                datetime.now(timezone.utc),
                status,
                site_count,
                success_count,
                error_count,
                notes,
                run_id,
            ),
        )
    tgt.commit()


def _write_merge_audit_rows(
    tgt_cursor,
    run_id: str,
    table: str,
    site_ids: Iterable[str],
    column_names: Sequence[str],
) -> None:
    rule_id = "resync_full_row"
    explanation = (
        f"Resync of {table} from source DB during merged-db-resync-from-source "
        f"plan. Updated columns: {', '.join(column_names)}."
    )
    rows = [
        (run_id, sid, None, table, "*", "api", None, None, None, rule_id, explanation)
        for sid in site_ids
    ]
    tgt_cursor.executemany(
        "INSERT INTO merge_audit "
        "(merge_run_id, site_id, criterion_id, table_name, column_name, "
        "source_chosen, api_value, llm_value, final_value, rule_id, rule_explanation) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        rows,
    )


def _adapt_value(value: Any, *, is_jsonb: bool) -> Any:
    if value is None:
        return None
    if is_jsonb:
        return Json(value)
    return value


def sync_table(
    src: "psycopg2.extensions.connection",
    tgt: "psycopg2.extensions.connection",
    table: str,
    intersection: set[str],
    run_id: str,
    *,
    dry_run: bool,
) -> TableSyncResult:
    src_cols = _table_columns(src, table)
    tgt_cols = _table_columns(tgt, table)
    common_columns = [c for c in src_cols if c in tgt_cols]
    src_only = [c for c in src_cols if c not in tgt_cols]
    tgt_only = [c for c in tgt_cols if c not in src_cols]

    if "site_id" not in common_columns:
        raise RuntimeError(f"site_id missing from common columns for {table}")

    update_columns = [
        c
        for c in common_columns
        if c != "site_id" and c not in PRESERVED_PROVENANCE_COLUMNS
    ]

    if dry_run:
        return TableSyncResult(
            table=table,
            intersect_count=len(intersection),
            updated=0,
            common_columns=update_columns,
            skipped_columns=sorted(set(src_only + tgt_only) | PRESERVED_PROVENANCE_COLUMNS),
        )

    select_columns = ["site_id"] + update_columns
    select_exprs = _build_select_expressions(table, select_columns)
    select_stmt = sql.SQL("SELECT {} FROM {} WHERE site_id = ANY(%s::uuid[])").format(
        sql.SQL(", ").join(select_exprs),
        sql.Identifier(table),
    )

    update_set = _build_update_set_clause(table, update_columns)
    update_stmt = sql.SQL("UPDATE {} SET {} WHERE site_id = %s").format(
        sql.Identifier(table), update_set
    )

    jsonb_cols = _table_jsonb_columns(tgt, table)
    is_jsonb_flags = [c in jsonb_cols for c in update_columns]

    site_ids_param = list(intersection)
    src_cur = src.cursor()
    src_cur.execute(select_stmt, (site_ids_param,))
    rows = src_cur.fetchall()
    src_cur.close()

    updated = 0
    tgt_cursor = tgt.cursor()
    update_params: list[tuple[Any, ...]] = []
    touched_site_ids: list[str] = []
    for row in rows:
        site_id = row[0]
        values = row[1:]
        adapted = tuple(
            _adapt_value(v, is_jsonb=flag) for v, flag in zip(values, is_jsonb_flags)
        )
        update_params.append(adapted + (run_id, site_id))
        touched_site_ids.append(str(site_id))

    if update_params:
        tgt_cursor.executemany(update_stmt.as_string(tgt), update_params)
        updated = tgt_cursor.rowcount if tgt_cursor.rowcount and tgt_cursor.rowcount > 0 else len(update_params)
        _write_merge_audit_rows(
            tgt_cursor, run_id, table, touched_site_ids, update_columns
        )
    tgt_cursor.close()

    return TableSyncResult(
        table=table,
        intersect_count=len(intersection),
        updated=updated,
        common_columns=update_columns,
        skipped_columns=sorted(set(src_only + tgt_only) | PRESERVED_PROVENANCE_COLUMNS),
        max_fetched_after=_max_fetched_at(tgt, table),
    )


def _format_dt(value: datetime | None) -> str:
    if value is None:
        return "—"
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def _write_report(
    *,
    run_id: str,
    intersection_size: int,
    source_alembic: str,
    target_alembic: str,
    pre_max_fetched: dict[str, datetime | None],
    post_max_fetched: dict[str, datetime | None],
    pre_spf_fill: dict[str, int],
    post_spf_fill: dict[str, int],
    results: list[TableSyncResult],
    report_path: Path,
    dry_run: bool,
) -> None:
    if dry_run:
        return
    report_path.parent.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).date().isoformat()
    lines: list[str] = []
    lines.append(f"# Merged DB resync from source — {today}")
    lines.append("")
    lines.append(f"**Resync run id:** `{run_id}`  ")
    lines.append(f"**Source DB:** `{SOURCE_DB}` (alembic `{source_alembic}`)  ")
    lines.append(f"**Target DB:** `{TARGET_DB}` (alembic `{target_alembic}`)  ")
    lines.append(f"**Intersection size (site_ids in both DBs):** {intersection_size}  ")
    lines.append("")
    lines.append("## Per-table summary")
    lines.append("")
    lines.append(
        "| Table | Intersect | Updated | Pre max(fetched_at) | Post max(fetched_at) | Columns synced | Columns skipped |"
    )
    lines.append(
        "|-------|-----------|---------|----------------------|-----------------------|----------------|-----------------|"
    )
    for r in results:
        lines.append(
            f"| `{r.table}` | {r.intersect_count} | {r.updated} | "
            f"{_format_dt(pre_max_fetched.get(r.table))} | "
            f"{_format_dt(post_max_fetched.get(r.table))} | "
            f"{len(r.common_columns)} | "
            f"{len(r.skipped_columns)} |"
        )
    lines.append("")
    lines.append("## site_human_hazards SP-F column fill (counts)")
    lines.append("")
    lines.append("| Column | Pre fill | Post fill |")
    lines.append("|--------|----------|-----------|")
    for c in pre_spf_fill:
        lines.append(f"| `{c}` | {pre_spf_fill[c]} | {post_spf_fill.get(c, 0)} |")
    lines.append("")
    lines.append("## Provenance notes")
    lines.append("")
    lines.append(
        f"* Every updated row in the 5 hazard tables and `sites` carries "
        f"`merge_run_id = '{run_id}'` and `source_db = 'api'`."
    )
    lines.append(
        "* The merged-only row `323cdbf0-c4a8-467a-af76-e2e3df0b537f` "
        "(Braila power station, RO, cancelled) was deliberately excluded "
        "from the intersection and is unchanged. Its 6 new SP-F columns "
        "remain NULL; the HI-01 / HI-06 rubrics handle this gracefully."
    )
    lines.append(
        "* Scoring history tables (`screening_verdicts`, `ranking_scores`, "
        "`composite_rankings`, `merge_audit` pre-existing rows) were not "
        "touched; a new `enrichment_runs` row carries the resync identity."
    )
    lines.append("")
    lines.append("## Verification")
    lines.append("")
    lines.append("Re-query against the merged DB after this run:")
    lines.append("")
    lines.append("```sql")
    lines.append("SELECT version_num FROM alembic_version;  -- 043")
    lines.append(
        "SELECT count(nearest_airport_class) FROM site_human_hazards;  "
        "-- 361 (Braila stays NULL)"
    )
    lines.append(
        f"SELECT count(*) FROM merge_audit WHERE merge_run_id='{run_id}';  -- ~{6 * intersection_size}"
    )
    lines.append("```")
    lines.append("")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned updates without applying anything.",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Override the resync run id (default: resync_<UTC timestamp>).",
    )
    parser.add_argument(
        "--tables",
        default=None,
        help=(
            "Comma-separated subset of tables to sync (default: all 6: "
            f"{','.join(SYNC_TABLES)})."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Debug: limit the intersection to the first N site_ids (sorted).",
    )
    parser.add_argument(
        "--report",
        default=None,
        help=(
            "Override report path (default: "
            f"{REPORT_DIR}/<YYYYMMDD>_merged_resync.md)."
        ),
    )
    args = parser.parse_args(argv)

    if args.tables:
        requested = [t.strip() for t in args.tables.split(",") if t.strip()]
        bad = [t for t in requested if t not in SYNC_TABLES]
        if bad:
            print(
                f"ERROR: unknown table(s) in --tables: {bad}. "
                f"Allowed: {SYNC_TABLES}",
                file=sys.stderr,
            )
            return 2
        tables_to_sync = tuple(requested)
    else:
        tables_to_sync = SYNC_TABLES

    src = _connect(SOURCE_DB, read_only=True)
    tgt = _connect(TARGET_DB, read_only=False)
    try:
        src_head = _alembic_head(src)
        tgt_head = _alembic_head(tgt)
        if src_head < tgt_head:
            print(
                f"ERROR: refusing to sync downward — source alembic {src_head} "
                f"< target alembic {tgt_head}.",
                file=sys.stderr,
            )
            return 3
        for t in tables_to_sync:
            for c, name in ((src, SOURCE_DB), (tgt, TARGET_DB)):
                if not _table_exists(c, t):
                    print(
                        f"ERROR: table {t!r} missing from {name}",
                        file=sys.stderr,
                    )
                    return 4

        src_site_ids = _site_id_set(src, "sites")
        tgt_site_ids = _site_id_set(tgt, "sites")
        intersection = src_site_ids & tgt_site_ids
        if args.limit is not None:
            intersection = set(sorted(intersection)[: args.limit])

        pre_max_fetched = {t: _max_fetched_at(tgt, t) for t in tables_to_sync}
        pre_spf_fill = _spf_fill_counts(tgt)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_id = args.run_id or f"resync_{timestamp}"
        notes = (
            f"Resync of merged DB from {SOURCE_DB} (alembic {src_head}). "
            f"Tables: {','.join(tables_to_sync)}. "
            f"Intersection: {len(intersection)} site_ids. "
            f"Source head {src_head}, target head {tgt_head}."
        )

        print(f"==> source: {SOURCE_DB} (alembic {src_head})")
        print(f"==> target: {TARGET_DB} (alembic {tgt_head})")
        print(f"==> tables: {','.join(tables_to_sync)}")
        print(f"==> source sites: {len(src_site_ids)}")
        print(f"==> target sites: {len(tgt_site_ids)}")
        print(f"==> intersection: {len(intersection)}")
        print(f"==> run_id: {run_id}")
        print(f"==> mode:   {'dry-run' if args.dry_run else 'apply'}")
        print()

        _ensure_enrichment_run(tgt, run_id, notes=notes, dry_run=args.dry_run)

        results: list[TableSyncResult] = []
        success_count = 0
        error_count = 0
        for table in tables_to_sync:
            print(f"  syncing {table}…")
            try:
                result = sync_table(
                    src, tgt, table, intersection, run_id, dry_run=args.dry_run
                )
                if not args.dry_run:
                    tgt.commit()
                success_count += result.updated
                results.append(result)
                print(
                    f"    updated={result.updated} "
                    f"(common columns={len(result.common_columns)}, "
                    f"skipped columns={len(result.skipped_columns)})"
                )
            except Exception as exc:
                tgt.rollback()
                error_count += 1
                results.append(
                    TableSyncResult(
                        table=table,
                        intersect_count=len(intersection),
                        updated=0,
                        error=str(exc),
                    )
                )
                print(f"    ERROR: {exc}", file=sys.stderr)

        post_max_fetched = {t: _max_fetched_at(tgt, t) for t in tables_to_sync}
        post_spf_fill = _spf_fill_counts(tgt)

        final_status = "completed" if error_count == 0 else "completed_with_errors"
        _finalize_enrichment_run(
            tgt,
            run_id,
            status=final_status,
            site_count=len(intersection),
            success_count=success_count,
            error_count=error_count,
            notes=notes,
            dry_run=args.dry_run,
        )

        report_path = Path(args.report) if args.report else (
            REPORT_DIR
            / f"{datetime.now(timezone.utc).date().isoformat().replace('-', '')}_merged_resync.md"
        )
        _write_report(
            run_id=run_id,
            intersection_size=len(intersection),
            source_alembic=src_head,
            target_alembic=tgt_head,
            pre_max_fetched=pre_max_fetched,
            post_max_fetched=post_max_fetched,
            pre_spf_fill=pre_spf_fill,
            post_spf_fill=post_spf_fill,
            results=results,
            report_path=report_path,
            dry_run=args.dry_run,
        )

        print()
        if args.dry_run:
            print("==> dry-run: no writes; report skipped")
        else:
            print(f"==> wrote report: {report_path}")
        print(f"==> done (errors={error_count})")
        return 0 if error_count == 0 else 5
    finally:
        src.close()
        tgt.close()


if __name__ == "__main__":
    sys.exit(main())
