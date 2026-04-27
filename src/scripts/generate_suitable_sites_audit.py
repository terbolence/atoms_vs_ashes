# man_hours: 1.0
"""Generate the suitable-sites scoring audit artefact bundle."""

from __future__ import annotations

import argparse
import os
from datetime import UTC, datetime
from pathlib import Path

from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.scoring_audit import collect_audit_rules
from atoms_vs_ashes.scoring_audit.db import (
    code_impacts,
    criterion_score_summaries,
    ep01_disjunct_impacts,
    resolve_latest_run_id,
    suitability_counts,
)
from atoms_vs_ashes.scoring_audit.report import (
    write_audit_report,
    write_counts_csv,
    write_csv,
)
from atoms_vs_ashes.scoring_audit.status import build_audit_status_rows

DB_PROFILES = {
    "api": "atoms_vs_ashes",
    "llm": "atoms_vs_ashes_llm",
    "merged": "atoms_vs_ashes_merged",
}
DEFAULT_OUT_ROOT = Path("audit/scoring_mechanism_audits")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-profile", choices=sorted(DB_PROFILES), default="merged")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--weight-profile", default="baseline")
    parser.add_argument(
        "--stamp", default=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    )
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--rubric-dir", type=Path, default=Path("config/scoring_rubrics"))
    parser.add_argument(
        "--threshold-metadata",
        type=Path,
        default=Path("config/scoring_specs/threshold_metadata.yaml"),
    )
    args = parser.parse_args(argv)

    os.environ["POSTGRES_DB"] = DB_PROFILES[args.db_profile]
    out_dir = args.out_root / f"{args.stamp}_suitable_sites_scoring_audit"
    rules = collect_audit_rules(args.rubric_dir, args.threshold_metadata)
    write_csv(out_dir / "ea_catalogue.csv", rules)

    counts = None
    impacts = []
    ep01_rows = []
    score_rows = []
    with session_scope() as session:
        run_id = args.run_id or resolve_latest_run_id(
            session, weight_profile=args.weight_profile
        )
        if run_id:
            counts = suitability_counts(
                session, run_id=run_id, weight_profile=args.weight_profile
            )
            impacts = code_impacts(session, run_id=run_id)
            ep01_rows = ep01_disjunct_impacts(session, run_id=run_id)
            score_rows = criterion_score_summaries(session, run_id=run_id)

    if counts is not None:
        write_counts_csv(out_dir / "suitability_counts.csv", counts)
    write_csv(out_dir / "code_impacts.csv", impacts)
    write_csv(out_dir / "ep01_disjunct_impacts.csv", ep01_rows)
    write_csv(out_dir / "audit_status.csv", build_audit_status_rows(rules, impacts))
    write_csv(out_dir / "criterion_score_summaries.csv", score_rows)
    write_audit_report(
        out_dir / "audit_report.md",
        counts=counts,
        rules=rules,
        impacts=impacts,
        ep01_impacts=ep01_rows,
        score_summaries=score_rows,
    )

    print(f"Suitable-sites audit written to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
