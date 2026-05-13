# man_hours: 1.4
"""Replay HI-01 airport SP-F columns from cached OurAirports CSVs.

Offline counterpart to ``replay_osm_military_from_logs.py``. Reads
``sources/ourairports/airports.csv`` + ``runways.csv`` (the bulk-CSV
"logs" -- the connector never writes a per-site ``site_raw_responses``
row), reruns ``compute_proximity_result`` for the requested sites, and
backfills only the SP-F columns added by Alembic migration ``042``::

    nearest_airport_class
    nearest_airport_runway_length_m
    nearest_airport_scheduled_service

Legacy HI-01 columns (``nearest_airport_km``, ``nearest_airport_type``,
``flight_path_distance_km``, ``airport_count``, ``hi01_quality``,
``hi01_comment``) are **never** touched by this script -- they belong to
the live-API enrichment pipeline. This guarantees the rubric snapshot
seen by composite scoring stays byte-identical until the user opts into
a fresh run from the GUI.

Default mode is ``--only-nulls``: a column is written if and only if its
current DB value is ``NULL``. ``--overwrite-with-better`` is the explicit
opt-in that allows updating a non-null column when the cached CSV
produces a different value; each such overwrite is recorded in the
preview/replay log with the current and replayed values plus the source
``ident``.

Usage::

    PYTHONPATH=src .venv/bin/python src/scripts/replay_ourairports_from_csv.py --dry-run
    PYTHONPATH=src .venv/bin/python src/scripts/replay_ourairports_from_csv.py \
        --site-id <UUID> --site-id <UUID> --site-id <UUID> --dry-run \
        --preview-md audit/post_processing/sp_f_log_replay/hi01_three_site_preview.md
    PYTHONPATH=src .venv/bin/python src/scripts/replay_ourairports_from_csv.py \
        --country RO,BG --only-nulls
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv(Path.cwd() / ".env")


SP_F_COLUMNS: tuple[str, ...] = (
    "nearest_airport_class",
    "nearest_airport_runway_length_m",
    "nearest_airport_scheduled_service",
)

DEFAULT_AIRPORTS_CSV = Path("sources/ourairports/airports.csv")
DEFAULT_RUNWAYS_CSV = Path("sources/ourairports/runways.csv")


# ---------------------------------------------------------------------------
# Pure decision logic (unit-tested without a DB)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ColumnDecision:
    """Per-column verdict produced by :func:`decide_writes`.

    * ``action`` -- one of ``"skip-nonnull"``, ``"skip-noop"``,
      ``"write-null"``, ``"overwrite"``, ``"skip-no-replay"``.
    * ``current`` and ``replayed`` are stored for evidence.
    """

    column: str
    action: str
    current: Any
    replayed: Any


def decide_writes(
    *,
    current: dict[str, Any],
    replayed: dict[str, Any],
    only_nulls: bool,
    overwrite_with_better: bool,
) -> list[ColumnDecision]:
    """Return the per-column verdict given current DB state and replay output.

    Pure: no I/O. ``current`` and ``replayed`` are dicts keyed by the
    SP-F column name. ``replayed`` may carry ``None`` for any field where
    the CSV produced no value.

    Action semantics:

    * ``write-null``       -- DB is NULL, replay has a value, write it.
    * ``skip-nonnull``     -- DB is non-null, ``--only-nulls`` mode, leave alone.
    * ``skip-noop``        -- DB is non-null and replay matches, no action.
    * ``overwrite``        -- DB is non-null, replay differs, ``--overwrite-with-better`` granted.
    * ``skip-no-replay``   -- replay produced ``None`` (CSV gap); no write either way.
    """
    decisions: list[ColumnDecision] = []
    for col in SP_F_COLUMNS:
        cur = current.get(col)
        rep = replayed.get(col)
        if rep is None:
            decisions.append(ColumnDecision(col, "skip-no-replay", cur, rep))
            continue
        if cur is None:
            decisions.append(ColumnDecision(col, "write-null", cur, rep))
            continue
        if _values_equal(cur, rep):
            decisions.append(ColumnDecision(col, "skip-noop", cur, rep))
            continue
        if overwrite_with_better and not only_nulls:
            decisions.append(ColumnDecision(col, "overwrite", cur, rep))
        else:
            decisions.append(ColumnDecision(col, "skip-nonnull", cur, rep))
    return decisions


def _values_equal(a: Any, b: Any) -> bool:
    """Tolerant equality for runway-length floats (1 m), straight equality otherwise."""
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b)
    try:
        fa = float(a)
        fb = float(b)
        return abs(fa - fb) < 1.0
    except (TypeError, ValueError):
        return a == b


# ---------------------------------------------------------------------------
# DB / IO plumbing
# ---------------------------------------------------------------------------

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


def _load_index(airports_csv: Path, runways_csv: Path):
    """Parse the cached CSVs into the in-memory airport index."""
    from atoms_vs_ashes.connectors.ourairports.parsers import (
        build_airport_index, parse_airports_csv, parse_runways_csv,
    )

    if not airports_csv.exists():
        sys.exit(f"ERROR: airports.csv not found at {airports_csv}; this script never downloads.")
    if not runways_csv.exists():
        sys.exit(f"ERROR: runways.csv not found at {runways_csv}; this script never downloads.")

    runway_lengths = parse_runways_csv(runways_csv.read_text(encoding="utf-8"))
    airports = parse_airports_csv(
        airports_csv.read_text(encoding="utf-8"),
        runway_lengths=runway_lengths,
    )
    return build_airport_index(airports), runway_lengths


def _replay_for_site(lat: float, lon: float, index, radius_km: float = 100.0) -> dict[str, Any]:
    from atoms_vs_ashes.connectors.ourairports.parsers import (
        compute_proximity_result, query_airports_in_radius,
    )

    nearby = query_airports_in_radius(lat, lon, index, radius_km=radius_km)
    result = compute_proximity_result(lat, lon, nearby)
    nearest_ident = nearby[0][0].ident if nearby else None
    nearest_obj = nearby[0][0] if nearby else None
    return {
        "nearest_airport_class": result.nearest_airport_class,
        "nearest_airport_runway_length_m": result.nearest_airport_runway_length_m,
        "nearest_airport_scheduled_service": result.nearest_airport_scheduled_service,
        # Reference-only fields for the preview log:
        "_nearest_airport_km": result.nearest_airport_km,
        "_nearest_airport_name": result.nearest_airport_name,
        "_nearest_airport_ident": nearest_ident,
        "_nearest_airport_country": nearest_obj.country_code if nearest_obj else None,
    }


def _current_db_state(session, site_id: uuid.UUID) -> dict[str, Any]:
    from atoms_vs_ashes.db.models import SiteHumanHazards

    row = session.get(SiteHumanHazards, site_id)
    if row is None:
        return {col: None for col in SP_F_COLUMNS}
    return {
        col: getattr(row, col, None) for col in SP_F_COLUMNS
    }


def _apply_writes(session, site_id: uuid.UUID, decisions: list[ColumnDecision]) -> int:
    """Apply only the decisions whose action is ``write-null`` or ``overwrite``."""
    from atoms_vs_ashes.db.models import SiteHumanHazards

    to_write = [d for d in decisions if d.action in {"write-null", "overwrite"}]
    if not to_write:
        return 0
    row = session.get(SiteHumanHazards, site_id)
    if row is None:
        row = SiteHumanHazards(site_id=site_id)
        session.add(row)
    for d in to_write:
        setattr(row, d.column, d.replayed)
    return len(to_write)


# ---------------------------------------------------------------------------
# Preview rendering
# ---------------------------------------------------------------------------

def render_three_site_preview_md(entries: list[dict[str, Any]], *, mode: str) -> str:
    """Render the per-site dry-run preview into the markdown shape Phase 4 expects."""
    parts = ["<!-- man_hours: 0.4 -->",
             "# HI-01 / OurAirports — three-site dry-run preview", "",
             f"Mode: **{mode}**. Source: `sources/ourairports/{{airports,runways}}.csv`. ",
             "No DB writes performed by this preview.", ""]
    if not entries:
        parts.append("_No sites matched._")
        return "\n".join(parts)

    for e in entries:
        parts.append(f"## {e['country']} — {e['name']}  (`{e['site_id']}`)")
        parts.append("")
        parts.append(f"- lat / lon: `{e['lat']}` / `{e['lon']}`")
        parts.append(
            f"- nearest airport (cached CSV): **{e['replay']['_nearest_airport_name']}**"
            f" (`ident={e['replay']['_nearest_airport_ident']}`,"
            f" country={e['replay']['_nearest_airport_country']},"
            f" {e['replay']['_nearest_airport_km']} km)"
        )
        parts.append("")
        parts.append("| column | current_db | replayed_value | source / verdict |")
        parts.append("|--------|------------|----------------|-------------------|")
        for d in e["decisions"]:
            src = (
                f"`runways.csv` join on ident=`{e['replay']['_nearest_airport_ident']}`"
                if d.column == "nearest_airport_runway_length_m"
                else f"`airports.csv` row for ident=`{e['replay']['_nearest_airport_ident']}`"
            )
            parts.append(
                f"| `{d.column}` | `{d.current}` | `{d.replayed}` | {src} — **{d.action}** |"
            )
        parts.append("")
        # Rubric-band shift forecast: HI-01's primary read is `nearest_airport_km`
        # which the replay never touches, so the band shift is "none" for the
        # SP-F-only columns by construction. Document explicitly so the gate
        # reader knows the score impact.
        parts.append(
            "- HI-01 rubric-band shift forecast: **none** for SP-F-only columns "
            "(rubric reads `nearest_airport_km`, `nearest_airport_type`, "
            "`nearest_military_airfield_km`, `flight_path_distance_km`; this "
            "replay touches only `nearest_airport_class`, "
            "`nearest_airport_runway_length_m`, `nearest_airport_scheduled_service`)."
        )
        parts.append("")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Replay HI-01 SP-F columns from cached OurAirports CSVs (offline; no live HTTP).",
    )
    p.add_argument("--airports-csv", type=Path, default=DEFAULT_AIRPORTS_CSV)
    p.add_argument("--runways-csv", type=Path, default=DEFAULT_RUNWAYS_CSV)
    p.add_argument(
        "--country",
        help="Comma-separated ISO country codes; restricts replay to those countries.",
    )
    p.add_argument(
        "--site-id", action="append", default=[],
        help="Restrict to specific site UUIDs (repeatable). Use 3 times for the gate preview.",
    )
    mode = p.add_mutually_exclusive_group()
    mode.add_argument(
        "--only-nulls", action="store_true",
        help="(default) Write a column only when the current DB value is NULL.",
    )
    mode.add_argument(
        "--overwrite-with-better", action="store_true",
        help="Also overwrite non-null columns when the replayed value differs. "
             "Each overwrite is logged with current+replayed evidence.",
    )
    p.add_argument(
        "--dry-run", action="store_true",
        help="Compute decisions and print preview, but do not commit anything.",
    )
    p.add_argument(
        "--preview-md", type=Path, default=None,
        help="When set, write the per-site dry-run preview to this markdown file.",
    )
    p.add_argument(
        "--json-summary", type=Path, default=None,
        help="Optional path to write a per-site JSON summary.",
    )
    p.add_argument(
        "--radius-km", type=float, default=100.0,
        help="Search radius for nearest-airport queries (default 100 km).",
    )
    return p.parse_args()


def main() -> int:
    from sqlalchemy import text
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
    sites = sites_q.order_by(Site.country_code, Site.name).all()
    if not sites:
        print("No sites match the filter; nothing to do.")
        return 0

    print(f"Loading cached OurAirports CSVs from {args.airports_csv} + {args.runways_csv} ...")
    index, _runway_lengths = _load_index(args.airports_csv, args.runways_csv)
    print(f"  index built: {index.airport_count} airports, "
          f"{len(index.countries_loaded)} countries.")

    summary = {
        "mode": mode,
        "dry_run": args.dry_run,
        "total_sites": len(sites),
        "decisions": {a: 0 for a in (
            "write-null", "overwrite", "skip-nonnull", "skip-noop", "skip-no-replay",
        )},
        "rows_with_writes": 0,
        "per_site": [],
    }
    preview_entries: list[dict[str, Any]] = []

    for site in sites:
        replayed = _replay_for_site(
            float(site.latitude), float(site.longitude), index,
            radius_km=args.radius_km,
        )
        current = _current_db_state(session, site.site_id)
        decisions = decide_writes(
            current=current, replayed=replayed,
            only_nulls=only_nulls,
            overwrite_with_better=args.overwrite_with_better,
        )
        for d in decisions:
            summary["decisions"][d.action] = summary["decisions"].get(d.action, 0) + 1

        write_count = 0
        if not args.dry_run:
            write_count = _apply_writes(session, site.site_id, decisions)
            if write_count:
                summary["rows_with_writes"] += 1

        per_site_record = {
            "site_id": str(site.site_id),
            "country": site.country_code,
            "name": site.name,
            "lat": float(site.latitude),
            "lon": float(site.longitude),
            "nearest_ident": replayed["_nearest_airport_ident"],
            "nearest_name": replayed["_nearest_airport_name"],
            "decisions": [
                {
                    "column": d.column, "action": d.action,
                    "current": _serialise(d.current),
                    "replayed": _serialise(d.replayed),
                }
                for d in decisions
            ],
            "writes_planned": sum(
                1 for d in decisions if d.action in {"write-null", "overwrite"}
            ),
            "writes_committed": write_count,
        }
        summary["per_site"].append(per_site_record)
        preview_entries.append({
            "site_id": str(site.site_id), "country": site.country_code,
            "name": site.name, "lat": float(site.latitude), "lon": float(site.longitude),
            "replay": replayed, "decisions": decisions,
        })

    if not args.dry_run and summary["rows_with_writes"]:
        session.commit()

    print()
    print("=== HI-01 ourairports CSV-replay summary ===")
    print(f"  Mode:                     {mode}")
    print(f"  Dry run:                  {args.dry_run}")
    print(f"  Sites considered:         {summary['total_sites']}")
    for action, n in summary["decisions"].items():
        print(f"  decisions[{action}]:".ljust(34) + f"{n}")
    print(f"  Rows with at least one write: {summary['rows_with_writes']}")

    if args.preview_md:
        args.preview_md.parent.mkdir(parents=True, exist_ok=True)
        args.preview_md.write_text(
            render_three_site_preview_md(preview_entries, mode=mode),
            encoding="utf-8",
        )
        print(f"  Preview MD written to:    {args.preview_md}")

    if args.json_summary:
        args.json_summary.parent.mkdir(parents=True, exist_ok=True)
        args.json_summary.write_text(json.dumps(summary, indent=2, default=str))
        print(f"  Per-site JSON written to: {args.json_summary}")

    return 0


def _serialise(v: Any) -> Any:
    """Make Decimal / Numeric values JSON-friendly without losing precision."""
    try:
        from decimal import Decimal
        if isinstance(v, Decimal):
            return float(v)
    except ImportError:
        pass
    return v


if __name__ == "__main__":
    sys.exit(main())
