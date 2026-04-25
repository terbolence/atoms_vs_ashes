# man_hours: 1.0
"""Phase 1.6 failure-mode analysis — DB → CSVs + PNG charts + methodology MD.

Answers the regulator question "**why did sites fail during scoring?**"
on top of the screening verdicts persisted by the floor-rescore run.

Run patterns:

- **All packs** (default — global + 8 per-SMR)::

      .venv/bin/python -m scripts.generate_failure_analysis \\
          --db-profile merged --stamp 20260425

- **NuScale-only refresh** (global + NuScale)::

      .venv/bin/python -m scripts.generate_failure_analysis \\
          --db-profile merged --stamp 20260425 --smr-nuscale

Per-SMR vendor flags: ``--smr-nuscale``, ``--smr-geh``, ``--smr-holtec``,
``--smr-oklo``, ``--smr-rollsroyce``, ``--smr-xenergy``,
``--smr-terrapower-nominal``, ``--smr-terrapower-peak``.
"""

from __future__ import annotations

import argparse
import os
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models import ScreeningVerdict, Site
from atoms_vs_ashes.db.runs import DatasetMeta, complete_run, start_run
from scripts._phase_1_6_failure_db import persist_breakdown
from atoms_vs_ashes.scoring._suite_persist import (
    _resolve_baseline_run_id,  # type: ignore[attr-defined]
)
from atoms_vs_ashes.scoring.rubric import load_rubric_bundle
from scripts._phase_1_6_failure_pack import (
    ALL_SMR_KEYS,
    VENDOR_FLAGS,
    PackArtefacts,
    build_per_tech_packs,
    load_smr_meta,
    paths_for_global,
    paths_for_smr,
    render_pack,
)

DB_PROFILES = {
    "api": "atoms_vs_ashes",
    "llm": "atoms_vs_ashes_llm",
    "merged": "atoms_vs_ashes_merged",
}
DEFAULT_RUBRIC_DIR = Path("config/scoring_rubrics")
DEFAULT_AUDIT_DIR = Path("audit/post_processing/06_scoring")
DEFAULT_REPORT_ROOT = Path("report/output/sensitivity")
DEFAULT_METHOD_PATH = Path("report/methodology/failure_analysis.md")
DEFAULT_METHOD_ROOT = Path("report/methodology")


def _load(
    session: Session, *, baseline_label: str
) -> tuple[dict[tuple, list[ScreeningVerdict]], dict, str | None]:
    run_id = _resolve_baseline_run_id(
        session, weight_profile_base=baseline_label
    )
    country_by_site = {
        sid: code
        for sid, code in session.execute(
            select(Site.site_id, Site.country_code)
        ).all()
    }
    stmt = select(ScreeningVerdict)
    if run_id:
        stmt = stmt.where(ScreeningVerdict.run_id == run_id)
    verdicts_by_pair: dict[tuple, list[ScreeningVerdict]] = {}
    for v in session.execute(stmt).scalars().all():
        verdicts_by_pair.setdefault((v.site_id, v.smr_key), []).append(v)
    return verdicts_by_pair, country_by_site, run_id


def _selected_smr_keys(args: argparse.Namespace) -> list[str]:
    """Return the list of SMR keys to render per-SMR packs for."""
    selected: list[str] = []
    for flag, smr_key in VENDOR_FLAGS.items():
        if getattr(args, f"smr_{flag.replace('-', '_')}", False):
            selected.append(smr_key)
    if not selected:
        return list(ALL_SMR_KEYS)
    return selected


def _print_pack(art: PackArtefacts) -> None:
    label = art.smr_key or "global"
    print(f"\n[pack] {label}")
    print(f"  summary CSV    : {art.summary_csv}")
    print(f"  per-criterion  : {art.per_criterion_csv}")
    print(f"  per-country    : {art.per_country_csv}")
    if art.per_smr_csv is not None:
        print(f"  per-SMR        : {art.per_smr_csv}")
    print(f"  per-pair       : {art.per_pair_csv}")
    print(f"  figures dir    : {art.figures_dir}")
    print(f"  methodology MD : {art.method_md}")
    b = art.breakdown
    print(
        f"  breakdown      : total={b.total_pairs} survived={b.survived} "
        f"hard_only={b.hard_only} floor_only={b.floor_only} both={b.both}"
    )


def _add_vendor_flags(parser: argparse.ArgumentParser) -> None:
    for flag in VENDOR_FLAGS:
        parser.add_argument(
            f"--smr-{flag}", dest=f"smr_{flag.replace('-', '_')}",
            action="store_true",
            help=f"Render only the {flag} pack (in addition to the global pack).",
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db-profile", choices=sorted(DB_PROFILES), default="merged"
    )
    parser.add_argument("--baseline-label", default="baseline")
    parser.add_argument(
        "--stamp", default=datetime.now(UTC).strftime("%Y%m%d")
    )
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument(
        "--report-root", type=Path, default=DEFAULT_REPORT_ROOT
    )
    parser.add_argument(
        "--method-path", type=Path, default=DEFAULT_METHOD_PATH,
        help="Output path for the global methodology MD.",
    )
    parser.add_argument(
        "--method-root", type=Path, default=DEFAULT_METHOD_ROOT,
        help="Folder under which per-SMR methodology MDs are written.",
    )
    parser.add_argument("--rubric-dir", type=Path, default=DEFAULT_RUBRIC_DIR)
    parser.add_argument(
        "--skip-global", action="store_true",
        help="Skip the global pack (per-SMR packs only).",
    )
    _add_vendor_flags(parser)
    args = parser.parse_args(argv)

    os.environ["POSTGRES_DB"] = DB_PROFILES[args.db_profile]

    with session_scope() as session:
        bundle = load_rubric_bundle(args.rubric_dir)
        criterion_names = {cid: c.name for cid, c in bundle.items()}
        smr_meta = load_smr_meta(session)
        verdicts_by_pair, country_by_site, run_id = _load(
            session, baseline_label=args.baseline_label,
        )
        handle = start_run(
            session,
            run_kind="failure_analysis",
            cli_command=" ".join(["scripts.generate_failure_analysis"] + (argv or [])),
            parent_run_id=run_id,
            run_id=f"fail_{args.stamp}_{(run_id or 'noref')[-8:]}",
            dataset_meta=DatasetMeta(
                rubric_file_path=str(args.rubric_dir),
                weight_normalisation_profile=args.baseline_label,
            ),
        )
        common_kwargs = {
            "verdicts_by_pair": verdicts_by_pair,
            "country_by_site": country_by_site,
            "criterion_names": criterion_names,
            "stamp": args.stamp,
            "run_id": run_id,
            "smr_meta": smr_meta,
        }

        per_tech_packs = build_per_tech_packs(
            smr_meta=smr_meta, method_root=args.method_root,
        )

        artefacts: list[PackArtefacts] = []
        if not args.skip_global:
            global_paths = paths_for_global(
                audit_dir=args.audit_dir,
                report_root=args.report_root,
                method_path=args.method_path,
                stamp=args.stamp,
            )
            art = render_pack(
                paths=global_paths,
                per_tech_packs=per_tech_packs,
                **common_kwargs,
            )
            persist_breakdown(
                session, run_id=handle.run_id,
                breakdown=art.breakdown,
                country_by_site=country_by_site,
                scope_smr_key=None,
            )
            artefacts.append(art)

        for smr_key in _selected_smr_keys(args):
            if smr_key not in smr_meta:
                print(f"[warn] {smr_key} missing from smr_designs; skipping.")
                continue
            pack_paths = paths_for_smr(
                smr_key=smr_key,
                audit_dir=args.audit_dir,
                report_root=args.report_root,
                method_root=args.method_root,
                stamp=args.stamp,
            )
            art = render_pack(
                paths=pack_paths, smr_key=smr_key, **common_kwargs,
            )
            persist_breakdown(
                session, run_id=handle.run_id,
                breakdown=art.breakdown,
                country_by_site=country_by_site,
                scope_smr_key=smr_key,
            )
            artefacts.append(art)
        complete_run(session, handle, status="completed")

    print(f"\nRendered {len(artefacts)} pack(s) for stamp={args.stamp}.")
    for art in artefacts:
        _print_pack(art)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
