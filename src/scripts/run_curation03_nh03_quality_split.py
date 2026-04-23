#!/usr/bin/env python
# man_hours: 1.0
"""CURATION-03: split NH-03 ``nh03_quality`` into quality vs. source.

Historically the Zhu, EGDI and SoilGrids batch writers all reused the
``nh03_quality`` column for two different purposes:

- **provenance** (e.g. ``zhu_global_1km`` written by Zhu) — what dataset
  produced the row;
- **evidence confidence** (e.g. ``low`` / ``medium`` written by EGDI when
  lithology was missing).

Mixing these created the visual collision the user reported ("`zhu` and
`low` mean what?"). This backfill normalises every row into the new
contract:

- ``nh03_source``   = provenance tag (``zhu_global_1km``,
  ``egdi_lithology``, ``soilgrids``, …);
- ``nh03_quality``  = strict enum: ``high|medium|low|no_data``.

Algorithm: see ``docs/post_processing/data_curation_methodology.md``,
Task 3.

Usage::

    python scripts/run_curation03_nh03_quality_split.py --dry-run
    python scripts/run_curation03_nh03_quality_split.py --dry-run --limit 20
    python scripts/run_curation03_nh03_quality_split.py
"""

from __future__ import annotations

import argparse
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
from atoms_vs_ashes.db.models import Site, SiteNaturalHazards
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

# Provenance tags that historically leaked into nh03_quality.
SOURCE_TAGS: set[str] = {
    "zhu_global_1km",
    "egdi_lithology",
    "egdi_geology",
    "soilgrids",
    "soilgrids_v2",
}

# Tokens that legitimately belonged in nh03_quality.
QUALITY_VALUES: set[str] = {"high", "medium", "low", "no_data", "insufficient"}

RAW_VALUE_RE = re.compile(r"raw\s*raster\s*value\s*:\s*(\-?\d+)", re.IGNORECASE)
SOURCE_HINTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"zhu", re.IGNORECASE), "zhu_global_1km"),
    (re.compile(r"egdi", re.IGNORECASE), "egdi_lithology"),
    (re.compile(r"soilgrids", re.IGNORECASE), "soilgrids"),
]

REPORT_PATH = (
    PROJECT_ROOT
    / "audit"
    / "post_processing"
    / "02_data_verification"
    / "2_5_targeted_checks"
    / "20260420_2_5_5b_nh03_quality_split.md"
)


def _normalise_quality(raw_value: int | None, has_class: bool, source: str | None) -> str:
    """Apply the methodology-doc rules to a single row."""
    if source == "zhu_global_1km":
        if raw_value is None or raw_value == 0:
            return "no_data" if not has_class else "medium"
        if 1 <= raw_value <= 5:
            return "medium"
        return "no_data"
    if source in {"egdi_lithology", "egdi_geology"}:
        return "medium" if has_class else "low"
    if source in {"soilgrids", "soilgrids_v2"}:
        return "low"
    return "low"


def _infer_source_from_comment(comment: str | None) -> str | None:
    if not comment:
        return None
    for pattern, source in SOURCE_HINTS:
        if pattern.search(comment):
            return source
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    engine = create_engine(Settings().database.url)
    SessionLocal = sessionmaker(bind=engine)

    rows_total = 0
    rows_already_split = 0  # nh03_quality already a clean enum AND nh03_source set
    rows_quality_already_clean_no_source = 0
    rows_swapped_from_source_tag = 0
    rows_skipped_unknown_quality = 0
    skipped_unknown: list[tuple[str, str, str | None]] = []
    quality_counter_before: Counter[str | None] = Counter()
    quality_counter_after: Counter[str | None] = Counter()
    source_counter_after: Counter[str | None] = Counter()
    sample_writes: list[tuple[str, str, str | None, str | None, str | None]] = []

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
            old_quality = row.nh03_quality
            old_source = row.nh03_source
            quality_counter_before[old_quality] += 1

            new_quality = old_quality
            new_source = old_source

            if old_quality in SOURCE_TAGS:
                inferred_source = old_quality
                if new_source is None:
                    new_source = inferred_source
                m = RAW_VALUE_RE.search(row.nh03_comment or "")
                raw_value = int(m.group(1)) if m else None
                has_class = row.liquefaction_suscept is not None
                new_quality = _normalise_quality(raw_value, has_class, inferred_source)
                rows_swapped_from_source_tag += 1
            elif old_quality in QUALITY_VALUES:
                if new_source is None:
                    inferred = _infer_source_from_comment(row.nh03_comment)
                    if inferred:
                        new_source = inferred
                if old_source is not None:
                    rows_already_split += 1
                else:
                    rows_quality_already_clean_no_source += 1
            elif old_quality is None:
                if new_source is None:
                    inferred = _infer_source_from_comment(row.nh03_comment)
                    if inferred:
                        new_source = inferred
            else:
                rows_skipped_unknown_quality += 1
                if len(skipped_unknown) < 20:
                    skipped_unknown.append((country_code or "??", site_name, old_quality))

            quality_counter_after[new_quality] += 1
            source_counter_after[new_source] += 1

            if not args.dry_run:
                row.nh03_quality = new_quality
                row.nh03_source = new_source

            if (new_quality, new_source) != (old_quality, old_source):
                if len(sample_writes) < 15:
                    sample_writes.append(
                        (country_code or "??", site_name, old_quality, new_quality, new_source)
                    )

        if not args.dry_run:
            session.commit()
            log.info("committed updates for %d rows", rows_total)
        else:
            session.rollback()

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = []
    lines.append("# NH-03 — quality / source column split")
    lines.append("")
    lines.append(f"_Generated {timestamp} by `scripts/run_curation03_nh03_quality_split.py`._")
    lines.append("")
    lines.append("Methodology: `docs/post_processing/data_curation_methodology.md`, Task 3.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Rows scanned: **{rows_total}**")
    lines.append(f"- Rows whose `nh03_quality` was a provenance tag and got rewritten "
                 f"(value moved to `nh03_source`, quality recomputed): **{rows_swapped_from_source_tag}**")
    lines.append(f"- Rows already in the new contract (clean quality + non-NULL source): "
                 f"**{rows_already_split}**")
    lines.append(f"- Rows with clean quality but no source — source inferred from comment if possible: "
                 f"**{rows_quality_already_clean_no_source}**")
    lines.append(f"- Rows with unknown `nh03_quality` value (left untouched): "
                 f"**{rows_skipped_unknown_quality}**")
    if args.dry_run:
        lines.append("")
        lines.append("> Dry-run — nothing committed.")
    lines.append("")
    lines.append("## `nh03_quality` distribution — before vs. after")
    lines.append("")
    lines.append("| Value | Before | After |")
    lines.append("|---|---:|---:|")
    keys = sorted({*quality_counter_before.keys(), *quality_counter_after.keys()},
                  key=lambda k: (k is None, str(k)))
    for k in keys:
        lines.append(f"| `{k!r}` | {quality_counter_before.get(k, 0)} | {quality_counter_after.get(k, 0)} |")
    lines.append("")
    lines.append("## `nh03_source` distribution — after")
    lines.append("")
    lines.append("| Value | Count |")
    lines.append("|---|---:|")
    for k, v in sorted(source_counter_after.items(), key=lambda kv: (kv[0] is None, str(kv[0]))):
        lines.append(f"| `{k!r}` | {v} |")
    if sample_writes:
        lines.append("")
        lines.append("## Sample rewrites (first 15)")
        lines.append("")
        lines.append("| Country | Site | quality (old → new) | source (new) |")
        lines.append("|---|---|---|---|")
        for cc, name, oq, nq, ns in sample_writes:
            lines.append(f"| {cc} | {name} | `{oq!r}` → `{nq!r}` | `{ns!r}` |")
    if skipped_unknown:
        lines.append("")
        lines.append("## Rows with unknown `nh03_quality` (left untouched)")
        lines.append("")
        lines.append("| Country | Site | nh03_quality |")
        lines.append("|---|---|---|")
        for cc, name, q in skipped_unknown:
            lines.append(f"| {cc} | {name} | `{q!r}` |")
    lines.append("")
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    log.info("wrote report → %s", REPORT_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
