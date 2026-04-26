# man_hours: 1.5
"""CLI orchestrator: NuScale top-10-per-country consolidated report.

Reads the persisted analytics tables populated by the Alembic-034
pipeline (scoring → sensitivity → extended) and emits a single
markdown report plus the per-country figure pack.

Usage::

    python -m scripts.build_nuscale_top10_report \
        --db-profile merged \
        --stamp 20260425b \
        --sensitivity-run-id <id>

The script is read-only against the DB and idempotent on disk: it
overwrites the markdown + figures under the chosen ``--out-dir``.
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
from atoms_vs_ashes.db.models_analytics import Run
from atoms_vs_ashes.db.runs import _git_sha  # type: ignore[attr-defined]
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring._suite_persist import _resolve_baseline_run_id
from scripts._nuscale_top10_figures import render_all_for_country
from scripts._nuscale_top10_md import NUSCALE_LABEL, render_report
from scripts._nuscale_top10_query import (
    load_composites,
    load_country_summary,
    load_family_scores,
    load_hit_rates,
    load_stability,
    load_top_n,
)

log = get_logger(__name__)


DB_PROFILES = {
    "api": "atoms_vs_ashes",
    "llm": "atoms_vs_ashes_llm",
    "merged": "atoms_vs_ashes_merged",
}


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Assemble NuScale top-N-per-country DB-backed report",
    )
    p.add_argument("--db-profile", choices=sorted(DB_PROFILES), default="merged",
                   help="Maps to POSTGRES_DB (default 'merged').")
    p.add_argument("--sensitivity-run-id", default=None,
                   help="Defaults to most recent sensitivity run.")
    p.add_argument("--scoring-run-id", default=None,
                   help="Defaults to most recent baseline scoring run.")
    p.add_argument("--smr-key", default="nuscale_voygr6")
    p.add_argument("--smr-label", default=NUSCALE_LABEL)
    p.add_argument("--stamp", default=None,
                   help="Output stamp (default: 'today' UTC).")
    p.add_argument("--top-n", type=int, default=10)
    p.add_argument("--weight-profile", default="baseline")
    p.add_argument("--out-dir", default=None,
                   help=("Override the output directory; default is "
                         "report/output/sensitivity/<stamp>."))
    p.add_argument("--no-figures", action="store_true",
                   help="Skip per-country PNG generation.")
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
        raise SystemExit(
            "No completed sensitivity run found — pass --sensitivity-run-id."
        )
    return rid


def _resolve_scoring_run_id(
    session: Session, supplied: str | None, weight_profile: str,
) -> str:
    if supplied:
        return supplied
    rid = _resolve_baseline_run_id(session, weight_profile_base=weight_profile)
    if rid is None:
        raise SystemExit(
            "No baseline scoring run found — pass --scoring-run-id."
        )
    return rid


def _collect_site_ids(rows_by_country):
    return [r["site_id"] for rows in rows_by_country.values() for r in rows]


def _emit_figures(
    *,
    rows_by_country,
    family_scores,
    composites,
    figures_dir: Path,
) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)
    for cc, rows in rows_by_country.items():
        if not rows:
            continue
        country_name = ""
        for r in rows:
            comp = composites.get(r["site_id"])
            if comp and comp.get("country_name"):
                country_name = comp["country_name"]
                break
        render_all_for_country(
            country_code=cc, country_name=country_name or cc,
            rows=rows, family_scores=family_scores, out_dir=figures_dir,
        )


def _build_summaries(
    session: Session, sensitivity_run_id: str, smr_key: str,
) -> dict[str, dict]:
    summaries = load_country_summary(
        session, run_id=sensitivity_run_id, smr_key=smr_key,
    )
    regional = load_country_summary(
        session, run_id=sensitivity_run_id, smr_key=ALL_SMR_SENTINEL,
    )
    summaries["_all_"] = regional.get("_all_") or next(
        iter(regional.values()), None,
    ) or {}
    return summaries


def _run(args: argparse.Namespace) -> Path:
    os.environ["POSTGRES_DB"] = DB_PROFILES[args.db_profile]
    init_engine(Settings())
    stamp = _resolve_stamp(args.stamp)
    out_dir = Path(args.out_dir or f"report/output/sensitivity/{stamp}")
    out_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = out_dir / "nuscale_top10" / "figures"

    with session_scope() as session:
        sens_id = _resolve_sensitivity_run_id(session, args.sensitivity_run_id)
        score_id = _resolve_scoring_run_id(
            session, args.scoring_run_id, args.weight_profile,
        )
        log.info(
            "nuscale_top10_resolved",
            sensitivity_run_id=sens_id, scoring_run_id=score_id,
            stamp=stamp, smr_key=args.smr_key, top_n=args.top_n,
        )
        rows_by_country = load_top_n(
            session, run_id=sens_id, smr_key=args.smr_key, n=args.top_n,
        )
        site_ids = _collect_site_ids(rows_by_country)
        composites = load_composites(
            session, scoring_run_id=score_id, smr_key=args.smr_key,
            site_ids=site_ids, weight_profile=args.weight_profile,
        )
        family_scores = load_family_scores(
            session, scoring_run_id=score_id, smr_key=args.smr_key,
            site_ids=site_ids, weight_profile=args.weight_profile,
        )
        hit_rates = load_hit_rates(
            session, sensitivity_run_id=sens_id, smr_key=args.smr_key,
            site_ids=site_ids,
        )
        stability = load_stability(
            session, sensitivity_run_id=sens_id,
        )
        summaries = _build_summaries(session, sens_id, args.smr_key)

    if not args.no_figures:
        _emit_figures(
            rows_by_country=rows_by_country, family_scores=family_scores,
            composites=composites, figures_dir=figures_dir,
        )

    md = render_report(
        smr_key=args.smr_key,
        smr_label=args.smr_label,
        stamp=stamp,
        sensitivity_run_id=sens_id,
        scoring_run_id=score_id,
        git_sha=_git_sha(),
        rows_by_country=rows_by_country,
        summaries=summaries,
        composites=composites,
        family_scores=family_scores,
        hit_rates=hit_rates,
        stability=stability,
    )
    md_path = out_dir / "nuscale_top10.md"
    md_path.write_text(md, encoding="utf-8")
    log.info(
        "nuscale_top10_report_written",
        path=str(md_path),
        countries=len(rows_by_country),
        sites=sum(len(v) for v in rows_by_country.values()),
    )
    return md_path


def main(argv: list[str] | None = None) -> int:
    args = _build_argparser().parse_args(argv)
    md_path = _run(args)
    print(str(md_path))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
