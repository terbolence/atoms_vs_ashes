#!/usr/bin/env python
# man_hours: 0.5
"""CURATION-05: backfill NH-11 mean_annual_precip_mm from nh11_comment.

ERA5 has long written the annual precipitation total inside nh11_comment as
``annual=NNNmm`` but until now that value was never extracted into a
dedicated column. This backfill walks every ``site_natural_hazards`` row,
parses the substring, and writes the integer mm/year into
``mean_annual_precip_mm`` (merge-only — never overwrites a non-NULL value).

Usage::

    python scripts/run_curation05_nh11_annual_precip.py --dry-run
    python scripts/run_curation05_nh11_annual_precip.py --dry-run --limit 20
    python scripts/run_curation05_nh11_annual_precip.py        # actually write

A markdown summary is always written to::

    audit/post_processing/02_data_verification/2_5_targeted_checks/
        20260420_2_5_8_nh11_annual_precip_backfill.md

Methodology: docs/post_processing/data_curation_methodology.md, Task 5.
"""

from __future__ import annotations

import argparse
import re
import sys
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
from atoms_vs_ashes.db.models import Site, SiteNaturalHazards
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

ANNUAL_RE = re.compile(r"annual=(\d+)\s*mm", re.IGNORECASE)

REPORT_PATH = (
    PROJECT_ROOT
    / "audit"
    / "post_processing"
    / "02_data_verification"
    / "2_5_targeted_checks"
    / "20260420_2_5_8_nh11_annual_precip_backfill.md"
)

LOW_THRESHOLD_MM = 100
HIGH_THRESHOLD_MM = 5000


def parse_annual(comment: str | None) -> int | None:
    if not comment:
        return None
    m = ANNUAL_RE.search(comment)
    if m is None:
        return None
    try:
        return int(m.group(1))
    except (TypeError, ValueError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--dry-run", action="store_true", help="parse and report only; no DB writes")
    parser.add_argument("--limit", type=int, default=None, help="cap number of rows processed")
    args = parser.parse_args()

    engine = create_engine(Settings().database.url)
    SessionLocal = sessionmaker(bind=engine)

    rows_total = 0
    rows_with_comment = 0
    rows_with_existing_value = 0
    rows_parsed = 0
    rows_written = 0
    rows_unparsed_with_comment = 0
    rows_low_outlier: list[tuple[str, str, int]] = []
    rows_high_outlier: list[tuple[str, str, int]] = []
    sample_writes: list[tuple[str, str, int]] = []
    sample_unparsed: list[tuple[str, str, str]] = []

    with SessionLocal() as session:
        q = (
            session.query(SiteNaturalHazards, Site.name, Site.country_code)
            .join(Site, Site.site_id == SiteNaturalHazards.site_id)
            .order_by(Site.country_code, Site.name)
        )
        if args.limit:
            q = q.limit(args.limit)

        for row, site_name, country_code in q:
            rows_total += 1
            comment = row.nh11_comment
            existing = row.mean_annual_precip_mm

            if existing is not None:
                rows_with_existing_value += 1

            if comment:
                rows_with_comment += 1

            value = parse_annual(comment)
            if value is None:
                if comment:
                    rows_unparsed_with_comment += 1
                    if len(sample_unparsed) < 10:
                        sample_unparsed.append((country_code or "??", site_name, comment[:120]))
                continue

            rows_parsed += 1

            if value < LOW_THRESHOLD_MM:
                rows_low_outlier.append((country_code or "??", site_name, value))
            if value > HIGH_THRESHOLD_MM:
                rows_high_outlier.append((country_code or "??", site_name, value))

            if existing is not None:
                continue

            if not args.dry_run:
                row.mean_annual_precip_mm = value

            rows_written += 1
            if len(sample_writes) < 10:
                sample_writes.append((country_code or "??", site_name, value))

        if not args.dry_run:
            session.commit()
            log.info("committed %d updates", rows_written)
        else:
            session.rollback()
            log.info("dry-run: would have written %d rows", rows_written)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = []
    lines.append("# NH-11 — `mean_annual_precip_mm` backfill")
    lines.append("")
    lines.append(f"_Generated {timestamp} by `scripts/run_curation05_nh11_annual_precip.py`._")
    lines.append("")
    lines.append("Source: parses `annual=<N>mm` out of `site_natural_hazards.nh11_comment` "
                 "(written by the Copernicus ERA5 connector). Never overwrites a non-NULL value.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Rows scanned: **{rows_total}**")
    lines.append(f"- Rows with `nh11_comment` set: **{rows_with_comment}**")
    lines.append(f"- Rows with `annual=<N>mm` parsed: **{rows_parsed}**")
    lines.append(f"- Rows with comment but no parseable annual value: **{rows_unparsed_with_comment}** "
                 "(likely NOAA-only / non-ERA5)")
    lines.append(f"- Rows already populated before this run: **{rows_with_existing_value}**")
    if args.dry_run:
        lines.append(f"- Rows that **would** be written: **{rows_written}** (dry-run, nothing committed)")
    else:
        lines.append(f"- Rows written this run: **{rows_written}**")
    lines.append("")
    lines.append("## Plausibility flags")
    lines.append("")
    lines.append(f"- < {LOW_THRESHOLD_MM} mm/yr: **{len(rows_low_outlier)}** row(s)")
    lines.append(f"- > {HIGH_THRESHOLD_MM} mm/yr: **{len(rows_high_outlier)}** row(s)")
    if rows_parsed > 0 and len(rows_low_outlier) >= rows_parsed * 0.9:
        lines.append("")
        lines.append("> **WARNING — UPSTREAM CONNECTOR BUG SUSPECTED.** Effectively every "
                     "row is below the low-outlier threshold. The Copernicus ERA5 connector "
                     "(`src/atoms_vs_ashes/connectors/copernicus_era5/client.py` "
                     "`_extract_precipitation`) treats the ERA5 monthly-means "
                     "`total_precipitation` field as `m per month` and multiplies by 1000 to get "
                     "mm. ERA5 monthly means are actually a daily-mean rate (m/day); the value "
                     "must additionally be multiplied by the number of days in the month before "
                     "summing across the year. This is **out of scope** for the current "
                     "post-processing curation plan, but the values stored in the new "
                     "`mean_annual_precip_mm` column are therefore ~30× too low. The column was "
                     "still backfilled (faithful to the comment), and the bug should be fixed in "
                     "a follow-up before the values are used for scoring.")
    if rows_low_outlier:
        lines.append("")
        lines.append("### Low outliers (< {} mm/yr) — first 30".format(LOW_THRESHOLD_MM))
        lines.append("")
        lines.append("| Country | Site | mm/yr |")
        lines.append("|---|---|---|")
        for cc, name, value in sorted(rows_low_outlier)[:30]:
            lines.append(f"| {cc} | {name} | {value} |")
        if len(rows_low_outlier) > 30:
            lines.append(f"| … | _{len(rows_low_outlier) - 30} more rows omitted_ | |")
    if rows_high_outlier:
        lines.append("")
        lines.append("### High outliers (> {} mm/yr) — first 30".format(HIGH_THRESHOLD_MM))
        lines.append("")
        lines.append("| Country | Site | mm/yr |")
        lines.append("|---|---|---|")
        for cc, name, value in sorted(rows_high_outlier)[:30]:
            lines.append(f"| {cc} | {name} | {value} |")
        if len(rows_high_outlier) > 30:
            lines.append(f"| … | _{len(rows_high_outlier) - 30} more rows omitted_ | |")
    lines.append("")
    lines.append("## Sample writes")
    lines.append("")
    if sample_writes:
        lines.append("| Country | Site | mm/yr |")
        lines.append("|---|---|---|")
        for cc, name, value in sample_writes:
            lines.append(f"| {cc} | {name} | {value} |")
    else:
        lines.append("_None — every parseable comment already had a value populated._")
    if sample_unparsed:
        lines.append("")
        lines.append("## Sample unparseable comments (first 10)")
        lines.append("")
        lines.append("| Country | Site | Comment (truncated) |")
        lines.append("|---|---|---|")
        for cc, name, snippet in sample_unparsed:
            safe = snippet.replace("|", "\\|")
            lines.append(f"| {cc} | {name} | {safe} |")
    lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    log.info("wrote report → %s", REPORT_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
