# man_hours: 1.5
"""Swing-weight audit — IAEA expert-review artefact.

Compares the rubric's declared (Phase 1.2 baseline) weights to the
swing-normalised weights computed from the observed 0-10 score range
across the surviving (site, SMR) pool. Produces:

- ``audit/post_processing/06_scoring/{stamp}_swing_weight_audit.csv``
- ``report/methodology/swing_weight_audit.md``

The audit answers the IAEA reviewer's question: "Are your declared
weights doing real work, or are they being washed out by criteria with
narrow observed ranges?" Criteria with observed range = 0 (constant
score across the pool) inherit their declared weight (no swing
information).

Run:
    POSTGRES_DB=atoms_vs_ashes_merged \\
        .venv/bin/python -m scripts.generate_swing_weight_audit \\
        --db-profile merged
"""

from __future__ import annotations

import argparse
import csv
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from atoms_vs_ashes.db.analytics_writers import persist_swing_weights
from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.runs import DatasetMeta, complete_run, start_run
from atoms_vs_ashes.scoring._suite_persist import (
    _resolve_baseline_run_id,  # type: ignore[attr-defined]
    load_pairs,
)
from atoms_vs_ashes.scoring._swing_weights import (
    ObservedRange,
    observed_ranges,
    swing_normalised_weights,
    swing_weight_delta,
)
from atoms_vs_ashes.scoring.rubric import (
    Criterion,
    load_rubric_bundle,
    weight_normalisation,
)

DEFAULT_RUBRIC_DIR = Path("config/scoring_rubrics")
DEFAULT_AUDIT_DIR = Path("audit/post_processing/06_scoring")
DEFAULT_REPORT_PATH = Path("report/methodology/swing_weight_audit.md")

DB_PROFILES = {
    "api": "atoms_vs_ashes",
    "llm": "atoms_vs_ashes_llm",
    "merged": "atoms_vs_ashes_merged",
}

EXCLUDED_PUBLISHED_COUNTRIES = frozenset({"BY"})


@dataclass
class _Row:
    criterion_id: str
    family: str
    name: str
    declared: float
    observed_min: float | None
    observed_max: float | None
    swing: float
    delta: float

    def to_csv_row(self) -> dict[str, object]:
        return {
            "criterion_id": self.criterion_id,
            "family": self.family,
            "name": self.name,
            "declared_weight": round(self.declared, 6),
            "observed_min": self.observed_min,
            "observed_max": self.observed_max,
            "observed_range": (
                round(self.observed_max - self.observed_min, 4)
                if self.observed_min is not None and self.observed_max is not None
                else None
            ),
            "swing_weight": round(self.swing, 6),
            "delta": round(self.delta, 6),
        }


def _build_rows(
    bundle: dict[str, Criterion],
    declared: dict[str, float],
    swing: dict[str, float],
    ranges: dict[str, ObservedRange],
) -> list[_Row]:
    delta = swing_weight_delta(declared, swing)
    rows: list[_Row] = []
    for cid, crit in bundle.items():
        rng = ranges.get(cid)
        rows.append(
            _Row(
                criterion_id=cid,
                family=crit.family.upper(),
                name=crit.name,
                declared=float(declared.get(cid, 0.0)),
                observed_min=rng.minimum if rng else None,
                observed_max=rng.maximum if rng else None,
                swing=float(swing.get(cid, 0.0)),
                delta=float(delta.get(cid, 0.0)),
            )
        )
    rows.sort(key=lambda r: -abs(r.delta))
    return rows


def _write_csv(rows: list[_Row], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        fieldnames = [
            "criterion_id",
            "family",
            "name",
            "declared_weight",
            "observed_min",
            "observed_max",
            "observed_range",
            "swing_weight",
            "delta",
        ]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r.to_csv_row())


def _write_markdown(
    rows: list[_Row],
    path: Path,
    *,
    csv_path: Path,
    pair_count: int,
    stamp: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Swing-weight audit",
        "",
        f"- Stamp: `{stamp}`",
        f"- Pool: {pair_count} (site, SMR) pairs from the latest baseline rescore",
        f"- Source CSV: `{csv_path.as_posix()}`",
        "",
        "## What this audit shows",
        "",
        "The Phase 1.2 weights were elicited declaratively (rubric author judgement).",
        "**Swing weights** rescale each criterion by its observed 0-10 score range",
        "across the survivor pool, then renormalise. A criterion that scores 5-7 for",
        "every site adds little discriminating power, so its swing weight drops.",
        "",
        "Re-running the composite under the swing profile (``w_swing``, written by",
        "``run_weight_sensitivity``) is part of the sensitivity suite; this file is",
        "the human-readable companion to the ``audit_post_processing`` CSV that",
        "documents the per-criterion delta.",
        "",
        "## Per-criterion table (sorted by |Δ|)",
        "",
        "| Criterion | Family | Declared | Observed range | Swing | Δ (swing − declared) |",
        "| --- | --- | ---: | --- | ---: | ---: |",
    ]
    for r in rows:
        rng = (
            f"[{r.observed_min:.2f}, {r.observed_max:.2f}]"
            if r.observed_min is not None and r.observed_max is not None
            else "—"
        )
        lines.append(
            f"| {r.criterion_id} ({r.name}) | {r.family} | "
            f"{r.declared:.4f} | {rng} | {r.swing:.4f} | {r.delta:+.4f} |"
        )
    lines.extend(
        [
            "",
            "## Reading the deltas",
            "",
            "- **Δ > 0**: the criterion is **up-weighted** by swing — its observed",
            "  range across the pool is wider than the rubric's declared weight",
            "  implies. Watch for hidden drivers of the ranking.",
            "- **Δ < 0**: the criterion is **down-weighted** — it has narrow",
            "  observed range, so its declared weight is partly being absorbed by",
            "  renormalisation. The composite is robust to its weight.",
            "- **Δ ≈ 0**: declared weight is roughly aligned with the swing.",
            "",
            "## Provenance",
            "",
            "- Generator: `python -m scripts.generate_swing_weight_audit`",
            "- Module: `atoms_vs_ashes.scoring._swing_weights`",
            "- Profile injected into the suite: `w_swing` (see "
            "`atoms_vs_ashes.scoring._weight_perturbation`).",
        ]
    )
    path.write_text("\n".join(lines).rstrip() + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db-profile",
        choices=sorted(DB_PROFILES),
        default="merged",
    )
    parser.add_argument("--rubric-dir", type=Path, default=DEFAULT_RUBRIC_DIR)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument(
        "--weight-profile-base",
        default="baseline",
        help="Composite profile to anchor the swing pool on.",
    )
    parser.add_argument("--stamp", default=datetime.now(UTC).strftime("%Y%m%d"))
    args = parser.parse_args(argv)

    os.environ["POSTGRES_DB"] = DB_PROFILES[args.db_profile]

    bundle = load_rubric_bundle(args.rubric_dir)
    declared = weight_normalisation(bundle, profile="baseline")

    csv_path = args.audit_dir / f"{args.stamp}_swing_weight_audit.csv"

    with session_scope() as session:
        parent_run_id = _resolve_baseline_run_id(
            session, weight_profile_base=args.weight_profile_base
        )
        handle = start_run(
            session,
            run_kind="swing_audit",
            cli_command="scripts.generate_swing_weight_audit",
            parent_run_id=parent_run_id,
            run_id=f"swing_{args.stamp}_{(parent_run_id or 'noref')[-8:]}",
            dataset_meta=DatasetMeta(
                rubric_file_path=str(args.rubric_dir),
                weight_normalisation_profile=args.weight_profile_base,
            ),
        )
        rows_by_pair, _verdicts, countries = load_pairs(
            session, weight_profile_base=args.weight_profile_base
        )
        if EXCLUDED_PUBLISHED_COUNTRIES:
            rows_by_pair = {
                pair: rs
                for pair, rs in rows_by_pair.items()
                if countries.get(pair) not in EXCLUDED_PUBLISHED_COUNTRIES
            }
        flat = [r for rs in rows_by_pair.values() for r in rs]
        ranges = observed_ranges(flat)
        pair_count = len(rows_by_pair)
        swing = swing_normalised_weights(declared, ranges)
        rows = _build_rows(bundle, declared, swing, ranges)
        persist_swing_weights(session, run_id=handle.run_id, rows=rows)
        complete_run(session, handle, status="completed")
    _write_csv(rows, csv_path)
    _write_markdown(
        rows,
        args.report_path,
        csv_path=csv_path,
        pair_count=pair_count,
        stamp=args.stamp,
    )

    print(f"Wrote {csv_path}")
    print(f"Wrote {args.report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
