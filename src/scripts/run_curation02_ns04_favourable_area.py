#!/usr/bin/env python
# man_hours: 1.0
"""CURATION-02: derive ``favourable_area_ha`` for NS-04.

Walks every ``site_infrastructure_v2`` row and computes the favourable
hectare value from data already on the row. The methodology is in
``docs/post_processing/data_curation_methodology.md`` task 2.

Three methods, in priority order:

1. ``comment_buildable_x_fav_pct`` — preferred. Parses ``Buildable
   (..., 0-1 km): B ha`` and ``Suitability: F% fav`` from
   ``ns04_comment`` and writes ``B * F / 100``.
2. ``buffer_x_pct`` — fallback when only ``favourable_land_pct`` is
   available (e.g. Copernicus DEM has rewritten the comment to
   terrain-only). Uses ``π * 1km² = 314.159 ha`` as the analysis disk.
3. ``pct_x_site_area`` — secondary fallback that scales the plant
   footprint (``sites.site_area_ha``) by ``favourable_land_pct``.

Rows whose computed value is ``< 1.0 ha`` while the underlying plant
footprint is ``> 50 ha`` are flagged for manual review (no auto-fix).

Usage::

    python scripts/run_curation02_ns04_favourable_area.py --dry-run
    python scripts/run_curation02_ns04_favourable_area.py
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.models import Site, SiteInfrastructureV2
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

BUILDABLE_RE = re.compile(
    r"Buildable\s*\([^)]+,\s*0\s*[\u2013\-]\s*1\s*km\):\s*([0-9]+(?:\.[0-9]+)?)\s*ha",
    re.IGNORECASE,
)
FAV_PCT_RE = re.compile(
    r"Suitability:\s*([0-9]+(?:\.[0-9]+)?)\s*%\s*fav",
    re.IGNORECASE,
)

ANALYSIS_DISK_HA = math.pi * (1.0 ** 2) * 100.0  # 1 km² = 100 ha → π × 100

LOW_HA_THRESHOLD = 1.0
LARGE_SITE_HA_THRESHOLD = 50.0

WATER_CLASSES = {
    "WaterBodies", "Water", "Permanent water bodies", "Sea and ocean",
    "Inland water bodies", "Marine waters", "Continuous urban fabric",
}
WATER_CLASS_PREFIXES = ("5",)  # CORINE level-1 = 5xx (water bodies)

REPORT_PATH = (
    PROJECT_ROOT
    / "audit"
    / "post_processing"
    / "02_data_verification"
    / "2_5_targeted_checks"
    / "20260420_2_5_1_favourable_area_review.md"
)


def _parse(comment: str | None) -> tuple[float | None, float | None]:
    if not comment:
        return None, None
    b = BUILDABLE_RE.search(comment)
    f = FAV_PCT_RE.search(comment)
    buildable = float(b.group(1)) if b else None
    fav_pct = float(f.group(1)) if f else None
    return buildable, fav_pct


def _hypothesise_cause(row: SiteInfrastructureV2, comment: str | None) -> str:
    dominant = (row.dominant_land_class or "").strip()
    if dominant in WATER_CLASSES or any(dominant.startswith(p) for p in WATER_CLASS_PREFIXES):
        if row.dominant_class_pct is not None and float(row.dominant_class_pct) > 80:
            return "mid_river_or_offshore"
        return "dominant_water"
    if comment and "Buildable" not in comment and row.favourable_land_pct is not None:
        return "dem_overwrote_landcover_comment"
    return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    engine = create_engine(Settings().database.url)
    SessionLocal = sessionmaker(bind=engine)

    rows_total = 0
    method_counter: Counter[str] = Counter()
    rows_already_set = 0
    rows_written = 0
    flagged_rows: list[tuple[str, str, float, float | None, float | None, float | None, str, str]] = []
    sample_writes: list[tuple[str, str, str, float]] = []

    with SessionLocal() as session:
        q = (
            session.query(SiteInfrastructureV2, Site.name, Site.country_code, Site.site_area_ha)
            .join(Site, Site.site_id == SiteInfrastructureV2.site_id)
            .order_by(Site.country_code, Site.name)
        )
        if args.limit:
            q = q.limit(args.limit)

        for row, site_name, country_code, site_area_ha in q:
            rows_total += 1

            if row.favourable_area_ha is not None:
                rows_already_set += 1
                method_counter[row.favourable_area_method or "preexisting_unknown"] += 1
                continue

            buildable_ha, fav_pct = _parse(row.ns04_comment)
            method = "none"
            value: float | None = None

            if buildable_ha is not None and fav_pct is not None:
                value = round(buildable_ha * fav_pct / 100.0, 2)
                method = "comment_buildable_x_fav_pct"
            elif row.favourable_land_pct is not None:
                value = round(ANALYSIS_DISK_HA * float(row.favourable_land_pct) / 100.0, 2)
                method = "buffer_x_pct"
            elif site_area_ha is not None and row.favourable_land_pct is not None:
                value = round(float(site_area_ha) * float(row.favourable_land_pct) / 100.0, 2)
                method = "pct_x_site_area"

            method_counter[method] += 1

            if value is None:
                continue

            if not args.dry_run:
                row.favourable_area_ha = value
                row.favourable_area_method = method

            rows_written += 1
            if len(sample_writes) < 10:
                sample_writes.append((country_code or "??", site_name, method, value))

            if (
                value < LOW_HA_THRESHOLD
                and site_area_ha is not None
                and float(site_area_ha) > LARGE_SITE_HA_THRESHOLD
            ):
                flagged_rows.append((
                    country_code or "??", site_name,
                    float(site_area_ha),
                    value,
                    buildable_ha,
                    fav_pct,
                    method,
                    _hypothesise_cause(row, row.ns04_comment),
                ))

        if not args.dry_run:
            session.commit()
            log.info("committed %d updates", rows_written)
        else:
            session.rollback()
            log.info("dry-run: would have written %d rows", rows_written)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = []
    lines.append("# NS-04 — `favourable_area_ha` derivation & review")
    lines.append("")
    lines.append(f"_Generated {timestamp} by `scripts/run_curation02_ns04_favourable_area.py`._")
    lines.append("")
    lines.append("Methodology: `docs/post_processing/data_curation_methodology.md`, Task 2.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Rows scanned: **{rows_total}**")
    lines.append(f"- Rows already populated before this run: **{rows_already_set}**")
    if args.dry_run:
        lines.append(f"- Rows that **would** be written: **{rows_written}** (dry-run)")
    else:
        lines.append(f"- Rows written this run: **{rows_written}**")
    lines.append("")
    lines.append("## Method counts")
    lines.append("")
    lines.append("| Method | Count |")
    lines.append("|---|---:|")
    for k, v in sorted(method_counter.items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{k}` | {v} |")
    lines.append("")
    lines.append("## Implausibility flags")
    lines.append("")
    lines.append(f"Sites where `favourable_area_ha < {LOW_HA_THRESHOLD}` ha "
                 f"AND `sites.site_area_ha > {LARGE_SITE_HA_THRESHOLD}` ha. "
                 "These rows are flagged for manual review only — no auto-fix.")
    lines.append("")
    lines.append(f"- Total flagged: **{len(flagged_rows)}**")
    if flagged_rows:
        lines.append("")
        lines.append("| Country | Site | site_area_ha | favourable_area_ha | "
                     "buildable (parsed) | fav % (parsed) | method | hypothesis |")
        lines.append("|---|---|---:|---:|---:|---:|---|---|")
        for cc, name, area, value, b, f, method, hyp in sorted(flagged_rows, key=lambda r: -r[2]):
            b_str = f"{b:.1f}" if b is not None else "—"
            f_str = f"{f:.0f}" if f is not None else "—"
            lines.append(
                f"| {cc} | {name} | {area:.1f} | {value:.2f} | {b_str} | {f_str} | "
                f"`{method}` | `{hyp}` |"
            )
    if sample_writes:
        lines.append("")
        lines.append("## Sample writes")
        lines.append("")
        lines.append("| Country | Site | Method | favourable_area_ha |")
        lines.append("|---|---|---|---:|")
        for cc, name, method, value in sample_writes:
            lines.append(f"| {cc} | {name} | `{method}` | {value:.2f} |")
    lines.append("")
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    log.info("wrote report → %s", REPORT_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
