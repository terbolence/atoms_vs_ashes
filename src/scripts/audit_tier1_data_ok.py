# man_hours: 6.0
"""Read-only distribution audit for Tier 1 Data OK scoring repair.

The script reads existing site/domain/ranking rows, evaluates the current
working-tree band logic in memory, and writes Markdown/CSV artifacts. It never
modifies the database.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from sqlalchemy import and_, select

from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models import (
    RankingScore,
    Site,
    SiteHumanHazards,
    SiteNaturalHazards,
)
from atoms_vs_ashes.scoring.bands import evaluate_criterion_value
from atoms_vs_ashes.scoring.merge_context_derivations import apply_derived_context_values
from atoms_vs_ashes.scoring.rubric import load_rubric_bundle

DEFAULT_RUN_ID = "20260517T104618_459ae424"
DEFAULT_SMR_KEY = "nuscale_voygr6"
DEFAULT_OUT_DIR = Path("audit/post_processing/06_scoring")
CRITERIA = ("HI-07", "NH-10", "NH-12")

FIELD_MAP: dict[str, tuple[str, ...]] = {
    "HI-07": (
        "transmitter_count",
        "nearest_transmitter_km",
        "transmitter_type",
        "hi07_quality",
        "hi07_comment",
        "human_run_id",
        "human_fetched_at",
    ),
    "NH-10": (
        "max_wind_speed_ms",
        "nh10_quality",
        "nh10_comment",
        "natural_run_id",
        "natural_fetched_at",
    ),
    "NH-12": (
        "extreme_temp_max_c",
        "extreme_temp_min_c",
        "nh12_quality",
        "nh12_comment",
        "natural_run_id",
        "natural_fetched_at",
    ),
}

QUALITY_FIELD = {
    "HI-07": "hi07_quality",
    "NH-10": "nh10_quality",
    "NH-12": "nh12_quality",
}


@dataclass(frozen=True)
class AuditRecord:
    """One site x criterion row for read-only scoring diagnostics."""

    site_id: str
    name: str
    country_code: str
    latitude: float | None
    longitude: float | None
    criterion_id: str
    smr_key: str
    baseline_score: float | None
    baseline_quality_flag: str | None
    baseline_confidence: str | None
    baseline_justification: str | None
    candidate_score: float | None
    candidate_quality_flag: str | None
    candidate_band: str | None
    fields: dict[str, Any]


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def _criterion_context(criterion_id: str, fields: dict[str, Any]) -> dict[str, Any]:
    context = {k: v for k, v in fields.items() if not k.endswith("_fetched_at")}
    if criterion_id == "HI-07":
        context["transmitter_count_10km"] = fields.get("transmitter_count")
    apply_derived_context_values(context)
    return context


def candidate_result(
    criterion_id: str,
    fields: dict[str, Any],
    bundle: dict[str, Any],
) -> tuple[float, str, str]:
    """Evaluate current working-tree logic without writing DB rows."""
    criterion = bundle[criterion_id]
    context = _criterion_context(criterion_id, fields)
    result = evaluate_criterion_value(
        criterion,
        context,
        quality=fields.get(QUALITY_FIELD[criterion_id]),
    )
    quality_flag = "unscored" if result.notes and "unscored" in result.notes else "scored"
    band = result.matched_band.descriptor if result.matched_band else result.descriptor
    return float(result.score), quality_flag, band


def fetch_records(run_id: str, smr_key: str, rubric_dir: str) -> list[AuditRecord]:
    """Read local DB rows and evaluate candidate scores in memory."""
    bundle = load_rubric_bundle(rubric_dir)
    records: list[AuditRecord] = []
    with session_scope() as session:
        for criterion_id in CRITERIA:
            score_join = and_(
                RankingScore.site_id == Site.site_id,
                RankingScore.run_id == run_id,
                RankingScore.smr_key == smr_key,
                RankingScore.criterion_id == criterion_id,
            )
            stmt = (
                select(Site, SiteHumanHazards, SiteNaturalHazards, RankingScore)
                .outerjoin(SiteHumanHazards, SiteHumanHazards.site_id == Site.site_id)
                .outerjoin(SiteNaturalHazards, SiteNaturalHazards.site_id == Site.site_id)
                .outerjoin(RankingScore, score_join)
                .order_by(Site.country_code, Site.name)
            )
            for site, human, natural, score in session.execute(stmt).all():
                fields = _fields_for(criterion_id, human, natural)
                cand_score, cand_flag, cand_band = candidate_result(
                    criterion_id, fields, bundle,
                )
                records.append(
                    AuditRecord(
                        site_id=str(site.site_id),
                        name=str(site.name),
                        country_code=str(site.country_code),
                        latitude=_to_float(site.latitude),
                        longitude=_to_float(site.longitude),
                        criterion_id=criterion_id,
                        smr_key=smr_key,
                        baseline_score=(
                            _to_float(score.score_0_10) if score is not None else None
                        ),
                        baseline_quality_flag=(
                            str(score.quality_flag) if score is not None else None
                        ),
                        baseline_confidence=(
                            str(score.confidence) if score is not None else None
                        ),
                        baseline_justification=(
                            str(score.justification) if score is not None else None
                        ),
                        candidate_score=cand_score,
                        candidate_quality_flag=cand_flag,
                        candidate_band=cand_band,
                        fields=fields,
                    )
                )
    return records


def _fields_for(
    criterion_id: str,
    human: SiteHumanHazards | None,
    natural: SiteNaturalHazards | None,
) -> dict[str, Any]:
    if criterion_id == "HI-07":
        return {
            "transmitter_count": getattr(human, "transmitter_count", None),
            "nearest_transmitter_km": _to_float(getattr(human, "nearest_transmitter_km", None)),
            "transmitter_type": getattr(human, "transmitter_type", None),
            "hi07_quality": getattr(human, "hi07_quality", None),
            "hi07_comment": getattr(human, "hi07_comment", None),
            "human_run_id": getattr(human, "run_id", None),
            "human_fetched_at": getattr(human, "fetched_at", None),
        }
    if criterion_id == "NH-10":
        return {
            "max_wind_speed_ms": _to_float(getattr(natural, "max_wind_speed_ms", None)),
            "nh10_quality": getattr(natural, "nh10_quality", None),
            "nh10_comment": getattr(natural, "nh10_comment", None),
            "natural_run_id": getattr(natural, "run_id", None),
            "natural_fetched_at": getattr(natural, "fetched_at", None),
        }
    return {
        "extreme_temp_max_c": _to_float(getattr(natural, "extreme_temp_max_c", None)),
        "extreme_temp_min_c": _to_float(getattr(natural, "extreme_temp_min_c", None)),
        "nh12_quality": getattr(natural, "nh12_quality", None),
        "nh12_comment": getattr(natural, "nh12_comment", None),
        "natural_run_id": getattr(natural, "run_id", None),
        "natural_fetched_at": getattr(natural, "fetched_at", None),
    }


def numeric_summary(values: Iterable[Any]) -> dict[str, float | int | None]:
    """Return simple distribution statistics for non-null numeric values."""
    nums = sorted(v for v in (_to_float(v) for v in values) if v is not None)
    if not nums:
        return {"count": 0, "min": None, "p05": None, "p25": None, "median": None,
                "p75": None, "p95": None, "max": None, "mean": None, "stdev": None}
    return {
        "count": len(nums),
        "min": nums[0],
        "p05": _percentile(nums, 0.05),
        "p25": _percentile(nums, 0.25),
        "median": _percentile(nums, 0.50),
        "p75": _percentile(nums, 0.75),
        "p95": _percentile(nums, 0.95),
        "max": nums[-1],
        "mean": statistics.mean(nums),
        "stdev": statistics.stdev(nums) if len(nums) > 1 else 0.0,
    }


def _percentile(nums: list[float], p: float) -> float:
    if len(nums) == 1:
        return nums[0]
    idx = p * (len(nums) - 1)
    lo = int(idx)
    hi = min(lo + 1, len(nums) - 1)
    frac = idx - lo
    return nums[lo] * (1 - frac) + nums[hi] * frac


def write_outputs(records: list[AuditRecord], out_dir: Path, stamp: str) -> list[Path]:
    """Write detail CSV, summary CSV, and Markdown curation memo."""
    out_dir.mkdir(parents=True, exist_ok=True)
    detail_path = out_dir / f"{stamp}_tier1_data_ok_detail.csv"
    summary_path = out_dir / f"{stamp}_tier1_data_ok_summary.csv"
    md_path = out_dir / f"{stamp}_tier1_data_ok_curation_memo.md"
    _write_detail_csv(records, detail_path)
    _write_summary_csv(records, summary_path)
    _write_markdown(records, md_path, detail_path, summary_path)
    return [detail_path, summary_path, md_path]


def _write_detail_csv(records: list[AuditRecord], path: Path) -> None:
    fieldnames = [
        "site_id", "name", "country_code", "latitude", "longitude", "smr_key",
        "criterion_id", "baseline_score", "baseline_quality_flag",
        "baseline_confidence", "candidate_score", "candidate_quality_flag",
        "candidate_band", "baseline_justification", "fields_json",
    ]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow({
                "site_id": r.site_id,
                "name": r.name,
                "country_code": r.country_code,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "smr_key": r.smr_key,
                "criterion_id": r.criterion_id,
                "baseline_score": r.baseline_score,
                "baseline_quality_flag": r.baseline_quality_flag,
                "baseline_confidence": r.baseline_confidence,
                "candidate_score": r.candidate_score,
                "candidate_quality_flag": r.candidate_quality_flag,
                "candidate_band": r.candidate_band,
                "baseline_justification": r.baseline_justification,
                "fields_json": json.dumps({k: _jsonable(v) for k, v in r.fields.items()}, sort_keys=True),
            })


def _write_summary_csv(records: list[AuditRecord], path: Path) -> None:
    rows: list[dict[str, Any]] = []
    for cid in CRITERIA:
        subset = [r for r in records if r.criterion_id == cid]
        rows.extend(_field_summary_rows(cid, subset))
        rows.extend(_count_rows(cid, "baseline_quality_flag", (r.baseline_quality_flag for r in subset)))
        rows.extend(_count_rows(cid, "candidate_quality_flag", (r.candidate_quality_flag for r in subset)))
        rows.extend(_count_rows(cid, "candidate_band", (r.candidate_band for r in subset)))
        rows.append({"criterion_id": cid, "metric": "candidate_score", **numeric_summary(r.candidate_score for r in subset)})
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _field_summary_rows(cid: str, records: list[AuditRecord]) -> list[dict[str, Any]]:
    rows = []
    for field in FIELD_MAP[cid]:
        values = [r.fields.get(field) for r in records]
        nulls = sum(v is None or v == "" for v in values)
        zeros = sum(v == 0 or v == 0.0 for v in values)
        row = {"criterion_id": cid, "metric": field, "rows": len(records), "nulls": nulls, "zeros": zeros}
        row.update(numeric_summary(values))
        rows.append(row)
    return rows


def _count_rows(cid: str, metric: str, values: Iterable[Any]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value if value not in (None, "") else "<null>")
        counts[key] = counts.get(key, 0) + 1
    return [
        {"criterion_id": cid, "metric": metric, "value": key, "count": count}
        for key, count in sorted(counts.items())
    ]


def _write_markdown(
    records: list[AuditRecord],
    path: Path,
    detail_path: Path,
    summary_path: Path,
) -> None:
    lines = [
        "<!-- man_hours: 1.0 -->",
        "# Tier 1 Data OK Curation Memo",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"Detail CSV: `{detail_path}`",
        f"Summary CSV: `{summary_path}`",
        "",
        "This is a read-only audit. It evaluates working-tree scoring logic in memory and does not write DB rows.",
    ]
    for cid in CRITERIA:
        subset = [r for r in records if r.criterion_id == cid]
        lines += ["", f"## {cid}", ""]
        lines += [f"- Rows reviewed: {len(subset)}"]
        for field in FIELD_MAP[cid]:
            stats = numeric_summary(r.fields.get(field) for r in subset)
            nulls = sum(r.fields.get(field) in (None, "") for r in subset)
            lines.append(
                f"- `{field}`: nulls {nulls}/{len(subset)}, "
                f"range {stats['min']} to {stats['max']}, stdev {stats['stdev']}"
            )
        cand = numeric_summary(r.candidate_score for r in subset)
        unscored = sum(r.candidate_quality_flag == "unscored" for r in subset)
        baseline_present = sum(r.baseline_score is not None for r in subset)
        lines.append(f"- Baseline ranking rows found: {baseline_present}/{len(subset)}")
        lines.append(
            f"- Candidate scores: unscored {unscored}/{len(subset)}, "
            f"stdev {cand['stdev']}, range {cand['min']} to {cand['max']}"
        )
        lines.append("- Field classification: see `experts/quality/data_science_siting_curator.md` curation format.")
    path.write_text("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--smr-key", default=DEFAULT_SMR_KEY)
    parser.add_argument("--rubric-dir", default="config/scoring_rubrics")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--stamp", default="20260517")
    args = parser.parse_args(argv)
    records = fetch_records(args.run_id, args.smr_key, args.rubric_dir)
    paths = write_outputs(records, args.out_dir, args.stamp)
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
