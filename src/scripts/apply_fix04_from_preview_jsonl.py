# man_hours: 1.4
"""Apply FIX-04 OSM avoidance enrichment by replaying the preview JSONL.

DB-only alternative to ``run_fix04_osm_avoidance_batch.py`` for the case
where a preview run has already captured fully-parsed Overpass payloads
to ``logs/hi06_fix04_preview.jsonl``. Makes **no external HTTP calls** —
reuses the apply script's ``_persist_*`` functions for byte-identical
UPSERT semantics.

See ``audit/post_processing/hi06_fix04_preview/README.md`` for the
preview-approve-apply operational notes. Pure per-record logic lives in
:mod:`_apply_fix04_from_jsonl`.

Usage::

    PYTHONPATH=src .venv/bin/python src/scripts/apply_fix04_from_preview_jsonl.py \
        --jsonl logs/hi06_fix04_preview.jsonl --dry-run

    PYTHONPATH=src .venv/bin/python src/scripts/apply_fix04_from_preview_jsonl.py \
        --jsonl logs/hi06_fix04_preview.jsonl
"""

from __future__ import annotations

import argparse
import importlib.util
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
from _apply_fix04_from_jsonl import (  # noqa: E402
    DOMAIN_LABELS, classify_payload, empty_counts, iter_records, select_record,
)


def _import_fix04():
    """Import the FIX-04 batch module so we reuse its persist functions."""
    name = "_fix04_batch_for_replay"
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
    return sessionmaker(bind=engine, future=True)()


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def _persist_one(fix04, session, label: str, site_id: uuid.UUID,
                 payload: dict[str, Any], run_id: str) -> None:
    if label == "military":
        fix04._persist_military(session, site_id, payload, run_id)
    elif label == "power":
        fix04._persist_power(session, site_id, payload, run_id)
    elif label == "transmitter":
        fix04._persist_transmitter(session, site_id, payload, run_id)
    else:  # pragma: no cover — guarded by DOMAIN_LABELS
        raise ValueError(f"Unknown domain label: {label}")


def replay_record(*, fix04, session, rec: dict[str, Any], run_id: str,
                  dry_run: bool) -> dict[str, str]:
    """Apply one record to the DB. Returns ``{label: action}``."""
    site_id = uuid.UUID(rec["site_id"])
    actions: dict[str, str] = {}
    for label in DOMAIN_LABELS:
        action, payload = classify_payload(rec, label)
        if action == "apply" and not dry_run:
            assert payload is not None
            _persist_one(fix04, session, label, site_id, payload, run_id)
        actions[label] = action
    return actions


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Apply FIX-04 OSM avoidance enrichment by replaying a preview "
            "JSONL. No external HTTP calls; reuses the apply script's "
            "_persist_* functions."
        ),
    )
    p.add_argument(
        "--jsonl", type=Path,
        default=Path("logs/hi06_fix04_preview.jsonl"),
        help="Source JSONL (default: logs/hi06_fix04_preview.jsonl).",
    )
    p.add_argument(
        "--country", dest="countries", metavar="CC,...",
        help="Comma-separated ISO country codes to replay (e.g. RO,PL).",
    )
    p.add_argument(
        "--site-id", action="append", default=[],
        help="Restrict to specific site UUIDs (repeatable).",
    )
    p.add_argument(
        "--dry-run", action="store_true",
        help="Parse JSONL and report what would be written; no DB writes.",
    )
    p.add_argument(
        "--run-id", default=None,
        help="Override the auto-generated run_id (default: fix04_replay_<UTC>).",
    )
    return p.parse_args()


def _print_header(args: argparse.Namespace, run_id: str,
                  countries: set[str] | None,
                  site_ids: set[str] | None) -> None:
    print(f"[{_ts()}] === FIX-04 replay from JSONL ===", flush=True)
    print(f"[{_ts()}] Source JSONL: {args.jsonl}", flush=True)
    print(f"[{_ts()}] Run ID:       {run_id}", flush=True)
    mode = "DRY RUN (no DB writes)" if args.dry_run else "APPLY"
    print(f"[{_ts()}] Mode:         {mode}", flush=True)
    if countries:
        print(f"[{_ts()}] Countries:    {','.join(sorted(countries))}", flush=True)
    if site_ids:
        print(f"[{_ts()}] Site IDs:     {len(site_ids)} explicit", flush=True)


def _print_summary(counts: dict[str, Any], run_id: str) -> None:
    print(f"\n[{_ts()}] === FIX-04 replay complete ===", flush=True)
    print(f"[{_ts()}] Run ID:        {run_id}", flush=True)
    print(f"[{_ts()}] Considered:    {counts['considered']}", flush=True)
    print(f"[{_ts()}] Filtered out:  {counts['filtered_out']}", flush=True)
    for label in DOMAIN_LABELS:
        a = counts["applied"][label]
        e = counts["skip_error"][label]
        n = counts["skip_no_payload"][label]
        print(
            f"[{_ts()}]   {label:>11}: applied={a}  skip-error={e}  "
            f"skip-no-payload={n}",
            flush=True,
        )
    print(f"[{_ts()}] Commit errors: {counts['commit_errors']}", flush=True)


def _process_record(*, fix04, session, line_no: int, rec: dict[str, Any],
                    run_id: str, dry_run: bool, counts: dict[str, Any]) -> None:
    try:
        actions = replay_record(
            fix04=fix04, session=session, rec=rec,
            run_id=run_id, dry_run=dry_run,
        )
    except Exception as exc:
        print(
            f"[{_ts()}] line={line_no} site={rec.get('site_id')} "
            f"REPLAY ERROR: {exc}",
            file=sys.stderr,
        )
        if session is not None:
            session.rollback()
        return

    for label, action in actions.items():
        if action == "apply":
            counts["applied"][label] += 1
        elif action == "skip-error":
            counts["skip_error"][label] += 1
        else:
            counts["skip_no_payload"][label] += 1

    if session is not None:
        try:
            session.commit()
        except Exception as exc:
            session.rollback()
            counts["commit_errors"] += 1
            print(
                f"[{_ts()}] site={rec.get('site_id')} COMMIT ERROR: {exc}",
                file=sys.stderr,
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

    fix04 = _import_fix04()
    run_id = args.run_id or (
        f"fix04_replay_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    )

    _print_header(args, run_id, countries, site_ids)

    session = None if args.dry_run else _build_session()
    if session is not None:
        # Idempotent — same as the live apply path.
        fix04._ensure_data_source(session)
        session.commit()

    counts = empty_counts()
    for line_no, rec in iter_records(args.jsonl):
        counts["considered"] += 1
        if not select_record(rec, countries=countries, site_ids=site_ids):
            counts["filtered_out"] += 1
            continue
        _process_record(
            fix04=fix04, session=session, line_no=line_no, rec=rec,
            run_id=run_id, dry_run=args.dry_run, counts=counts,
        )
        if counts["considered"] % 50 == 0:
            print(
                f"[{_ts()}] processed={counts['considered']} "
                f"applied(mil/pwr/tx)="
                f"{counts['applied']['military']}/"
                f"{counts['applied']['power']}/"
                f"{counts['applied']['transmitter']} "
                f"filtered={counts['filtered_out']}",
                flush=True,
            )

    if session is not None:
        session.close()

    _print_summary(counts, run_id)
    return 0 if counts["commit_errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
