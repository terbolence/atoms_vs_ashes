# man_hours: 1.5
"""Full forensic DB extract for a single SMR design.

Pulls every analytics + raw-fact table relevant to a chosen ``--smr-key``
(latest scoring / sensitivity / failure runs unless overridden) and emits
CSV-per-table plus a single Excel workbook (one sheet per table) under
``audit/post_processing/db_extract/<stamp>_<smr>/``. Read-only.

Usage::

    python -m scripts.extract_smr_db \\
        --db-profile merged --smr-key nuscale_voygr6 --stamp 20260425b
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.engine import init_engine, session_scope
from atoms_vs_ashes.db.models_analytics import Run
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring._suite_persist import _resolve_baseline_run_id

log = get_logger(__name__)

DB_PROFILES = {
    "api": "atoms_vs_ashes",
    "llm": "atoms_vs_ashes_llm",
    "merged": "atoms_vs_ashes_merged",
}

# (sheet_name, sql, params_keys). Each SQL gets only the named binds it needs.
TABLE_QUERIES: list[tuple[str, str, tuple[str, ...]]] = [
    ("00_runs",
     "SELECT * FROM runs WHERE run_id IN "
     "(:scoring_run_id, :sensitivity_run_id, :failure_run_id) ORDER BY started_at",
     ("scoring_run_id", "sensitivity_run_id", "failure_run_id")),
    ("01_sites",
     "SELECT site_id, name, country_code, country_name, latitude, longitude, "
     "plant_type, status, region, elevation_m, installed_capacity_mw, "
     "site_area_ha FROM sites ORDER BY country_code, name",
     ()),
    ("02_composite_rankings",
     "SELECT cr.*, s.name AS site_name, s.country_code "
     "FROM composite_rankings cr JOIN sites s USING(site_id) "
     "WHERE cr.smr_key=:smr_key AND cr.run_id=:scoring_run_id "
     "ORDER BY cr.weight_profile, cr.composite_score DESC NULLS LAST",
     ("smr_key", "scoring_run_id")),
    ("03_composite_components",
     "SELECT csc.*, s.name AS site_name, s.country_code "
     "FROM composite_score_components csc JOIN sites s USING(site_id) "
     "WHERE csc.smr_key=:smr_key AND csc.run_id=:scoring_run_id "
     "ORDER BY csc.weight_profile, s.country_code, s.name, csc.criterion_id",
     ("smr_key", "scoring_run_id")),
    ("04_ranking_scores",
     "SELECT rs.*, s.name AS site_name, s.country_code "
     "FROM ranking_scores rs JOIN sites s USING(site_id) "
     "WHERE rs.smr_key=:smr_key AND rs.run_id=:scoring_run_id "
     "ORDER BY s.country_code, s.name, rs.criterion_id",
     ("smr_key", "scoring_run_id")),
    ("05_screening_verdicts",
     "SELECT sv.*, s.name AS site_name, s.country_code "
     "FROM screening_verdicts sv JOIN sites s USING(site_id) "
     "WHERE sv.smr_key=:smr_key "
     "ORDER BY s.country_code, s.name, sv.phase, sv.criterion_id, sv.prompt_key",
     ("smr_key",)),
    ("06_failure_outcomes",
     "SELECT fo.*, s.name AS site_name, s.country_code "
     "FROM failure_outcomes fo JOIN sites s USING(site_id) "
     "WHERE fo.smr_key=:smr_key AND fo.run_id=:failure_run_id "
     "ORDER BY (fo.bucket='survived') DESC, fo.bucket, s.country_code, s.name",
     ("smr_key", "failure_run_id")),
    ("07_failure_aggregates",
     "SELECT * FROM failure_aggregates "
     "WHERE run_id=:failure_run_id "
     "AND (scope_smr_key=:smr_key OR scope_smr_key='_all_') "
     "ORDER BY scope_smr_key, axis, key",
     ("smr_key", "failure_run_id")),
    ("08_country_site_rankings",
     "SELECT csr.*, s.name AS site_name "
     "FROM country_site_rankings csr JOIN sites s USING(site_id) "
     "WHERE csr.smr_key=:smr_key AND csr.run_id=:sensitivity_run_id "
     "ORDER BY csr.country_code, csr.national_rank",
     ("smr_key", "sensitivity_run_id")),
    ("09_site_bands",
     "SELECT sb.*, s.name AS site_name, s.country_code "
     "FROM site_bands sb JOIN sites s USING(site_id) "
     "WHERE sb.smr_key=:smr_key AND sb.run_id=:sensitivity_run_id "
     "ORDER BY sb.scope_country_code, sb.band, s.name",
     ("smr_key", "sensitivity_run_id")),
    ("10_country_summary",
     "SELECT * FROM country_rankings_summary "
     "WHERE run_id=:sensitivity_run_id "
     "AND (smr_key=:smr_key OR smr_key='_all_') "
     "ORDER BY smr_key, country_code",
     ("smr_key", "sensitivity_run_id")),
    ("11_oat_importance",
     "SELECT * FROM oat_importance WHERE run_id=:sensitivity_run_id "
     "ORDER BY importance_score DESC NULLS LAST",
     ("sensitivity_run_id",)),
    ("12_threshold_sensitivity",
     "SELECT * FROM threshold_sensitivity WHERE run_id=:sensitivity_run_id "
     "ORDER BY criterion_id, direction",
     ("sensitivity_run_id",)),
    ("13_weight_stability",
     "SELECT * FROM weight_profile_stability WHERE run_id=:sensitivity_run_id "
     "ORDER BY weight_profile",
     ("sensitivity_run_id",)),
    ("14_criterion_correlations",
     "SELECT * FROM criterion_correlations WHERE run_id=:sensitivity_run_id "
     "ORDER BY criterion_a, criterion_b",
     ("sensitivity_run_id",)),
    ("15_swing_weights",
     "SELECT * FROM swing_weights ORDER BY family, criterion_id",
     ()),
    ("20_raw_natural_hazards",
     "SELECT s.country_code, s.name AS site_name, snh.* "
     "FROM site_natural_hazards snh JOIN sites s USING(site_id) "
     "ORDER BY s.country_code, s.name",
     ()),
    ("21_raw_human_hazards",
     "SELECT s.country_code, s.name AS site_name, shh.* "
     "FROM site_human_hazards shh JOIN sites s USING(site_id) "
     "ORDER BY s.country_code, s.name",
     ()),
    ("22_raw_radiological",
     "SELECT s.country_code, s.name AS site_name, sr.* "
     "FROM site_radiological sr JOIN sites s USING(site_id) "
     "ORDER BY s.country_code, s.name",
     ()),
    ("23_raw_emergency_planning",
     "SELECT s.country_code, s.name AS site_name, sep.* "
     "FROM site_emergency_planning sep JOIN sites s USING(site_id) "
     "ORDER BY s.country_code, s.name",
     ()),
    ("24_raw_infrastructure",
     "SELECT s.country_code, s.name AS site_name, si.* "
     "FROM site_infrastructure_v2 si JOIN sites s USING(site_id) "
     "ORDER BY s.country_code, s.name",
     ()),
]


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--db-profile", choices=sorted(DB_PROFILES), default="merged")
    p.add_argument("--smr-key", required=True,
                   help="e.g. nuscale_voygr6, bwrx_300, holtec_smr300, ...")
    p.add_argument("--scoring-run-id", default=None)
    p.add_argument("--sensitivity-run-id", default=None)
    p.add_argument("--failure-run-id", default=None)
    p.add_argument("--weight-profile", default="baseline")
    p.add_argument("--stamp", default=None,
                   help="Output stamp (default: today UTC).")
    p.add_argument("--out-root", default="audit/post_processing/db_extract")
    p.add_argument("--no-excel", action="store_true")
    return p


def _stamp(arg: str | None) -> str:
    return arg or datetime.now(timezone.utc).strftime("%Y%m%d")


def _latest_run(session: Session, kind: str) -> str | None:
    return session.execute(
        select(Run.run_id)
        .where(Run.run_kind == kind, Run.status == "completed")
        .order_by(Run.started_at.desc()).limit(1)
    ).scalar_one_or_none()


def _resolve_ids(session: Session, args: argparse.Namespace) -> dict[str, str]:
    score = args.scoring_run_id or _resolve_baseline_run_id(
        session, weight_profile_base=args.weight_profile,
    )
    sens = args.sensitivity_run_id or _latest_run(session, "sensitivity")
    fail = args.failure_run_id or _latest_run(session, "failure_analysis")
    missing = [k for k, v in [("scoring", score), ("sensitivity", sens),
                              ("failure_analysis", fail)] if v is None]
    if missing:
        raise SystemExit(f"No completed run found for: {', '.join(missing)}")
    return {"scoring_run_id": score, "sensitivity_run_id": sens,
            "failure_run_id": fail, "smr_key": args.smr_key}


def _query_table(engine: Engine, sql: str, params: dict) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)


def _dump_csvs(
    engine: Engine, ids: dict[str, str], out_dir: Path,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    frames: dict[str, pd.DataFrame] = {}
    for sheet, sql, keys in TABLE_QUERIES:
        params = {k: ids[k] for k in keys}
        try:
            df = _query_table(engine, sql, params)
        except Exception as exc:  # noqa: BLE001
            log.warning("extract_table_failed", sheet=sheet, error=str(exc)[:200])
            df = pd.DataFrame()
        df.to_csv(out_dir / f"{sheet}.csv", index=False)
        frames[sheet] = df
        log.info("extract_table", sheet=sheet, rows=len(df))
    return frames


_XL_CELL_LIMIT = 32_700


def _excel_safe(df: pd.DataFrame) -> pd.DataFrame:
    # Dedupe duplicate column labels so df[c] always returns a Series.
    cols = list(df.columns)
    seen: dict[str, int] = {}
    new_cols: list[str] = []
    for c in cols:
        if c in seen:
            seen[c] += 1
            new_cols.append(f"{c}__{seen[c]}")
        else:
            seen[c] = 0
            new_cols.append(c)
    df = df.copy()
    df.columns = new_cols
    for c in df.columns:
        col = df[c]
        if pd.api.types.is_datetime64_any_dtype(col) and \
                getattr(col.dt, "tz", None) is not None:
            df[c] = col.dt.tz_convert("UTC").dt.tz_localize(None)
        elif col.dtype == object:
            def _trim(v):
                if v is None:
                    return v
                if not isinstance(v, str):
                    v = str(v)
                if len(v) > _XL_CELL_LIMIT:
                    return v[:_XL_CELL_LIMIT] + "…[truncated; see CSV]"
                return v
            df[c] = col.apply(_trim)
    return df


def _write_workbook(frames: dict[str, pd.DataFrame], path: Path) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as xl:
        for sheet, df in frames.items():
            _excel_safe(df).to_excel(xl, sheet_name=sheet[:31], index=False)


def _write_manifest(
    out_dir: Path, ids: dict[str, str], frames: dict[str, pd.DataFrame],
) -> None:
    lines = [
        "# DB extract manifest", "",
        f"- generated_at: {datetime.now(timezone.utc).isoformat()}",
        f"- smr_key: {ids['smr_key']}",
        f"- scoring_run_id: {ids['scoring_run_id']}",
        f"- sensitivity_run_id: {ids['sensitivity_run_id']}",
        f"- failure_run_id: {ids['failure_run_id']}",
        "", "## Sheets / CSVs", "", "| Sheet | Rows |", "|---|---:|",
    ]
    for sheet, df in frames.items():
        lines.append(f"| {sheet} | {len(df)} |")
    (out_dir / "MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run(args: argparse.Namespace) -> Path:
    os.environ["POSTGRES_DB"] = DB_PROFILES[args.db_profile]
    init_engine(Settings())
    out_dir = Path(args.out_root) / f"{_stamp(args.stamp)}_{args.smr_key}"
    with session_scope() as session:
        ids = _resolve_ids(session, args)
        log.info("extract_resolved", out_dir=str(out_dir), **ids)
        frames = _dump_csvs(session.bind, ids, out_dir)
    if not args.no_excel:
        _write_workbook(frames, out_dir / f"{args.smr_key}_extract.xlsx")
    _write_manifest(out_dir, ids, frames)
    return out_dir


def main(argv: list[str] | None = None) -> int:
    args = _build_argparser().parse_args(argv)
    print(str(_run(args)))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
