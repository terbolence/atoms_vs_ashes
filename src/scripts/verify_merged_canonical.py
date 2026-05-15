# man_hours: 2.0
"""Snapshot + diff helper for the merged-DB canonical cutover.

Usage
-----

Snapshot baseline (read-only against both DBs)::

    PYTHONPATH=src .venv/bin/python -m scripts.verify_merged_canonical \
        --baseline audit/post_processing/02_data_verification/canonical_baseline_<stamp>.json

Diff a later state against the recorded baseline::

    PYTHONPATH=src .venv/bin/python -m scripts.verify_merged_canonical \
        --against-baseline <baseline.json>

Both modes are read-only and require no live-API consent. The output
is intentionally compact JSON (machine-readable) plus a parallel
Markdown summary written next to the JSON.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DB_PROFILES = {
    "api": "atoms_vs_ashes",
    "merged": "atoms_vs_ashes_merged",
}

# Tables we always snapshot. New tables introduced after this script is
# written are picked up automatically via pg_tables, but we hard-code the
# canonical list so an unexpected schema change is visible in the diff.
SNAPSHOT_TABLES = (
    "alembic_version",
    "audit_log",
    "compiled_scoring_snapshots",
    "composite_rankings",
    "composite_score_components",
    "country_balance_check",
    "country_rankings_summary",
    "country_site_rankings",
    "criteria",
    "criterion_correlations",
    "data_sources",
    "dataset_snapshot",
    "enrichment_runs",
    "failure_aggregates",
    "failure_outcomes",
    "merge_audit",
    "oat_importance",
    "ranking_scores",
    "runs",
    "scoring_run_snapshots",
    "screening_verdicts",
    "site_bands",
    "site_emergency_planning",
    "site_human_hazards",
    "site_infrastructure_v2",
    "site_llm_observations",
    "site_llm_verdicts",
    "site_natural_hazards",
    "site_observations",
    "site_radiological",
    "site_raw_responses",
    "site_units",
    "sites",
    "smr_designs",
    "swing_weights",
    "threshold_overrides",
    "threshold_sensitivity",
    "weight_profile_stability",
)


def _engine_for(db: str):
    os.environ["POSTGRES_DB"] = db
    from atoms_vs_ashes.config import Settings

    return create_engine(Settings().database.url, pool_pre_ping=True)


def _table_exists(conn, table: str) -> bool:
    return bool(
        conn.execute(
            text(
                "SELECT 1 FROM pg_tables WHERE schemaname='public' "
                "AND tablename = :t"
            ),
            {"t": table},
        ).first()
    )


def _row_count(conn, table: str) -> int | None:
    if not _table_exists(conn, table):
        return None
    return conn.execute(text(f"SELECT count(*) FROM {table}")).scalar()


def _alembic_head(conn) -> str | None:
    if not _table_exists(conn, "alembic_version"):
        return None
    return conn.execute(text("SELECT version_num FROM alembic_version")).scalar()


def _run_ids(conn) -> list[str]:
    if not _table_exists(conn, "runs"):
        return []
    return [r[0] for r in conn.execute(text("SELECT run_id FROM runs")).all()]


def _site_ids(conn) -> list[str]:
    if not _table_exists(conn, "sites"):
        return []
    return [str(r[0]) for r in conn.execute(text("SELECT site_id FROM sites")).all()]


def _snapshot_one(db: str) -> dict:
    eng = _engine_for(db)
    with eng.connect() as conn:
        size = conn.execute(
            text("SELECT pg_database_size(current_database())")
        ).scalar()
        counts = {t: _row_count(conn, t) for t in SNAPSHOT_TABLES}
        return {
            "db": db,
            "size_bytes": int(size or 0),
            "alembic_head": _alembic_head(conn),
            "row_counts": counts,
            "run_ids": sorted(_run_ids(conn)),
            "site_ids": sorted(_site_ids(conn)),
        }


def snapshot(out_path: Path) -> dict:
    """Write a baseline snapshot for both DBs to ``out_path`` (JSON)."""
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dbs": {name: _snapshot_one(name) for name in DB_PROFILES.values()},
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, default=str))
    _write_markdown(out_path, payload)
    return payload


def _diff_counts(
    a: dict, b: dict,
) -> list[tuple[str, int | None, int | None, int | None]]:
    out: list[tuple[str, int | None, int | None, int | None]] = []
    for table in sorted(set(a) | set(b)):
        av, bv = a.get(table), b.get(table)
        delta: int | None
        delta = av - bv if isinstance(av, int) and isinstance(bv, int) else None
        out.append((table, av, bv, delta))
    return out


def diff(baseline_path: Path, label: str = "now") -> dict:
    baseline = json.loads(baseline_path.read_text())
    current = {name: _snapshot_one(name) for name in DB_PROFILES.values()}
    report: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "baseline_file": str(baseline_path),
        "baseline_generated_at": baseline.get("generated_at"),
        "label": label,
        "dbs": {},
    }
    for db_name in DB_PROFILES.values():
        base = baseline["dbs"][db_name]
        cur = current[db_name]
        report["dbs"][db_name] = {
            "alembic_baseline": base["alembic_head"],
            "alembic_current": cur["alembic_head"],
            "size_baseline": base["size_bytes"],
            "size_current": cur["size_bytes"],
            "size_delta": cur["size_bytes"] - base["size_bytes"],
            "runs_added": sorted(set(cur["run_ids"]) - set(base["run_ids"])),
            "runs_removed": sorted(set(base["run_ids"]) - set(cur["run_ids"])),
            "sites_added": sorted(set(cur["site_ids"]) - set(base["site_ids"])),
            "sites_removed": sorted(
                set(base["site_ids"]) - set(cur["site_ids"])
            ),
            "row_count_diff": [
                {"table": t, "before": a, "after": b, "delta": d}
                for t, a, b, d in _diff_counts(base["row_counts"], cur["row_counts"])
            ],
        }
    return report


def _write_markdown(json_path: Path, payload: dict) -> None:
    md_path = json_path.with_suffix(".md")
    lines = [
        f"# Canonical-DB snapshot ({payload['generated_at']})",
        "",
        "| DB | Alembic | Size | Runs | Sites |",
        "|---|---|---:|---:|---:|",
    ]
    for db_name, snap in payload["dbs"].items():
        lines.append(
            f"| `{db_name}` | `{snap['alembic_head']}` | "
            f"{snap['size_bytes']:,} B | "
            f"{len(snap['run_ids'])} | {len(snap['site_ids'])} |"
        )
    lines.append("")
    lines.append("## Per-table row counts")
    lines.append("")
    lines.append("| table | api | merged | api - merged |")
    lines.append("|---|---:|---:|---:|")
    api = payload["dbs"]["atoms_vs_ashes"]["row_counts"]
    mer = payload["dbs"]["atoms_vs_ashes_merged"]["row_counts"]
    for table in sorted(set(api) | set(mer)):
        a = api.get(table)
        m = mer.get(table)
        delta = a - m if isinstance(a, int) and isinstance(m, int) else "n/a"
        lines.append(
            f"| `{table}` | {a if a is not None else 'n/a'} | "
            f"{m if m is not None else 'n/a'} | {delta} |"
        )
    md_path.write_text("\n".join(lines) + "\n")


def _print_diff_human(report: dict) -> None:
    print(f"# Diff against {report['baseline_file']}")
    print(f"baseline_generated_at: {report['baseline_generated_at']}")
    print(f"now:                   {report['generated_at']}")
    for db_name, d in report["dbs"].items():
        print()
        print(f"## {db_name}")
        print(f"  alembic: {d['alembic_baseline']} -> {d['alembic_current']}")
        print(f"  size:    {d['size_baseline']:,} -> {d['size_current']:,} "
              f"(delta {d['size_delta']:+,})")
        if d["runs_added"]:
            print(f"  runs added (+{len(d['runs_added'])}): "
                  f"{', '.join(d['runs_added'][:5])}{' ...' if len(d['runs_added']) > 5 else ''}")
        if d["runs_removed"]:
            print(f"  runs removed (-{len(d['runs_removed'])}): "
                  f"{', '.join(d['runs_removed'][:5])}{' ...' if len(d['runs_removed']) > 5 else ''}")
        if d["sites_added"]:
            print(f"  sites added (+{len(d['sites_added'])}): "
                  f"{', '.join(d['sites_added'])}")
        if d["sites_removed"]:
            print(f"  sites removed (-{len(d['sites_removed'])}): "
                  f"{', '.join(d['sites_removed'])}")
        nontrivial = [r for r in d["row_count_diff"] if r["delta"] not in (0, None)]
        if nontrivial:
            print(f"  table count changes:")
            for r in nontrivial:
                print(f"    {r['table']:40s} {r['before']:>10} -> "
                      f"{r['after']:>10} ({r['delta']:+,})")


def _parse(argv: Iterable[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument(
        "--baseline", type=Path,
        help="Write a baseline snapshot JSON to this path.",
    )
    g.add_argument(
        "--against-baseline", type=Path,
        help="Diff the current state against an existing baseline JSON.",
    )
    p.add_argument(
        "--label", default="now",
        help="Optional label for the diff report (e.g. 'post-phase-2').",
    )
    p.add_argument(
        "--out", type=Path, default=None,
        help="Optional explicit output path for the diff JSON report.",
    )
    return p.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = _parse(argv)
    if args.baseline:
        snapshot(args.baseline)
        print(f"baseline written to {args.baseline}")
        return 0
    report = diff(args.against_baseline, label=args.label)
    _print_diff_human(report)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, default=str))
        print(f"\nDiff JSON written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
