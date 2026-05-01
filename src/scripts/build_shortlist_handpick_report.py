# man_hours: 1.0
"""Emit hand-pick shortlist markdown (top N per country + avoidance annex).

Usage::

    PYTHONPATH=src python -m scripts.build_shortlist_handpick_report \\
        --db-profile merged \\
        --scoring-run-id score-fae96308 \\
        --sensitivity-run-id sens-a9f3e400 \\
        --smr-key nuscale_voygr6 \\
        --top-n 5 \\
        --stamp 20260429_handpick
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.analytics_writers import ALL_SMR_SENTINEL
from atoms_vs_ashes.db.engine import init_engine, session_scope
from atoms_vs_ashes.db.models_analytics import CountrySiteRanking, Run
from atoms_vs_ashes.db.runs import _git_sha  # type: ignore[attr-defined]
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring._suite_persist import _resolve_baseline_run_id
from scripts._shortlist_handpick_md import render_shortlist_handpick_md
from scripts._shortlist_handpick_query import (
    load_avoidance_flagged_pairs,
    load_avoidance_verdicts_for_pairs,
    load_full_pass_pairs,
    load_shortlist_grouped,
)

log = get_logger(__name__)

DB_PROFILES = {
    "api": "atoms_vs_ashes",
    "llm": "atoms_vs_ashes_llm",
    "merged": "atoms_vs_ashes_merged",
}


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="DB-backed shortlist + avoidance annex (markdown)",
    )
    p.add_argument(
        "--db-profile",
        choices=sorted(DB_PROFILES),
        default="merged",
        help="Maps to POSTGRES_DB.",
    )
    p.add_argument(
        "--sensitivity-run-id",
        default=None,
        help="Sensitivity run (country_site_rankings). Default: latest completed.",
    )
    p.add_argument(
        "--scoring-run-id",
        default=None,
        help="Scoring run (composite_rankings, screening_verdicts). "
        "Default: latest baseline scoring run.",
    )
    p.add_argument("--smr-key", default=None, help="SMR key (default: infer from rankings).")
    p.add_argument("--stamp", default=None, help="Output stamp (default: today UTC).")
    p.add_argument("--top-n", type=int, default=5, help="Max sites per country (default 5).")
    p.add_argument("--weight-profile", default="baseline")
    p.add_argument(
        "--out-dir",
        default=None,
        help="Override output directory (default report/output/sensitivity/<stamp>).",
    )
    return p


def _resolve_stamp(arg: str | None) -> str:
    if arg:
        return arg
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y%m%d")


def _resolve_sensitivity_run_id(session: Session, supplied: str | None) -> str:
    if supplied:
        return supplied
    rid = session.execute(
        select(Run.run_id)
        .where(Run.run_kind == "sensitivity")
        .where(Run.status == "completed")
        .order_by(Run.started_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if rid is None:
        raise SystemExit("No completed sensitivity run — pass --sensitivity-run-id.")
    return rid


def _resolve_scoring_run_id(
    session: Session, supplied: str | None, weight_profile: str,
) -> str:
    if supplied:
        return supplied
    rid = _resolve_baseline_run_id(session, weight_profile_base=weight_profile)
    if rid is None:
        raise SystemExit("No baseline scoring run — pass --scoring-run-id.")
    return rid


def _infer_smr_key(session: Session, sensitivity_run_id: str) -> str:
    concrete = session.execute(
        select(CountrySiteRanking.smr_key)
        .where(CountrySiteRanking.run_id == sensitivity_run_id)
        .where(CountrySiteRanking.smr_key != ALL_SMR_SENTINEL)
        .distinct()
        .limit(2)
    ).all()
    if not concrete:
        rid = session.execute(
            select(CountrySiteRanking.smr_key)
            .where(CountrySiteRanking.run_id == sensitivity_run_id)
            .distinct()
            .limit(2)
        ).all()
        if not rid:
            raise SystemExit(
                f"No country_site_rankings for run_id={sensitivity_run_id!r} — "
                "pass --smr-key explicitly.",
            )
        keys = [row[0] for row in rid]
        if len(keys) > 1:
            raise SystemExit(
                f"Multiple smr_key values (incl. sentinel): {keys!r}. "
                "Pass --smr-key explicitly.",
            )
        return str(keys[0])
    keys = [row[0] for row in concrete]
    if len(keys) > 1:
        raise SystemExit(
            f"Multiple concrete smr_key values in country_site_rankings: {keys!r}. "
            "Pass --smr-key explicitly.",
        )
    return str(keys[0])


def _run(args: argparse.Namespace) -> Path:
    os.environ["POSTGRES_DB"] = DB_PROFILES[args.db_profile]
    init_engine(Settings())
    stamp = _resolve_stamp(args.stamp)
    out_dir = Path(args.out_dir or f"report/output/sensitivity/{stamp}")
    out_dir.mkdir(parents=True, exist_ok=True)

    with session_scope() as session:
        sens_id = _resolve_sensitivity_run_id(session, args.sensitivity_run_id)
        score_id = _resolve_scoring_run_id(
            session, args.scoring_run_id, args.weight_profile,
        )
        smr_key = args.smr_key or _infer_smr_key(session, sens_id)
        log.info(
            "shortlist_handpick_resolved",
            sensitivity_run_id=sens_id,
            scoring_run_id=score_id,
            smr_key=smr_key,
            stamp=stamp,
            top_n=args.top_n,
        )
        shortlist = load_shortlist_grouped(
            session,
            sensitivity_run_id=sens_id,
            scoring_run_id=score_id,
            smr_key=smr_key,
            top_n=args.top_n,
            weight_profile=args.weight_profile,
        )
        full_pass = load_full_pass_pairs(
            session,
            scoring_run_id=score_id,
            smr_key=smr_key,
            weight_profile=args.weight_profile,
        )
        avoidance_pairs = load_avoidance_flagged_pairs(
            session,
            scoring_run_id=score_id,
            smr_key=smr_key,
            weight_profile=args.weight_profile,
        )
        pair_keys = [
            (r["site_id"], str(r["smr_key"]))
            for r in avoidance_pairs
        ]
        verdicts_by_pair = load_avoidance_verdicts_for_pairs(
            session, scoring_run_id=score_id, pairs=pair_keys,
        )

    md = render_shortlist_handpick_md(
        stamp=stamp,
        scoring_run_id=score_id,
        sensitivity_run_id=sens_id,
        smr_key=smr_key,
        weight_profile=args.weight_profile,
        db_profile=args.db_profile,
        git_sha=_git_sha(),
        top_n=args.top_n,
        shortlist_by_country=shortlist,
        full_pass_rows=full_pass,
        avoidance_pairs=avoidance_pairs,
        verdicts_by_pair=verdicts_by_pair,
    )
    path = out_dir / "shortlist_handpick.md"
    path.write_text(md, encoding="utf-8")
    log.info("shortlist_handpick_written", path=str(path))
    return path


def main(argv: list[str] | None = None) -> int:
    args = _build_argparser().parse_args(argv)
    out = _run(args)
    print(str(out))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
