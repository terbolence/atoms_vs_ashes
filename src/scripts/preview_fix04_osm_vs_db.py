# man_hours: 1.0
"""Preview FIX-04 OSM avoidance enrichment vs current DB state (no DB writes).

CLI orchestrator that drives Overpass + DB IO. Pure diff/render logic
lives in :mod:`_preview_fix04_diff`. See
``audit/post_processing/hi06_fix04_preview/README.md`` for full
operational notes.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

# Local helper module (pure logic, unit-testable):
sys.path.insert(0, str(Path(__file__).parent))
from _preview_fix04_diff import (  # noqa: E402
    DOMAINS, ColumnDiff, diff_domain, render_report_md, serialise, serialise_diff,
)


def _import_fix04():
    """Import FIX-04 batch as a module so we can reuse its parsers + retry logic."""
    name = "_fix04_batch_for_preview"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).with_name("run_fix04_osm_avoidance_batch.py"),
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _build_session():
    from atoms_vs_ashes.config import Settings
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    settings = Settings()
    engine = create_engine(settings.database.url, echo=False, pool_pre_ping=True)
    return sessionmaker(bind=engine, future=True)(), settings


def _fetch_db_state(session, site_id: uuid.UUID) -> dict[str, dict[str, Any]]:
    """Read the columns this preview compares for one site.

    Returns ``{domain_label: {db_column: value}}``. Missing rows produce
    a dict with all values ``None``.
    """
    from sqlalchemy import text as sa_text

    out: dict[str, dict[str, Any]] = {
        d.label: {col: None for _, col in d.columns} for d in DOMAINS
    }

    for table in {d.db_table for d in DOMAINS}:
        cols = [
            col for d in DOMAINS if d.db_table == table for _, col in d.columns
        ]
        if not cols:
            continue
        cols_sql = ", ".join(cols)
        row = session.execute(
            sa_text(f"SELECT {cols_sql} FROM {table} WHERE site_id = CAST(:sid AS uuid)"),
            {"sid": str(site_id)},
        ).mappings().first()
        if row is None:
            continue
        for d in DOMAINS:
            if d.db_table != table:
                continue
            for _, col in d.columns:
                out[d.label][col] = row.get(col)
    return out


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Preview FIX-04 OSM avoidance enrichment for all sites and diff "
            "against current DB state. No DB writes."
        ),
    )
    p.add_argument(
        "--country", dest="countries", metavar="CC,...",
        help="Comma-separated ISO country codes (e.g. RO,PL); restricts the preview.",
    )
    p.add_argument(
        "--site-id", action="append", default=[],
        help="Restrict to specific site UUIDs (repeatable).",
    )
    p.add_argument(
        "--jsonl", type=Path,
        default=Path("logs/hi06_fix04_preview.jsonl"),
        help="Per-site JSONL output (default: logs/hi06_fix04_preview.jsonl).",
    )
    p.add_argument(
        "--report", type=Path,
        default=Path("audit/post_processing/hi06_fix04_preview/hi06_fix04_preview_report.md"),
        help="Markdown correction report path.",
    )
    p.add_argument(
        "--head-limit", type=int, default=50,
        help="Cap on per-site detail blocks rendered in the markdown report.",
    )
    p.add_argument(
        "--max-sites", type=int, default=None,
        help="Hard cap on number of sites processed (useful for partial runs).",
    )
    return p.parse_args()


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def _run_one_site(*, fix04, client, session, site):
    """Fetch + parse + diff for one site. Returns (parsed, db_state, errors, diffs)."""
    lat, lon = float(site.latitude), float(site.longitude)
    parsed: dict[str, dict[str, Any] | None] = {}
    site_errors: dict[str, str] = {}

    fetchers = (
        ("military", client.fetch_military_areas,
         fix04._parse_military, fix04.MILITARY_RADIUS_KM),
        ("power", client.fetch_power_infrastructure,
         fix04._parse_power, fix04.POWER_RADIUS_KM),
        ("transmitter", client.fetch_transmitters,
         fix04._parse_transmitters, fix04.TRANSMITTER_RADIUS_KM),
    )
    for label, fetch_fn, parse_fn, radius in fetchers:
        try:
            elements = fix04._query_with_retry(fetch_fn, client, lat, lon, radius)
            parsed[label] = parse_fn(lat, lon, elements)
        except Exception as exc:
            parsed[label] = None
            site_errors[label] = str(exc)

    db_state = _fetch_db_state(session, site.site_id)
    diffs: list[ColumnDiff] = []
    for spec in DOMAINS:
        diffs.extend(diff_domain(
            spec=spec, parsed=parsed.get(spec.label), db_row=db_state[spec.label],
        ))
    return parsed, db_state, site_errors, diffs


def main() -> int:
    fix04 = _import_fix04()
    from atoms_vs_ashes.db.models import Site

    args = _parse_args()
    run_id = (
        f"hi06-fix04-preview-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    )

    print(f"[{_ts()}] === FIX-04 OSM preview (no DB writes) ===")
    print(f"[{_ts()}] Run ID: {run_id}")

    session, settings = _build_session()
    sites_q = session.query(Site)
    if args.countries:
        codes = [c.strip().upper() for c in args.countries.split(",") if c.strip()]
        sites_q = sites_q.filter(Site.country_code.in_(codes))
    if args.site_id:
        ids = [uuid.UUID(s) for s in args.site_id]
        sites_q = sites_q.filter(Site.site_id.in_(ids))
    sites = sites_q.order_by(Site.country_code, Site.name).all()
    if args.max_sites is not None:
        sites = sites[: args.max_sites]
    print(f"[{_ts()}] Sites in scope: {len(sites)}")
    if not sites:
        print("Nothing to preview.")
        return 0

    args.jsonl.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    client = fix04.OverpassClient(settings)

    sites_with_changes: list[dict[str, Any]] = []
    sites_unchanged = 0
    fetch_errors: dict[str, list[dict[str, Any]]] = {d.label: [] for d in DOMAINS}
    column_change_counts: dict[str, dict[str, int]] = {
        d.label: {col: 0 for _, col in d.columns} for d in DOMAINS
    }

    with args.jsonl.open("w", encoding="utf-8") as jsonl_fh:
        for i, site in enumerate(sites, start=1):
            parsed, db_state, site_errors, diffs = _run_one_site(
                fix04=fix04, client=client, session=session, site=site,
            )

            for label, err in site_errors.items():
                fetch_errors[label].append({
                    "site_id": str(site.site_id), "name": site.name,
                    "country_code": site.country_code, "error": err,
                })
            for d in diffs:
                column_change_counts[d.domain][d.column] = (
                    column_change_counts[d.domain].get(d.column, 0) + 1
                )

            if diffs:
                sites_with_changes.append({
                    "site_id": str(site.site_id),
                    "name": site.name,
                    "country_code": site.country_code,
                    "diffs": [serialise_diff(d) for d in diffs],
                })
            else:
                sites_unchanged += 1

            jsonl_fh.write(json.dumps({
                "site_id": str(site.site_id),
                "name": site.name,
                "country_code": site.country_code,
                "lat": float(site.latitude), "lon": float(site.longitude),
                "status": "diff" if diffs else "in_sync",
                "fetch": parsed,
                "fetch_errors": site_errors or None,
                "db": {label: {k: serialise(v) for k, v in cols.items()}
                       for label, cols in db_state.items()},
                "diff": [serialise_diff(d) for d in diffs],
            }, default=str) + "\n")
            jsonl_fh.flush()

            if i % 10 == 0 or i == len(sites):
                print(
                    f"[{_ts()}] processed {i}/{len(sites)} | "
                    f"changes={len(sites_with_changes)} | in_sync={sites_unchanged} | "
                    f"errors mil={len(fetch_errors['military'])} "
                    f"pwr={len(fetch_errors['power'])} "
                    f"tx={len(fetch_errors['transmitter'])}",
                    flush=True,
                )

    client.close()
    session.rollback()
    session.close()

    md = render_report_md(
        total_sites=len(sites),
        sites_with_changes=sites_with_changes,
        sites_unchanged=sites_unchanged,
        fetch_errors=fetch_errors,
        column_change_counts=column_change_counts,
        run_id=run_id,
        head_limit=args.head_limit,
    )
    args.report.write_text(md, encoding="utf-8")

    print(f"\n[{_ts()}] === Preview complete ===")
    print(f"[{_ts()}] changes={len(sites_with_changes)} in_sync={sites_unchanged}")
    for d in DOMAINS:
        print(f"[{_ts()}]   errors {d.label}/{d.criterion}: {len(fetch_errors[d.label])}")
    print(f"[{_ts()}] JSONL:  {args.jsonl}")
    print(f"[{_ts()}] Report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
