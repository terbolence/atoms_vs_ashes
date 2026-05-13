# man_hours: 1.6
"""Replay HI-06 military classification from logged OSM raw responses.

The April 19-21 enrichment run dual-wrote every Overpass call into
``site_raw_responses`` (per ``raw-response-logging.mdc``). For HI-06 the
relevant payload lives at::

    response_body['results'][i]['data']  where  ['type'] == 'military'

That ``data`` is a ``list[{lat, lon, tags, osm_id}]`` -- exactly what
``classify_military_element`` and ``assess_military_proximity`` consume.
This script walks the logged rows, recomputes the SP-F enrichment fields
introduced by Alembic migration ``042``, and writes them to
``site_human_hazards``::

    nearest_military_class
    nearest_high_consequence_military_km
    nearest_high_consequence_military_class

The legacy fields (``nearest_military_km``, ``nearest_military_name``,
``military_count``, ``hi06_quality``) read by the HI-06 rubric are
**deliberately not touched** -- composite scoring stays byte-identical
across the replay. No live HTTP is performed; runs in seconds.

Usage::

    PYTHONPATH=src .venv/bin/python src/scripts/replay_osm_military_from_logs.py
    PYTHONPATH=src .venv/bin/python src/scripts/replay_osm_military_from_logs.py \
        --country RO,BG --requery-nulls
    PYTHONPATH=src .venv/bin/python src/scripts/replay_osm_military_from_logs.py \
        --site-id 28c80d72-dd9e-4fbf-a2c7-d48d49ca61dc --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from dotenv import load_dotenv

load_dotenv(Path.cwd() / ".env")


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


def _wrap_elements(raw_elements: list[dict[str, Any]]) -> list[Any]:
    """Wrap raw OSM dicts into the OverpassElement-shaped duck type.

    ``classify_military_element`` and ``assess_military_proximity`` only
    read ``.lat``, ``.lon``, and ``.tags``; ``SimpleNamespace`` is enough.
    """
    wrapped: list[Any] = []
    for el in raw_elements or []:
        if not isinstance(el, dict):
            continue
        lat = el.get("lat")
        lon = el.get("lon")
        tags = el.get("tags") or {}
        wrapped.append(SimpleNamespace(lat=lat, lon=lon, tags=tags))
    return wrapped


def _extract_military_data(body: Any) -> list[dict[str, Any]] | None:
    """Pull the military element list out of an osm raw_responses body.

    Returns ``None`` when the audit-style payload is absent (e.g. the row
    came from a non-audit code path), an empty list when the audit ran
    successfully but found nothing in radius, or the raw element list.
    """
    if not isinstance(body, dict):
        return None
    results = body.get("results")
    if not isinstance(results, list):
        return None
    for entry in results:
        if not isinstance(entry, dict):
            continue
        if entry.get("type") != "military":
            continue
        if "error" in entry:
            return None
        data = entry.get("data")
        if data is None:
            return None
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            els = data.get("elements")
            return els if isinstance(els, list) else None
    return None


SP_F_HI06_COLUMNS: tuple[str, ...] = (
    "nearest_military_class",
    "nearest_high_consequence_military_km",
    "nearest_high_consequence_military_class",
)


def decide_hi06_writes(
    *,
    current: dict[str, Any],
    replayed: dict[str, Any],
    only_nulls: bool,
    overwrite_with_better: bool,
) -> dict[str, str]:
    """Per-column verdict for HI-06 SP-F columns. Pure; mirror of HI-01.

    Returns a mapping ``{column -> action}`` where action is one of
    ``"write-null"``, ``"overwrite"``, ``"skip-nonnull"``,
    ``"skip-noop"``, ``"skip-no-replay"``.
    """
    out: dict[str, str] = {}
    for col in SP_F_HI06_COLUMNS:
        cur = current.get(col)
        rep = replayed.get(col)
        if rep is None:
            out[col] = "skip-no-replay"
            continue
        if cur is None:
            out[col] = "write-null"
            continue
        if _values_equal_hi06(cur, rep):
            out[col] = "skip-noop"
            continue
        if overwrite_with_better and not only_nulls:
            out[col] = "overwrite"
        else:
            out[col] = "skip-nonnull"
    return out


def _values_equal_hi06(a: Any, b: Any) -> bool:
    """Tolerant equality: 1 km for distances, exact for class strings."""
    try:
        fa = float(a)
        fb = float(b)
        return abs(fa - fb) < 1.0
    except (TypeError, ValueError):
        return a == b


def _current_hi06_state(session, site_id: uuid.UUID) -> dict[str, Any]:
    from atoms_vs_ashes.db.models import SiteHumanHazards

    row = session.get(SiteHumanHazards, site_id)
    if row is None:
        return {col: None for col in SP_F_HI06_COLUMNS}
    return {col: getattr(row, col, None) for col in SP_F_HI06_COLUMNS}


def _persist_sp_f_only(
    session, site_id: uuid.UUID, decisions: dict[str, str],
    replayed: dict[str, Any],
) -> int:
    """UPDATE only the SP-F columns whose decision permits a write."""
    from atoms_vs_ashes.db.models import SiteHumanHazards

    to_write = {
        col: replayed[col]
        for col, action in decisions.items()
        if action in {"write-null", "overwrite"}
    }
    if not to_write:
        return 0
    row = session.get(SiteHumanHazards, site_id)
    if row is None:
        row = SiteHumanHazards(site_id=site_id)
        session.add(row)
    for col, value in to_write.items():
        setattr(row, col, value)
    return len(to_write)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Replay HI-06 military SP-F enrichment from logged OSM raw responses",
    )
    p.add_argument(
        "--country",
        help="Comma-separated ISO country codes (e.g. RO,BG); restricts replay to those countries.",
    )
    p.add_argument(
        "--site-id", action="append", default=[],
        help="Restrict to specific site UUIDs (repeatable).",
    )
    p.add_argument(
        "--requery-nulls", action="store_true",
        help="Skip sites where nearest_military_class is already populated.",
    )
    mode = p.add_mutually_exclusive_group()
    mode.add_argument(
        "--only-nulls", action="store_true",
        help="(default) Write a SP-F column only when the current DB value is NULL.",
    )
    mode.add_argument(
        "--overwrite-with-better", action="store_true",
        help="Also overwrite non-null SP-F columns when the replayed value differs. "
             "Each overwrite is recorded in the per-site summary with current/replayed evidence.",
    )
    p.add_argument(
        "--dry-run", action="store_true",
        help="Compute and print results, do not commit DB changes.",
    )
    p.add_argument(
        "--json-summary", type=Path, default=None,
        help="Optional path to write a per-site JSON summary.",
    )
    return p.parse_args()


def main() -> int:
    from sqlalchemy import text

    from atoms_vs_ashes.analysis.military_proximity import (
        HIGH_CONSEQUENCE_CLASSES,
        assess_military_proximity,
    )
    from atoms_vs_ashes.db.models import Site

    args = _parse_args()
    only_nulls = args.only_nulls or not args.overwrite_with_better
    mode = "overwrite-with-better" if args.overwrite_with_better else "only-nulls"
    session = _build_session()

    sites_q = session.query(Site)
    if args.country:
        codes = [c.strip().upper() for c in args.country.split(",") if c.strip()]
        sites_q = sites_q.filter(Site.country_code.in_(codes))
    if args.site_id:
        ids = [uuid.UUID(s) for s in args.site_id]
        sites_q = sites_q.filter(Site.site_id.in_(ids))
    sites = {s.site_id: s for s in sites_q.all()}
    if not sites:
        print("No sites match the filter; nothing to do.")
        return 0

    raw_rows = session.execute(
        text(
            "SELECT site_id, response_body "
            "FROM site_raw_responses "
            "WHERE connector_slug = 'osm' "
            "  AND site_id = ANY(:site_ids)"
        ),
        {"site_ids": list(sites.keys())},
    ).fetchall()
    raw_by_site: dict[uuid.UUID, Any] = {r.site_id: r.response_body for r in raw_rows}

    summary = {
        "total_sites": len(sites),
        "with_logged_payload": 0,
        "no_logged_payload": 0,
        "skipped_already_populated": 0,
        "with_class_assigned": 0,
        "with_high_consequence": 0,
        "errors": 0,
        "per_site": [],
    }

    skip_lookup: dict[uuid.UUID, str | None] = {}
    if args.requery_nulls:
        from atoms_vs_ashes.db.models import SiteHumanHazards

        rows = session.query(
            SiteHumanHazards.site_id, SiteHumanHazards.nearest_military_class
        ).filter(SiteHumanHazards.site_id.in_(sites.keys())).all()
        skip_lookup = {r.site_id: r.nearest_military_class for r in rows}

    for site_id, site in sites.items():
        if args.requery_nulls and skip_lookup.get(site_id) is not None:
            summary["skipped_already_populated"] += 1
            continue

        body = raw_by_site.get(site_id)
        if body is None:
            summary["no_logged_payload"] += 1
            summary["per_site"].append({
                "site_id": str(site_id), "country": site.country_code,
                "name": site.name, "status": "no_logged_payload",
            })
            continue

        data = _extract_military_data(body)
        if data is None:
            summary["no_logged_payload"] += 1
            summary["per_site"].append({
                "site_id": str(site_id), "country": site.country_code,
                "name": site.name, "status": "no_military_payload",
            })
            continue

        summary["with_logged_payload"] += 1
        try:
            elements = _wrap_elements(data)
            result = assess_military_proximity(
                lat=float(site.latitude), lon=float(site.longitude),
                elements=elements,
            )
        except Exception as exc:
            summary["errors"] += 1
            summary["per_site"].append({
                "site_id": str(site_id), "country": site.country_code,
                "name": site.name, "status": "error", "error": str(exc),
            })
            continue

        if result.nearest_class is not None:
            summary["with_class_assigned"] += 1
        if result.nearest_high_consequence_km is not None:
            summary["with_high_consequence"] += 1

        replayed_values = {
            "nearest_military_class": result.nearest_class,
            "nearest_high_consequence_military_km": result.nearest_high_consequence_km,
            "nearest_high_consequence_military_class": result.nearest_high_consequence_class,
        }
        current_state = _current_hi06_state(session, site_id)
        decisions = decide_hi06_writes(
            current=current_state, replayed=replayed_values,
            only_nulls=only_nulls,
            overwrite_with_better=args.overwrite_with_better,
        )

        write_count = 0
        if not args.dry_run:
            write_count = _persist_sp_f_only(
                session, site_id, decisions=decisions, replayed=replayed_values,
            )

        summary["per_site"].append({
            "site_id": str(site_id),
            "country": site.country_code,
            "name": site.name,
            "elements": len(elements),
            "nearest_class": result.nearest_class,
            "nearest_distance_km": result.nearest_distance_km,
            "high_consequence_km": result.nearest_high_consequence_km,
            "high_consequence_class": result.nearest_high_consequence_class,
            "class_counts": result.class_counts,
            "evidence": [
                {
                    "column": col,
                    "current": str(current_state[col]) if current_state[col] is not None else None,
                    "replayed": (
                        str(replayed_values[col])
                        if replayed_values[col] is not None else None
                    ),
                    "action": decisions[col],
                }
                for col in SP_F_HI06_COLUMNS
            ],
            "writes_planned": sum(
                1 for a in decisions.values() if a in {"write-null", "overwrite"}
            ),
            "writes_committed": write_count,
        })

    if not args.dry_run:
        session.commit()

    print("\n=== HI-06 military log-replay summary ===")
    print(f"  Total sites considered:          {summary['total_sites']}")
    print(f"  With logged military payload:    {summary['with_logged_payload']}")
    print(f"  Without logged payload:          {summary['no_logged_payload']}")
    print(f"  Skipped (already populated):     {summary['skipped_already_populated']}")
    print(f"  With nearest_military_class set: {summary['with_class_assigned']}")
    print(f"  With high-consequence flagged:   {summary['with_high_consequence']}")
    print(f"  Errors:                          {summary['errors']}")
    print(f"  Mode:                            {mode}{' (DRY-RUN)' if args.dry_run else ''}")
    print(f"  High-consequence classes:        {sorted(HIGH_CONSEQUENCE_CLASSES)}")
    rows_with_writes = sum(
        1 for ps in summary['per_site'] if isinstance(ps, dict) and ps.get('writes_committed', 0)
    )
    print(f"  Rows with at least one write:    {rows_with_writes}")

    if args.json_summary:
        args.json_summary.write_text(json.dumps(summary, indent=2, default=str))
        print(f"  Per-site JSON summary written:   {args.json_summary}")

    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
