# man_hours: 0.5
"""Export one site narrative bundle as JSON.

This is a read-only helper for report drafting. It does not call external APIs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import uuid

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.engine import init_engine, session_scope
from atoms_vs_ashes.reporting import build_site_bundle


def _site_uuid(raw: str) -> uuid.UUID:
    try:
        return uuid.UUID(raw)
    except ValueError as exc:
        raise SystemExit(f"invalid site_id (expect UUID): {raw}") from exc


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("export_site_bundle")
    p.add_argument("--site-id", required=True, help="Site UUID")
    p.add_argument("--smr", required=True, help="SMR key, e.g. nuscale_voygr6")
    p.add_argument("--run-id", required=True, help="Persisted analytics run_id")
    p.add_argument(
        "--sensitivity-stamp",
        default="20260425b",
        help="Report output stamp used for file links (default: 20260425b)",
    )
    p.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path; stdout is used when omitted",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    init_engine(Settings())
    with session_scope() as session:
        payload = build_site_bundle(
            session,
            site_id=_site_uuid(args.site_id),
            smr_key=args.smr,
            run_id=args.run_id,
            sensitivity_stamp=args.sensitivity_stamp,
        )

    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        sys.stdout.write(text)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
