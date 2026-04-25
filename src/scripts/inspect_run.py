# man_hours: 1.0
"""CLI helpers to inspect a persisted analytics ``run_id`` from the DB.

Subcommands:

- ``top-n-per-country`` — top-N (sites) per country for a given SMR.
- ``site-criterion-scores`` — per-criterion 0-10 contributions for one site.
- ``site-sensitivity-profile`` — composite + band + active profile drift.
- ``failure-explanation`` — failure bucket + verdict trail.
- ``threshold-summary`` — per-direction threshold roll-up.

All outputs are JSON on stdout so the CLI is composable in shell pipelines.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.queries import (
    failure_explanation,
    site_criterion_scores,
    site_sensitivity_profile,
    threshold_summary,
    top_n_per_country,
)
from atoms_vs_ashes.db.engine import init_engine, session_scope


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("inspect_run")
    p.add_argument("--run-id", required=True)
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("top-n-per-country")
    a.add_argument("--smr", required=True)
    a.add_argument("--n", type=int, default=10)
    a.add_argument("--country")

    b = sub.add_parser("site-criterion-scores")
    b.add_argument("--site-id", required=True)
    b.add_argument("--smr", required=True)
    b.add_argument("--profile", default="baseline")

    c = sub.add_parser("site-sensitivity-profile")
    c.add_argument("--site-id", required=True)
    c.add_argument("--smr", required=True)

    d = sub.add_parser("failure-explanation")
    d.add_argument("--site-id", required=True)
    d.add_argument("--smr", required=True)

    e = sub.add_parser("threshold-summary")
    e.add_argument("--direction", choices=("plus_25", "minus_25"))
    return p


def _site_uuid(raw: str) -> uuid.UUID:
    try:
        return uuid.UUID(raw)
    except ValueError as exc:
        raise SystemExit(f"invalid site_id (expect UUID): {raw}") from exc


def _dispatch(args) -> object:
    with session_scope() as session:
        if args.cmd == "top-n-per-country":
            return top_n_per_country(
                session, run_id=args.run_id, smr_key=args.smr,
                n=args.n, country_code=args.country,
            )
        if args.cmd == "site-criterion-scores":
            return site_criterion_scores(
                session, run_id=args.run_id,
                site_id=_site_uuid(args.site_id), smr_key=args.smr,
                weight_profile=args.profile,
            )
        if args.cmd == "site-sensitivity-profile":
            return site_sensitivity_profile(
                session, run_id=args.run_id,
                site_id=_site_uuid(args.site_id), smr_key=args.smr,
            )
        if args.cmd == "failure-explanation":
            return failure_explanation(
                session, run_id=args.run_id,
                site_id=_site_uuid(args.site_id), smr_key=args.smr,
            )
        if args.cmd == "threshold-summary":
            return threshold_summary(
                session, run_id=args.run_id, direction=args.direction,
            )
        raise SystemExit(f"unknown subcommand {args.cmd!r}")


def _json_default(obj):
    if isinstance(obj, uuid.UUID):
        return str(obj)
    raise TypeError(f"non-serialisable {type(obj)}")


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    init_engine(Settings())
    payload = _dispatch(args)
    json.dump(payload, sys.stdout, indent=2, default=_json_default)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
