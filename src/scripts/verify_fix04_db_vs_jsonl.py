# man_hours: 1.4
"""Verify the FIX-04 apply landed correctly using a three-way comparison.

For every (site, column) the verifier compares **three** values:

- ``A`` = JSONL.db.<domain>.<col>      — pre-apply DB state captured at
                                         preview time.
- ``B`` = JSONL.fetch.<domain>.<key>   — Overpass-derived "proposed"
                                         value the preview promised
                                         would land in the DB.
- ``C`` = post-apply DB read           — what the DB actually holds
                                         right now.

A healthy apply requires:

1. ``C == B`` for every (site, column). The apply wrote what the
   preview promised. (This is the v1 "roundtrip" check; it catches
   persist-function bugs but not a corrupted JSONL or a bad parser
   since A/B/C all derive from the same May-11 preview run.)
2. For every (site, column) the preview flagged as ``A != B``:
   ``C == B`` AND ``C != A``. The apply *moved* the value off the
   prior state, on exactly the cells the preview promised.
3. For every (site, column) the preview did *not* flag (in-sync at
   preview time): ``C == A == B``. No off-target writes.

The verifier still reads the JSONL as its data source, so it cannot
detect a JSONL corrupt at write time or a parser bug at preview
time. To catch those, an independent re-parse against
``site_raw_responses`` (rule ``raw-response-logging.mdc``) is
required; today's preview/apply do not yet write there. See the
audit entry follow-up.

Pure logic lives in :mod:`_verify_fix04_threeway`.

Usage::

    PYTHONPATH=src .venv/bin/python src/scripts/verify_fix04_db_vs_jsonl.py \
        --jsonl logs/hi06_fix04_preview.jsonl

Exit code 0 iff all three checks pass.
"""

from __future__ import annotations

import argparse
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

sys.path.insert(0, str(Path(__file__).parent))
from _preview_fix04_diff import DOMAINS  # noqa: E402
from _apply_fix04_from_jsonl import iter_records, select_record  # noqa: E402
from _verify_fix04_threeway import (  # noqa: E402
    empty_aggregate, empty_flip_counts, evaluate_record, flagged_set,
    render_report, update_flip_counts,
)


def _build_session():
    from atoms_vs_ashes.config import Settings
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    settings = Settings()
    engine = create_engine(settings.database.url, echo=False, pool_pre_ping=True)
    return sessionmaker(bind=engine, future=True)()


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def _fetch_db_state(session, site_id: uuid.UUID) -> dict[str, dict[str, Any]]:
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
            sa_text(
                f"SELECT {cols_sql} FROM {table} "
                f"WHERE site_id = CAST(:sid AS uuid)"
            ),
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
            "Verify FIX-04 apply with a three-way (pre-apply / proposed / "
            "post-apply) cross-check. No Overpass calls."
        ),
    )
    p.add_argument(
        "--jsonl", type=Path,
        default=Path("logs/hi06_fix04_preview.jsonl"),
        help="Source JSONL (default: logs/hi06_fix04_preview.jsonl).",
    )
    p.add_argument(
        "--country", dest="countries", metavar="CC,...",
        help="Comma-separated ISO country codes to verify (default: all).",
    )
    p.add_argument(
        "--site-id", action="append", default=[],
        help="Restrict to specific site UUIDs (repeatable).",
    )
    p.add_argument(
        "--report", type=Path,
        default=Path(
            "audit/post_processing/hi06_fix04_preview/"
            "hi06_fix04_post_apply_verify.md"
        ),
        help="Markdown verification report path.",
    )
    p.add_argument(
        "--head-limit", type=int, default=20,
        help="Cap on per-site failure blocks rendered in the markdown report.",
    )
    return p.parse_args()


def _maybe_progress(*, total_verified: int, flips_landed: int,
                    flips_expected: int, n_failures: int) -> None:
    if total_verified % 50 == 0:
        print(
            f"[{_ts()}] verified={total_verified} "
            f"flips_landed={flips_landed}/{flips_expected} "
            f"failures={n_failures}",
            flush=True,
        )


def main() -> int:
    args = _parse_args()
    if not args.jsonl.exists():
        print(f"ERROR: JSONL not found: {args.jsonl}", file=sys.stderr)
        return 2

    countries: set[str] | None = None
    if args.countries:
        countries = {
            c.strip().upper() for c in args.countries.split(",") if c.strip()
        }
    site_ids: set[str] | None = set(args.site_id) if args.site_id else None

    run_id = (
        f"fix04-verify-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    )

    print(f"[{_ts()}] === FIX-04 three-way verification (no Overpass) ===")
    print(f"[{_ts()}] Source JSONL: {args.jsonl}")
    print(f"[{_ts()}] Run ID:       {run_id}")

    session = _build_session()
    sites_with_failures: list[dict[str, Any]] = []
    aggregate = empty_aggregate()
    per_column_flip_counts = empty_flip_counts()
    total_verified = 0
    flips_expected = 0
    flips_landed = 0

    for _, rec in iter_records(args.jsonl):
        if not select_record(rec, countries=countries, site_ids=site_ids):
            continue
        total_verified += 1
        flagged = flagged_set(rec)
        site_id = uuid.UUID(rec["site_id"])
        db_state = _fetch_db_state(session, site_id)
        failures, verdicts = evaluate_record(
            rec=rec, db_state=db_state, flagged=flagged,
        )
        for k, v in verdicts.items():
            aggregate[k] += v
        landed_here = update_flip_counts(
            flip_counts=per_column_flip_counts,
            flagged=flagged, failures=failures,
        )
        flips_expected += len(flagged)
        flips_landed += landed_here
        if failures:
            sites_with_failures.append({
                "site_id": rec["site_id"],
                "name": rec.get("name") or "",
                "country_code": rec.get("country_code") or "",
                "failures": failures,
            })
        _maybe_progress(
            total_verified=total_verified, flips_landed=flips_landed,
            flips_expected=flips_expected,
            n_failures=len(sites_with_failures),
        )

    session.close()

    args.report.parent.mkdir(parents=True, exist_ok=True)
    md = render_report(
        total=total_verified, flips_expected=flips_expected,
        flips_landed=flips_landed,
        sites_with_failures=sites_with_failures,
        aggregate=aggregate,
        per_column_flip_counts=per_column_flip_counts,
        jsonl_path=args.jsonl, head_limit=args.head_limit, run_id=run_id,
    )
    args.report.write_text(md, encoding="utf-8")

    print(f"\n[{_ts()}] === Verification complete ===")
    print(f"[{_ts()}] Sites verified:      {total_verified}")
    print(f"[{_ts()}] Flips expected:      {flips_expected}")
    print(f"[{_ts()}] Flips landed:        {flips_landed}")
    print(f"[{_ts()}] Sites with failures: {len(sites_with_failures)}")
    for k in sorted(aggregate):
        print(f"[{_ts()}]   {k:>22}: {aggregate[k]}")
    print(f"[{_ts()}] Report: {args.report}")
    return 0 if not sites_with_failures else 1


if __name__ == "__main__":
    sys.exit(main())
