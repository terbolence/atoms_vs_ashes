#!/usr/bin/env python
# man_hours: 1.5
"""CURATION-01: replace ``HYRIV-{id}`` cooling source names with real names.

Two phases:

1. ``--phase=id`` (default, no API calls): for every row whose
   ``cooling_source_name`` matches ``HYRIV-NNN``, parse the integer and
   persist it to ``cooling_source_hyriv_id``. Safe to run any time.
2. ``--phase=harvest`` (no API calls): scan the local audit cache at
   ``data/raw_responses/overpass/*.json`` for waterway responses that
   already contain a named river/canal/stream within ~10 km of a site.
3. ``--phase=names``: for every row still showing a ``HYRIV-*`` name,
   query Overpass (single mirror, with retry-on-error backoff) for the
   nearest named ``waterway=river|canal|stream`` inside a small radius
   and replace ``cooling_source_name`` with the OSM ``name`` tag.
4. ``--phase=all``: id → harvest → names.

Merge-only persistence — the ``HYRIV-*`` placeholder stays in place when
no name is found (coverage never decreases). The HydroRIVERS reach id is
preserved in the new ``cooling_source_hyriv_id`` column either way.

Usage::

    python scripts/run_curation01_cooling_river_names.py --phase=id --dry-run
    python scripts/run_curation01_cooling_river_names.py --phase=id
    python scripts/run_curation01_cooling_river_names.py --phase=names --dry-run --limit 5
    python scripts/run_curation01_cooling_river_names.py --phase=names

Methodology: ``docs/post_processing/data_curation_methodology.md``, Task 1.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.connectors.osm.client import OverpassClient
from atoms_vs_ashes.db.models import Site, SiteInfrastructureV2
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

HYRIV_RE = re.compile(r"^HYRIV-(\d+)$")

# Base radius ladder (m), tried in order; stop at first hit with a name.
# A per-site step is added on top of this when HydroRIVERS' own
# cooling_distance_km says the river is further away — see
# ``_radii_for_site``.
RADIUS_LADDER_M = (500, 1000, 2000)
RADIUS_HARD_CAP_M = 15000


def _radii_for_site(cooling_distance_km: float | None) -> tuple[int, ...]:
    """Build a per-site radius ladder.

    Always tries the base ladder (500/1000/2000 m). When HydroRIVERS
    reports the cooling source > 2 km away, append one extra step at
    ``ceil(cooling_distance_km * 1000) + 500 m``, capped at
    ``RADIUS_HARD_CAP_M``. This lets us reach the actual river the
    HydroRIVERS reach was snapped to (e.g. Brăila-Chișcani → Danube
    ~4 km away).
    """
    ladder: list[int] = list(RADIUS_LADDER_M)
    if cooling_distance_km is None:
        return tuple(ladder)
    target_m = int(math.ceil(float(cooling_distance_km) * 1000.0)) + 500
    target_m = min(target_m, RADIUS_HARD_CAP_M)
    if target_m > ladder[-1]:
        ladder.append(target_m)
    return tuple(ladder)

REPORT_PATH = (
    PROJECT_ROOT
    / "audit"
    / "post_processing"
    / "02_data_verification"
    / "2_5_targeted_checks"
    / "20260420_2_5_3_cooling_river_names.md"
)

OVERPASS_CACHE_DIR = PROJECT_ROOT / "data" / "raw_responses" / "overpass"

WATERWAY_RANK = {"river": 0, "canal": 1, "stream": 2}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    a = math.radians(lat2 - lat1)
    b = math.radians(lon2 - lon1)
    s1 = math.sin(a / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(
        math.radians(lat2)
    ) * math.sin(b / 2) ** 2
    return 2 * r * math.asin(math.sqrt(s1))


def _scan_audit_cache_for_named_waterways() -> list[tuple[float, float, str, str]]:
    """Walk the on-disk Overpass cache and return a flat list of every
    named waterway feature found, as ``(lat, lon, name, kind)``.

    Filters strictly on the **element tags** (``waterway`` key present)
    — not on the query string — because some audit queries union
    highway/railway/waterway into a single response, so per-element
    classification is required.
    """
    if not OVERPASS_CACHE_DIR.exists():
        return []
    allowed = set(WATERWAY_RANK)
    out: list[tuple[float, float, str, str]] = []
    for path in OVERPASS_CACHE_DIR.glob("*.json"):
        try:
            with path.open() as fh:
                doc = json.load(fh)
        except Exception:
            continue
        q = (doc.get("meta") or {}).get("query") or ""
        if "waterway" not in q:
            continue
        elements = ((doc.get("response") or {}).get("elements")) or []
        for el in elements:
            tags = el.get("tags") or {}
            kind = tags.get("waterway")
            if kind not in allowed:
                continue
            name = tags.get("name:en") or tags.get("name")
            if not name:
                continue
            center = el.get("center") or {}
            elat = center.get("lat") or el.get("lat")
            elon = center.get("lon") or el.get("lon")
            if elat is None or elon is None:
                continue
            out.append((float(elat), float(elon), str(name), str(kind)))
    return out


def _query_nearest_named_waterway(
    client: OverpassClient,
    lat: float,
    lon: float,
    radius_m: int,
    *,
    expected_dist_km: float | None = None,
) -> tuple[str | None, str | None, float | None]:
    """Return (name, waterway_kind, distance_km) for the best-matching
    named waterway, or (None, None, None) if nothing was found.

    Selection rules (applied in order):
      1. Prefer river > canal > stream (by ``waterway`` tag).
      2. If ``expected_dist_km`` is given (i.e. HydroRIVERS already
         reported the cooling source distance), pick the candidate whose
         centroid distance is closest to that value — this disambiguates
         large rivers vs nearby small streams when the radius is wide.
      3. Otherwise pick the nearest centroid.
    """
    ql = f"""
[out:json][timeout:60];
(
  way(around:{radius_m},{lat},{lon})["waterway"~"river|canal|stream"]["name"];
);
out tags center;
"""
    elements = client.query(ql)
    if not elements:
        return None, None, None

    rank = {"river": 0, "canal": 1, "stream": 2}
    best: tuple[int, float, float, str, str] | None = None
    # tuple = (rank, score, centroid_dist_km, name, kind)
    for el in elements:
        tags = el.get("tags") or {}
        name = tags.get("name:en") or tags.get("name")
        if not name:
            continue
        kind = tags.get("waterway") or "river"
        center = el.get("center") or {}
        elat = center.get("lat")
        elon = center.get("lon")
        if elat is None or elon is None:
            elat = el.get("lat")
            elon = el.get("lon")
        if elat is None or elon is None:
            continue
        dist = _haversine_km(lat, lon, float(elat), float(elon))
        secondary = (
            abs(dist - expected_dist_km) if expected_dist_km is not None else dist
        )
        if best is None or (rank.get(kind, 99), secondary) < (best[0], best[1]):
            best = (rank.get(kind, 99), secondary, dist, name, kind)

    if best is None:
        return None, None, None
    return best[3], best[4], best[2]


def _phase_id(session, args, report_lines: list[str]) -> int:
    log.info("phase 1 — extracting HYRIV ids from cooling_source_name")
    rows = (
        session.query(SiteInfrastructureV2, Site.name, Site.country_code)
        .join(Site, Site.site_id == SiteInfrastructureV2.site_id)
        .filter(SiteInfrastructureV2.cooling_source_name.like("HYRIV-%"))
        .order_by(Site.country_code, Site.name)
    )
    if args.limit:
        rows = rows.limit(args.limit)

    written = 0
    already = 0
    sample: list[tuple[str, str, int]] = []
    for row, name, cc in rows:
        m = HYRIV_RE.match(row.cooling_source_name or "")
        if not m:
            continue
        hyriv_id = int(m.group(1))
        if row.cooling_source_hyriv_id is not None:
            already += 1
            continue
        if not args.dry_run:
            row.cooling_source_hyriv_id = hyriv_id
        written += 1
        if len(sample) < 8:
            sample.append((cc or "??", name, hyriv_id))

    if not args.dry_run:
        session.commit()
        log.info("phase 1: committed %d updates", written)
    else:
        session.rollback()
        log.info("phase 1: dry-run, %d would be written", written)

    report_lines.append("## Phase 1 — `cooling_source_hyriv_id` backfill")
    report_lines.append("")
    report_lines.append(f"- Rows updated this run: **{written}**")
    report_lines.append(f"- Rows already populated: **{already}**")
    if sample:
        report_lines.append("")
        report_lines.append("| Country | Site | hyriv id |")
        report_lines.append("|---|---|---:|")
        for cc, name, hyriv_id in sample:
            report_lines.append(f"| {cc} | {name} | {hyriv_id} |")
    report_lines.append("")
    return written


def _phase_harvest(session, args, report_lines: list[str]) -> int:
    """Resolve names from the local Overpass audit cache (no API calls)."""
    log.info("phase 2 — harvesting named waterways from local audit cache")
    cache_features = _scan_audit_cache_for_named_waterways()
    log.info("phase harvest: %d named waterway features found in cache", len(cache_features))

    rows = (
        session.query(SiteInfrastructureV2, Site.name, Site.country_code,
                      Site.latitude, Site.longitude)
        .join(Site, Site.site_id == SiteInfrastructureV2.site_id)
        .filter(SiteInfrastructureV2.cooling_source_name.like("HYRIV-%"))
        .order_by(Site.country_code, Site.name)
    )
    if args.limit:
        rows = rows.limit(args.limit)
    rows = list(rows)

    # Centroid distance is unreliable for linear features (rivers), so the
    # harvest is intentionally narrow: only resolve sites where a NAMED
    # river/canal/stream's centroid is within 12 km AND HydroRIVERS itself
    # reports the cooling source within 12 km. River always wins over canal
    # over stream, then by smallest centroid distance.
    HARVEST_HARD_CAP_KM = 12.0
    resolved = 0
    skipped_no_match = 0
    skipped_distance_guard = 0
    samples: list[tuple[str, str, str, str, str, float]] = []

    for row, name, cc, lat, lon in rows:
        cooling_dist = (
            float(row.cooling_distance_km) if row.cooling_distance_km is not None else None
        )
        # Skip when HydroRIVERS itself put the cooling source far away — we
        # have no reliable way to match without per-vertex geometry.
        if cooling_dist is not None and cooling_dist > HARVEST_HARD_CAP_KM:
            skipped_distance_guard += 1
            continue

        site_lat = float(lat)
        site_lon = float(lon)
        best: tuple[int, float, str, str] | None = None
        for elat, elon, ename, ekind in cache_features:
            dist = _haversine_km(site_lat, site_lon, elat, elon)
            if dist > HARVEST_HARD_CAP_KM:
                continue
            score = (WATERWAY_RANK.get(ekind, 99), dist)
            if best is None or score < (best[0], best[1]):
                best = (WATERWAY_RANK.get(ekind, 99), dist, ename, ekind)
        if best is None:
            skipped_no_match += 1
            continue
        before = row.cooling_source_name
        if not args.dry_run:
            row.cooling_source_name = best[2]
        resolved += 1
        if len(samples) < 30:
            samples.append((cc or "??", name, before or "", best[2], best[3], best[1]))
        log.info(
            "[harvest] %s | %s — %s → %s (%s, centroid_dist=%.2f km, hyriv_dist=%s)",
            cc, name, before, best[2], best[3], best[1],
            f"{cooling_dist:.2f} km" if cooling_dist is not None else "n/a",
        )

    if not args.dry_run:
        session.commit()
        log.info("phase harvest: committed %d updates", resolved)
    else:
        session.rollback()

    report_lines.append("## Phase Harvest — name resolution from local audit cache")
    report_lines.append("")
    report_lines.append("Source: every `*.json` file under `data/raw_responses/overpass/` "
                        "whose Overpass query mentions `waterway`, filtered per-element on "
                        "`tags.waterway in {river, canal, stream}` and `tags.name`. The audit's "
                        "waterway query is restricted to navigable waterways "
                        "(`boat=yes` / `CEMT` / `motorboat=yes`), so this phase only resolves the "
                        "small subset of sites whose cooling source happens to be a major "
                        "navigable river (Danube, Dnieper, etc.). All other HYRIV-* placeholders "
                        "are deferred to the live `--phase=names` Overpass lookup.")
    report_lines.append("")
    report_lines.append("**Note on distance**: Overpass returns each way's centroid, not the "
                        "nearest point on the polyline. We cap at 12 km centroid distance and "
                        "additionally skip sites where HydroRIVERS itself reports the cooling "
                        "source > 12 km away. This means a few real river hits will be missed by "
                        "harvest and re-resolved by phase 2 instead.")
    report_lines.append("")
    report_lines.append(f"- Named waterway features in cache: **{len(cache_features)}**")
    report_lines.append(f"- Sites still on `HYRIV-*` at start of phase: **{len(rows)}**")
    report_lines.append(f"- Sites resolved this phase: **{resolved}**")
    report_lines.append(f"- Sites with no named-waterway hit in guard radius: **{skipped_no_match}**")
    report_lines.append(f"- Sites where HydroRIVERS distance exceeded 12 km guard: **{skipped_distance_guard}**")
    if samples:
        report_lines.append("")
        report_lines.append("| Country | Site | Before | After | OSM kind | Dist (km) |")
        report_lines.append("|---|---|---|---|---|---:|")
        for cc, name, before, after, kind, dist in samples:
            report_lines.append(f"| {cc} | {name} | `{before}` | `{after}` | `{kind}` | {dist:.2f} |")
    report_lines.append("")
    return resolved


def _phase_names(session, args, report_lines: list[str]) -> int:
    log.info("phase 2 — Overpass lookup for named waterways")
    client = OverpassClient(
        settings=Settings(),
        overpass_url=args.overpass_url,
        retry_on_error=True,
    )

    rows = (
        session.query(SiteInfrastructureV2, Site.name, Site.country_code,
                      Site.latitude, Site.longitude)
        .join(Site, Site.site_id == SiteInfrastructureV2.site_id)
        .filter(SiteInfrastructureV2.cooling_source_name.like("HYRIV-%"))
        .order_by(Site.country_code, Site.name)
    )
    if args.limit:
        rows = rows.limit(args.limit)

    rows = list(rows)
    log.info("phase 2: %d rows still on a HYRIV-* placeholder", len(rows))

    resolved = 0
    no_name_found = 0
    errors = 0
    skipped_distance_guard = 0
    samples: list[tuple[str, str, str, str, str, float]] = []

    for i, (row, name, cc, lat, lon) in enumerate(rows, start=1):
        before = row.cooling_source_name
        cooling_dist = (
            float(row.cooling_distance_km)
            if row.cooling_distance_km is not None
            else None
        )
        # Safety: if HydroRIVERS itself says the cooling source is
        # beyond our hard cap, we cannot reach it; querying Overpass
        # will pick a wrong nearby waterway. Keep the HYRIV-* placeholder.
        if cooling_dist is not None and cooling_dist * 1000.0 > RADIUS_HARD_CAP_M:
            skipped_distance_guard += 1
            log.info(
                "[%d/%d] %s | %s — HydroRIVERS distance %.2f km > %d m cap, "
                "skipping Overpass to avoid picking the wrong river (HYRIV stays)",
                i, len(rows), cc, name, cooling_dist, RADIUS_HARD_CAP_M,
            )
            continue
        ladder = _radii_for_site(cooling_dist)
        try:
            new_name, kind, dist_km = (None, None, None)
            for radius_m in ladder:
                new_name, kind, dist_km = _query_nearest_named_waterway(
                    client,
                    float(lat),
                    float(lon),
                    radius_m,
                    expected_dist_km=cooling_dist,
                )
                if new_name:
                    break
                time.sleep(0.5)
        except Exception as exc:  # noqa: BLE001
            errors += 1
            log.warning("[%d/%d] %s | %s — Overpass error: %s", i, len(rows), cc, name, exc)
            time.sleep(2.0)
            continue

        if not new_name:
            no_name_found += 1
            log.info(
                "[%d/%d] %s | %s — no named waterway up to %dm "
                "(hyriv_dist=%s, HYRIV stays)",
                i, len(rows), cc, name, ladder[-1],
                f"{cooling_dist:.2f} km" if cooling_dist is not None else "n/a",
            )
            time.sleep(1.0)
            continue

        if not args.dry_run:
            row.cooling_source_name = new_name
            session.commit()
        resolved += 1
        log.info(
            "[%d/%d] %s | %s — %s → %s (waterway=%s, centroid=%.2f km, "
            "hyriv_dist=%s, radius=%dm)",
            i, len(rows), cc, name, before, new_name, kind, dist_km or 0.0,
            f"{cooling_dist:.2f} km" if cooling_dist is not None else "n/a",
            ladder[-1],
        )
        if len(samples) < 50:
            samples.append((cc or "??", name, before or "", new_name, kind or "", dist_km or 0.0))
        time.sleep(1.0)

    report_lines.append("## Phase 2 — Overpass name resolution")
    report_lines.append("")
    report_lines.append(
        "Per-site dynamic radius: ladder = (500, 1000, 2000) m plus, when "
        "HydroRIVERS reports the cooling source > 2 km away, an extra step at "
        "`ceil(cooling_distance_km*1000) + 500` m, hard-capped at "
        f"**{RADIUS_HARD_CAP_M} m**. Among returned candidates we prefer "
        "river > canal > stream, and when several rivers are returned we pick "
        "the one whose centroid distance is closest to HydroRIVERS' own "
        "`cooling_distance_km` (so a wide search around Brăila-Chișcani picks "
        "the Danube ~4 km away rather than a small stream that happens to "
        "clip the disk)."
    )
    report_lines.append("")
    report_lines.append(f"- Rows attempted: **{len(rows)}**")
    report_lines.append(f"- Rows resolved (real name written): **{resolved}**")
    report_lines.append(f"- Rows with no named waterway in dynamic radius (HYRIV-* preserved): **{no_name_found}**")
    report_lines.append(
        f"- Rows skipped because HydroRIVERS distance > {RADIUS_HARD_CAP_M} m cap "
        f"(HYRIV-* preserved to avoid picking a wrong nearby river): **{skipped_distance_guard}**"
    )
    report_lines.append(f"- Rows skipped due to Overpass error: **{errors}**")
    if samples:
        report_lines.append("")
        report_lines.append("### Resolved samples (first 30)")
        report_lines.append("")
        report_lines.append("| Country | Site | Before | After | OSM kind | Dist (km) |")
        report_lines.append("|---|---|---|---|---|---:|")
        for cc, name, before, after, kind, dist in samples:
            report_lines.append(f"| {cc} | {name} | `{before}` | `{after}` | `{kind}` | {dist:.2f} |")
    report_lines.append("")
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--phase",
        choices=("id", "harvest", "names", "both", "all"),
        default="id",
        help=(
            "id = parse HYRIV-id into cooling_source_hyriv_id (no API). "
            "harvest = resolve names from local Overpass audit cache (no API). "
            "names = run live Overpass lookups for the remaining HYRIV-* sites. "
            "both = id + names (legacy). all = id + harvest + names."
        ),
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--overpass-url",
        default="https://overpass.kumi.systems/api/interpreter",
        help="Overpass mirror to use for phase 2",
    )
    args = parser.parse_args()

    engine = create_engine(Settings().database.url)
    SessionLocal = sessionmaker(bind=engine)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report_lines: list[str] = []
    report_lines.append("# NS-01 — cooling source river names")
    report_lines.append("")
    report_lines.append(f"_Generated {timestamp} by `scripts/run_curation01_cooling_river_names.py` (phase={args.phase})._")
    report_lines.append("")
    report_lines.append("Methodology: `docs/post_processing/data_curation_methodology.md`, Task 1.")
    report_lines.append("")

    with SessionLocal() as session:
        if args.phase in ("id", "both", "all"):
            _phase_id(session, args, report_lines)
        if args.phase in ("harvest", "all"):
            _phase_harvest(session, args, report_lines)
        if args.phase in ("names", "both", "all"):
            _phase_names(session, args, report_lines)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    append_modes = {"harvest", "names"}
    if REPORT_PATH.exists() and args.phase in append_modes:
        existing = REPORT_PATH.read_text(encoding="utf-8")
        REPORT_PATH.write_text(existing + "\n\n---\n\n" + "\n".join(report_lines), encoding="utf-8")
    else:
        REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")
    log.info("wrote report → %s", REPORT_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
