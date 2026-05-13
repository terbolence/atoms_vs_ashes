#!/usr/bin/env python
# man_hours: 1.6
"""HI-06 focused rerun against OSM Overpass.

Replays every site against the SP-F-reworked
``OverpassClient.fetch_military_areas`` query (which now covers
``military=*`` nodes/ways/relations, ``landuse=military`` polygons, and
military-tagged aerodromes), classifies each element via
``atoms_vs_ashes.analysis.military_proximity.classify_military_element``,
and persists the resulting fields onto ``site_human_hazards``:

- ``nearest_military_km`` / ``nearest_military_name``
- ``nearest_military_class``  (airfield / depot / training_area / other)
- ``nearest_high_consequence_military_km``
- ``nearest_high_consequence_military_class``  (airfield or depot)
- ``military_count``
- ``hi06_quality`` / ``hi06_comment``

This script is scoped to HI-06 only — it does NOT touch HI-07 (transmitters),
NS-02 (power) or any other criterion. Use it after the SP-F query rework
to refresh military classification fields without re-running the broader
FIX-04 batch.

Live API consent: this script issues calls against
``https://overpass-api.de/api/interpreter``. Re-run with ``--confirm`` to
acknowledge live Overpass calls.

Usage::

    PYTHONPATH=src .venv/bin/python src/scripts/run_hi06_rerun.py --confirm --dry-run
    PYTHONPATH=src .venv/bin/python src/scripts/run_hi06_rerun.py --confirm --country RO,AT
    PYTHONPATH=src .venv/bin/python src/scripts/run_hi06_rerun.py --confirm \\
        --site-id 28c80d72-dd9e-4fbf-a2c7-d48d49ca61dc
"""

from __future__ import annotations

import argparse
import random
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from sqlalchemy import create_engine, text as sa_text
from sqlalchemy.orm import sessionmaker

from atoms_vs_ashes.analysis.military_proximity import (
    DEFAULT_SEARCH_RADIUS_KM,
    assess_military_proximity,
)
from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.connectors.osm.client import OverpassClient
from atoms_vs_ashes.connectors.response_logger import log_raw_response
from atoms_vs_ashes.db.models import DataSource, Site
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

INTER_QUERY_DELAY_S = 12.0
JITTER_S = 3.0
SOURCE_NAME = "osm_overpass_military_spf"
SOURCE_URL = "https://overpass-api.de/api/interpreter"
SOURCE_DESC = (
    "OSM Overpass (SP-F HI-06 rerun): military proximity + 4-class taxonomy "
    "+ high-consequence proximity for HI-06 scoring."
)
HI06_COMMENT_MARKER = "Source: OSM Overpass [SP-F HI-06 rerun]"


def _ensure_data_source(session) -> None:
    existing = session.query(DataSource).filter_by(name=SOURCE_NAME).first()
    if existing is None:
        session.add(DataSource(
            name=SOURCE_NAME,
            url=SOURCE_URL,
            description=SOURCE_DESC,
            last_fetched=datetime.now(timezone.utc),
        ))
        session.flush()


def _is_enriched(session, site_id: uuid.UUID) -> bool:
    """True if this site's hi06_comment already carries our SP-F marker."""
    row = session.execute(
        sa_text(
            "SELECT hi06_comment FROM site_human_hazards "
            "WHERE site_id = CAST(:sid AS uuid)"
        ),
        {"sid": str(site_id)},
    ).mappings().first()
    if row is None:
        return False
    return HI06_COMMENT_MARKER in (row.get("hi06_comment") or "")


def _build_comment(result, radius_km: float) -> str:
    """Compose ``hi06_comment`` with nearest, high-consequence and counts."""
    parts: list[str] = []
    if result.nearest_distance_km is not None:
        name = result.nearest_name or "unnamed"
        cls = result.nearest_class or "?"
        parts.append(f"Nearest military: {name} ({cls}), {result.nearest_distance_km:.1f} km")
    else:
        parts.append(f"No military features within {radius_km:.0f} km")
    if result.nearest_high_consequence_km is not None:
        hc_cls = result.nearest_high_consequence_class or "?"
        parts.append(
            f"Nearest high-consequence ({hc_cls}): "
            f"{result.nearest_high_consequence_km:.1f} km"
        )
    if result.class_counts:
        counts = ", ".join(f"{k}={v}" for k, v in sorted(result.class_counts.items()))
        parts.append(f"Counts: {counts}")
    parts.append(f"Total within {radius_km:.0f} km: {result.installation_count}")
    parts.append(HI06_COMMENT_MARKER)
    return "; ".join(parts)[:1000]


def _quality(result) -> str:
    """Map an assessment result onto the ``hi06_quality`` enum."""
    if result.error:
        return "error"
    if result.installation_count == 0:
        return "no_features_found"
    if result.nearest_distance_km is None:
        return "low"
    return "high" if result.nearest_distance_km < 5 else "medium"


def _log_osm_raw(
    session,
    client: OverpassClient,
    site_id: uuid.UUID,
    run_id: str,
    *,
    error: str | None = None,
) -> None:
    """Drain the per-site Overpass accumulator and dual-write to DB + disk.

    Mirrors ``atoms_vs_ashes.connectors.osm.batch._log_osm_raw`` so the
    SP-F HI-06 rerun satisfies the ``raw-response-logging.mdc`` rule
    without depending on the private helper in the connector package.
    """
    calls = client.consume_raw_call_log()
    if not calls and error is None:
        return
    body: dict = {"scope": "hi06_spf_rerun", "calls": calls}
    if error is not None:
        body["error"] = error
    last_status = calls[-1]["http_status"] if calls else None
    log_raw_response(
        session=session,
        site_id=site_id,
        connector_slug="osm",
        run_id=run_id,
        request_url=getattr(client, "_url", ""),
        response_body=body,
        http_status=last_status,
    )


def _persist(session, site_id: uuid.UUID, result, run_id: str, radius_km: float) -> None:
    """Upsert HI-06 fields for *site_id*; commit handled by caller."""
    now = datetime.now(timezone.utc)
    session.execute(
        sa_text("""
            INSERT INTO site_human_hazards (
                site_id, nearest_military_km, nearest_military_name,
                nearest_military_class, nearest_high_consequence_military_km,
                nearest_high_consequence_military_class, military_count,
                hi06_quality, hi06_comment, fetched_at, run_id
            )
            VALUES (
                CAST(:sid AS uuid), :nearest_km, :nearest_name,
                :nearest_class, :hc_km, :hc_class, :count,
                :quality, :comment, :now, :run_id
            )
            ON CONFLICT (site_id) DO UPDATE SET
                nearest_military_km                     = EXCLUDED.nearest_military_km,
                nearest_military_name                   = EXCLUDED.nearest_military_name,
                nearest_military_class                  = EXCLUDED.nearest_military_class,
                nearest_high_consequence_military_km    = EXCLUDED.nearest_high_consequence_military_km,
                nearest_high_consequence_military_class = EXCLUDED.nearest_high_consequence_military_class,
                military_count                          = EXCLUDED.military_count,
                hi06_quality                            = EXCLUDED.hi06_quality,
                hi06_comment                            = EXCLUDED.hi06_comment,
                fetched_at                              = EXCLUDED.fetched_at,
                run_id                                  = EXCLUDED.run_id
        """),
        {
            "sid": str(site_id),
            "nearest_km": result.nearest_distance_km,
            "nearest_name": (result.nearest_name or "")[:200] or None,
            "nearest_class": result.nearest_class,
            "hc_km": result.nearest_high_consequence_km,
            "hc_class": result.nearest_high_consequence_class,
            "count": result.installation_count,
            "quality": _quality(result),
            "comment": _build_comment(result, radius_km),
            "now": now,
            "run_id": run_id,
        },
    )


def _query_sites(session, *, country_codes, site_id):
    """Return the ordered list of sites to process given CLI filters."""
    q = session.query(Site)
    if site_id:
        q = q.filter(Site.site_id == site_id)
    if country_codes:
        q = q.filter(Site.country_code.in_(country_codes))
    return q.order_by(Site.country_code, Site.name).all()


def run_batch(
    *,
    dry_run: bool,
    requery_enriched: bool,
    country_codes: list[str] | None,
    site_id: uuid.UUID | None,
    radius_km: float,
) -> int:
    settings = Settings()
    engine = create_engine(settings.database.url, echo=False, pool_pre_ping=True)
    SessionFactory = sessionmaker(bind=engine)
    session = SessionFactory()
    client = OverpassClient(settings, retry_on_error=True)

    run_id = f"hi06_spf_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    log.info("hi06_rerun_start", run_id=run_id, dry_run=dry_run, radius_km=radius_km)

    sites = _query_sites(session, country_codes=country_codes, site_id=site_id)
    if not sites:
        print("No sites matched the requested filters.", file=sys.stderr)
        return 1

    if not dry_run:
        _ensure_data_source(session)
        session.commit()

    ok = skipped = errors = 0
    t_start = time.monotonic()

    print(
        f"\nHI-06 SP-F rerun — {len(sites)} sites, run_id={run_id}"
        + (" [DRY RUN]" if dry_run else ""),
        flush=True,
    )
    print(f"{'#':>4}  {'CC':>3}  {'Site':<40}  {'count':>6}  {'class':<14}  {'nearest_km':>10}  {'hc_km':>7}")
    print("-" * 95)

    for i, site in enumerate(sites):
        lat, lon = float(site.latitude), float(site.longitude)
        sid = site.site_id
        cc = site.country_code or "??"

        if not requery_enriched and _is_enriched(session, sid):
            skipped += 1
            print(
                f"{i+1:>4}  {cc:>3}  {(site.name or '')[:40]:<40}  {'-':>6}  {'cached':<14}  {'-':>10}  {'-':>7}",
                flush=True,
            )
            continue

        try:
            if dry_run:
                result_label = "dry-run"
                count_label = "-"
                class_label = "-"
                nearest_label = "-"
                hc_label = "-"
            else:
                client.reset_raw_call_log()
                result = assess_military_proximity(
                    lat, lon, overpass=client, radius_km=radius_km,
                )
                if result.error:
                    raise RuntimeError(result.error)
                _persist(session, sid, result, run_id, radius_km)
                _log_osm_raw(session, client, sid, run_id)
                session.commit()
                count_label = str(result.installation_count)
                class_label = (result.nearest_class or "none")[:14]
                nearest_label = (
                    f"{result.nearest_distance_km:.1f}"
                    if result.nearest_distance_km is not None else "-"
                )
                hc_label = (
                    f"{result.nearest_high_consequence_km:.1f}"
                    if result.nearest_high_consequence_km is not None else "-"
                )
                result_label = "ok"
            ok += 1
        except Exception as exc:
            errors += 1
            session.rollback()
            try:
                _log_osm_raw(session, client, sid, run_id, error=str(exc))
                session.commit()
            except Exception as inner:
                session.rollback()
                log.warning("hi06_rerun_raw_log_failed", site_id=str(sid), error=str(inner))
            log.error("hi06_rerun_error", site_id=str(sid), error=str(exc))
            count_label = "ERR"
            class_label = "ERR"
            nearest_label = "-"
            hc_label = "-"
            result_label = "ERR"

        print(
            f"{i+1:>4}  {cc:>3}  {(site.name or '')[:40]:<40}  "
            f"{count_label:>6}  {class_label:<14}  {nearest_label:>10}  {hc_label:>7}",
            flush=True,
        )

        if not dry_run:
            time.sleep(max(2.0, INTER_QUERY_DELAY_S + random.uniform(-JITTER_S, JITTER_S)))

    elapsed_s = time.monotonic() - t_start
    print(
        f"\nDone in {elapsed_s/60:.1f} min — ok={ok}, skipped={skipped}, errors={errors}",
        flush=True,
    )
    return 0 if errors == 0 else 1


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="HI-06 focused rerun against OSM Overpass.")
    parser.add_argument(
        "--confirm", action="store_true",
        help="Acknowledge live Overpass calls (required unless --dry-run).",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--requery-enriched", action="store_true",
        help="Re-run sites already carrying the SP-F marker.",
    )
    parser.add_argument("--country", type=str, default=None, help="Comma-separated country codes.")
    parser.add_argument("--site-id", type=str, default=None)
    parser.add_argument("--radius-km", type=float, default=float(DEFAULT_SEARCH_RADIUS_KM))
    args = parser.parse_args(argv)

    if not args.dry_run and not args.confirm:
        print(
            "ERROR: live mode requires --confirm to acknowledge OSM Overpass calls.",
            file=sys.stderr,
        )
        return 2

    country_codes = (
        [c.strip().upper() for c in args.country.split(",") if c.strip()]
        if args.country else None
    )
    sid = uuid.UUID(args.site_id) if args.site_id else None

    return run_batch(
        dry_run=args.dry_run,
        requery_enriched=args.requery_enriched,
        country_codes=country_codes,
        site_id=sid,
        radius_km=args.radius_km,
    )


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
