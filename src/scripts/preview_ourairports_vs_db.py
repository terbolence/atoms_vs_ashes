# man_hours: 1.0
"""Preview HI-01 OurAirports enrichment vs current DB state (no DB writes).

Computes the same `AirportProximityResult` that
``run_p10_ourairports_batch.py`` would persist, but **does not** write
to the database. See
``audit/post_processing/hi01_preview/README.md`` for full operational
notes. Pure diff/render logic lives in :mod:`_preview_ourairports_diff`.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv(Path.cwd() / ".env")

sys.path.insert(0, str(Path(__file__).parent))
from _preview_ourairports_diff import (  # noqa: E402
    HI01_COLUMNS, ColumnDiff, diff_site, render_report_md,
)


def _build_session():
    from atoms_vs_ashes.db.engine import get_engine
    from sqlalchemy.orm import sessionmaker

    engine = get_engine()
    if engine is None:
        sys.exit(
            "ERROR: Could not initialise the database engine; check "
            "POSTGRES_HOST/USER/PASSWORD/DB env vars."
        )
    return sessionmaker(bind=engine, future=True)()


def _current_db_state(session, site_id: uuid.UUID) -> dict[str, Any]:
    from atoms_vs_ashes.db.models import SiteHumanHazards

    row = session.get(SiteHumanHazards, site_id)
    if row is None:
        return {col: None for col in HI01_COLUMNS}
    return {col: getattr(row, col, None) for col in HI01_COLUMNS}


def _serialise(v: Any) -> Any:
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, uuid.UUID):
        return str(v)
    return v


def _serialise_diff(d: ColumnDiff) -> dict[str, Any]:
    return {"column": d.column,
            "current": _serialise(d.current),
            "proposed": _serialise(d.proposed)}


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Preview HI-01 OurAirports enrichment for all sites and diff "
            "against current DB state. No DB writes."
        ),
    )
    p.add_argument("--country",
                   help="Comma-separated ISO country codes (e.g. RO,BG); restricts the preview.")
    p.add_argument("--site-id", action="append", default=[],
                   help="Restrict to specific site UUIDs (repeatable).")
    p.add_argument("--jsonl", type=Path,
                   default=Path("logs/hi01_preview_all.jsonl"),
                   help="Per-site JSONL output (default: logs/hi01_preview_all.jsonl).")
    p.add_argument("--report", type=Path,
                   default=Path("audit/post_processing/hi01_preview/hi01_preview_report.md"),
                   help="Markdown correction report path.")
    p.add_argument("--head-limit", type=int, default=50,
                   help="Cap on per-site detail blocks rendered in the markdown report.")
    p.add_argument("--radius-km", type=float, default=None,
                   help="Override the OurAirports search radius (default: connector setting).")
    return p.parse_args()


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def _fetch_one(connector, site, radius_km):
    if radius_km is not None:
        return connector.fetch(float(site.latitude), float(site.longitude),
                               radius_km=radius_km)
    return connector.fetch(float(site.latitude), float(site.longitude))


def main() -> int:
    from atoms_vs_ashes.connectors.ourairports import OurAirportsConnector
    from atoms_vs_ashes.db.models import Site

    args = _parse_args()
    run_id = (
        f"hi01-preview-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    )
    print(f"[{_ts()}] === HI-01 OurAirports preview (no DB writes) ===")
    print(f"[{_ts()}] Run ID: {run_id}")

    session = _build_session()
    sites_q = session.query(Site)
    if args.country:
        codes = [c.strip().upper() for c in args.country.split(",") if c.strip()]
        sites_q = sites_q.filter(Site.country_code.in_(codes))
    if args.site_id:
        ids = [uuid.UUID(s) for s in args.site_id]
        sites_q = sites_q.filter(Site.site_id.in_(ids))
    sites = sites_q.order_by(Site.country_code, Site.name).all()
    print(f"[{_ts()}] Sites in scope: {len(sites)}")
    if not sites:
        print("Nothing to preview.")
        return 0

    print(f"[{_ts()}] Building OurAirports index (cached if recent)...")
    connector = OurAirportsConnector()
    if not connector.health_check():
        print(f"[{_ts()}] ERROR: OurAirports endpoint unreachable; aborting.")
        return 1
    index = connector.load_index()
    print(f"[{_ts()}] Index: {index.airport_count} airports across "
          f"{len(index.countries_loaded)} countries")

    args.jsonl.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    sites_with_changes: list[dict[str, Any]] = []
    fetch_errors: list[dict[str, Any]] = []
    column_change_counts: dict[str, int] = {col: 0 for col in HI01_COLUMNS}
    sites_unchanged = 0

    with args.jsonl.open("w", encoding="utf-8") as jsonl_fh:
        for i, site in enumerate(sites, start=1):
            try:
                result = _fetch_one(connector, site, args.radius_km)
            except Exception as exc:
                fetch_errors.append({
                    "site_id": str(site.site_id), "name": site.name,
                    "country_code": site.country_code, "error": str(exc),
                })
                jsonl_fh.write(json.dumps({
                    "site_id": str(site.site_id), "name": site.name,
                    "country_code": site.country_code,
                    "status": "fetch_error", "error": str(exc),
                }) + "\n")
                continue

            proposed = result.to_dict()
            db_state = _current_db_state(session, site.site_id)
            diffs = diff_site(db_row=db_state, proposed=proposed)
            for d in diffs:
                column_change_counts[d.column] = (
                    column_change_counts.get(d.column, 0) + 1
                )
            if diffs:
                sites_with_changes.append({
                    "site_id": str(site.site_id), "name": site.name,
                    "country_code": site.country_code,
                    "diffs": [_serialise_diff(d) for d in diffs],
                })
            else:
                sites_unchanged += 1

            jsonl_fh.write(json.dumps({
                "site_id": str(site.site_id), "name": site.name,
                "country_code": site.country_code,
                "lat": float(site.latitude), "lon": float(site.longitude),
                "status": "diff" if diffs else "in_sync",
                "fetch": proposed,
                "db": {k: _serialise(v) for k, v in db_state.items()},
                "diff": [_serialise_diff(d) for d in diffs],
            }, default=str) + "\n")

            if i % 50 == 0:
                print(f"[{_ts()}] processed {i}/{len(sites)} | "
                      f"changes={len(sites_with_changes)} | "
                      f"in_sync={sites_unchanged} | errors={len(fetch_errors)}")

    connector.close()
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
    print(f"[{_ts()}] changes={len(sites_with_changes)} in_sync={sites_unchanged} "
          f"errors={len(fetch_errors)}")
    for col, n in column_change_counts.items():
        print(f"[{_ts()}]   {col:42s} would change on {n} sites")
    print(f"[{_ts()}] JSONL:  {args.jsonl}")
    print(f"[{_ts()}] Report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
