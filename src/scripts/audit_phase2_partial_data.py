# man_hours: 7.2
"""Read-only distribution audit for Tier 2 Phase 2 partial-data scoring.

Evaluates working-tree band logic in memory for EP-03, HI-02/03/04, NH-09/11,
RI-03, and RI-05. Never modifies the database.
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
    SiteEmergencyPlanning,
    SiteHumanHazards,
    SiteNaturalHazards,
    SiteRadiological,
)
from atoms_vs_ashes.scoring.bands import evaluate_criterion_value
from atoms_vs_ashes.scoring.merge_context_derivations import apply_derived_context_values
from atoms_vs_ashes.scoring.rubric import load_rubric_bundle

DEFAULT_RUN_ID = "20260517T104618_459ae424"
DEFAULT_SMR_KEY = "nuscale_voygr6"
DEFAULT_OUT_DIR = Path("audit/post_processing/06_scoring")
CRITERIA = ("EP-03", "HI-02", "HI-03", "HI-04", "NH-09", "NH-11", "RI-03", "RI-05")

FIELD_MAP: dict[str, tuple[str, ...]] = {
    "EP-03": (
        "relief_m_per_10km",
        "ep03_gee_relief_16km_m",
        "major_river_barrier",
        "waterway_count_epz",
        "ep03_quality",
        "emergency_run_id",
        "emergency_fetched_at",
    ),
    "HI-02": (
        "nearest_seveso_km",
        "nearest_ied_km",
        "hi02_quality",
        "hi02_search_completed",
        "human_run_id",
        "human_fetched_at",
    ),
    "HI-03": (
        "nearest_toxic_source_km",
        "toxic_source_type",
        "hi03_quality",
        "hi03_search_completed",
        "human_run_id",
        "human_fetched_at",
    ),
    "HI-04": (
        "nearest_flammable_storage_km",
        "nearest_pipeline_km",
        "hi04_quality",
        "hi04_search_completed",
        "human_run_id",
        "human_fetched_at",
    ),
    "NH-09": (
        "river_distance_km",
        "nearest_river_km",
        "flood_zone_class_500yr",
        "flood_zone_class",
        "elevation_above_design_flood_m",
        "natural_run_id",
        "natural_fetched_at",
    ),
    "NH-11": (
        "spi12_min",
        "snow_months_per_year",
        "mean_annual_precip_mm",
        "mean_annual_precip_corrected_mm",
        "extreme_precip_mm",
        "extreme_precip_corrected_mm",
        "freezing_days_per_year",
        "natural_run_id",
        "natural_fetched_at",
    ),
    "RI-03": (
        "aquifer_type",
        "ri03_aquifer_screening_class",
        "groundwater_vulnerability_class",
        "ri03_quality",
        "radiological_run_id",
        "radiological_fetched_at",
    ),
    "RI-05": (
        "nearest_city_50k_km",
        "nearest_city_pop",
        "pop_density_16km",
        "pop_total_16km",
        "ri05_required_distance_km",
        "ri05_distance_margin_pct",
        "radiological_run_id",
        "radiological_fetched_at",
    ),
}

QUALITY_FIELD: dict[str, str | None] = {
    "EP-03": "ep03_quality",
    "HI-02": "hi02_quality",
    "HI-03": "hi03_quality",
    "HI-04": "hi04_quality",
    "NH-09": None,
    "NH-11": None,
    "RI-03": "ri03_quality",
    "RI-05": None,
}

COVERAGE_VERDICT: dict[str, str] = {
    "EP-03": "scoreable_with_derivation",
    "HI-02": "scoreable_with_sentinel",
    "HI-03": "scoreable_with_sentinel",
    "HI-04": "scoreable_with_sentinel",
    "NH-09": "scoreable_with_derivation",
    "NH-11": "scoreable_with_partial_metrics",
    "RI-03": "scoreable_with_derivation",
    "RI-05": "scoreable_with_derivation",
}

REMEDIATION_CLASS: dict[str, str] = {
    "EP-03": "B",
    "HI-02": "A",
    "HI-03": "A",
    "HI-04": "A",
    "NH-09": "A",
    "NH-11": "B",
    "RI-03": "A",
    "RI-05": "B",
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
    context = dict(fields)
    apply_derived_context_values(context)
    return context


def _fields_with_selected_derivations(criterion_id: str, fields: dict[str, Any]) -> dict[str, Any]:
    """Add derived audit fields without overwriting measured raw DB fields."""
    context = _criterion_context(criterion_id, fields)
    out = dict(fields)
    for field in FIELD_MAP[criterion_id]:
        if field not in out and field in context:
            out[field] = context[field]
    return out


def candidate_result(
    criterion_id: str,
    fields: dict[str, Any],
    bundle: dict[str, Any],
) -> tuple[float, str, str]:
    criterion = bundle[criterion_id]
    context = _criterion_context(criterion_id, fields)
    quality_key = QUALITY_FIELD.get(criterion_id)
    result = evaluate_criterion_value(
        criterion,
        context,
        quality=fields.get(quality_key) if quality_key else None,
    )
    quality_flag = "unscored" if result.notes and "unscored" in result.notes else "scored"
    band = result.matched_band.descriptor if result.matched_band else result.descriptor
    return float(result.score), quality_flag, band


def fetch_records(run_id: str, smr_key: str, rubric_dir: str) -> list[AuditRecord]:
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
                select(
                    Site,
                    SiteHumanHazards,
                    SiteNaturalHazards,
                    SiteEmergencyPlanning,
                    SiteRadiological,
                    RankingScore,
                )
                .outerjoin(SiteHumanHazards, SiteHumanHazards.site_id == Site.site_id)
                .outerjoin(SiteNaturalHazards, SiteNaturalHazards.site_id == Site.site_id)
                .outerjoin(SiteEmergencyPlanning, SiteEmergencyPlanning.site_id == Site.site_id)
                .outerjoin(SiteRadiological, SiteRadiological.site_id == Site.site_id)
                .outerjoin(RankingScore, score_join)
                .order_by(Site.country_code, Site.name)
            )
            for site, human, natural, emergency, radiological, score in session.execute(stmt).all():
                raw_fields = _fields_for(criterion_id, human, natural, emergency, radiological)
                fields = _fields_with_selected_derivations(criterion_id, raw_fields)
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
    emergency: SiteEmergencyPlanning | None,
    radiological: SiteRadiological | None,
) -> dict[str, Any]:
    if criterion_id == "EP-03":
        return {
            "relief_m_per_10km": None,
            "ep03_gee_relief_16km_m": _to_float(
                getattr(emergency, "ep03_gee_relief_16km_m", None),
            ),
            "major_river_barrier": getattr(emergency, "major_river_barrier", None),
            "waterway_count_epz": getattr(emergency, "waterway_count_epz", None),
            "ep03_quality": getattr(emergency, "ep03_quality", None),
            "emergency_run_id": getattr(emergency, "run_id", None),
            "emergency_fetched_at": getattr(emergency, "fetched_at", None),
        }
    if criterion_id in {"HI-02", "HI-03", "HI-04"}:
        base = {
            "human_run_id": getattr(human, "run_id", None),
            "human_fetched_at": getattr(human, "fetched_at", None),
        }
        if criterion_id == "HI-02":
            base.update({
                "nearest_seveso_km": _to_float(getattr(human, "nearest_seveso_km", None)),
                "nearest_ied_km": _to_float(getattr(human, "nearest_ied_km", None)),
                "hi02_quality": getattr(human, "hi02_quality", None),
            })
        elif criterion_id == "HI-03":
            base.update({
                "nearest_toxic_source_km": _to_float(
                    getattr(human, "nearest_toxic_source_km", None),
                ),
                "toxic_source_type": getattr(human, "toxic_source_type", None),
                "hi03_quality": getattr(human, "hi03_quality", None),
            })
        else:
            base.update({
                "nearest_flammable_storage_km": _to_float(
                    getattr(human, "nearest_flammable_storage_km", None),
                ),
                "nearest_pipeline_km": _to_float(getattr(human, "nearest_pipeline_km", None)),
                "hi04_quality": getattr(human, "hi04_quality", None),
            })
        return base
    if criterion_id == "NH-09":
        return {
            "river_distance_km": _to_float(getattr(natural, "river_distance_km", None)),
            "nearest_river_km": _to_float(getattr(natural, "nearest_river_km", None)),
            "flood_zone_class_500yr": getattr(natural, "flood_zone_class_500yr", None)
            or getattr(natural, "flood_zone_class", None),
            "flood_zone_class": getattr(natural, "flood_zone_class", None),
            "elevation_above_design_flood_m": _to_float(
                getattr(natural, "elevation_above_design_flood_m", None),
            ),
            "natural_run_id": getattr(natural, "run_id", None),
            "natural_fetched_at": getattr(natural, "fetched_at", None),
        }
    if criterion_id == "NH-11":
        return {
            "spi12_min": _to_float(getattr(natural, "spi12_min", None)),
            "snow_months_per_year": _to_float(getattr(natural, "snow_months_per_year", None)),
            "mean_annual_precip_mm": _to_float(getattr(natural, "mean_annual_precip_mm", None)),
            "extreme_precip_mm": _to_float(getattr(natural, "extreme_precip_mm", None)),
            "freezing_days_per_year": _to_float(
                getattr(natural, "freezing_days_per_year", None),
            ),
            "natural_run_id": getattr(natural, "run_id", None),
            "natural_fetched_at": getattr(natural, "fetched_at", None),
        }
    if criterion_id == "RI-03":
        return {
            "aquifer_type": getattr(radiological, "aquifer_type", None),
            "groundwater_vulnerability_class": getattr(
                radiological, "groundwater_vulnerability_class", None,
            ),
            "ri03_quality": getattr(radiological, "ri03_quality", None),
            "radiological_run_id": getattr(radiological, "run_id", None),
            "radiological_fetched_at": getattr(radiological, "fetched_at", None),
        }
    return {
        "nearest_city_50k_km": _to_float(getattr(radiological, "nearest_city_50k_km", None)),
        "nearest_city_pop": _to_float(getattr(radiological, "nearest_city_pop", None)),
        "pop_density_16km": _to_float(getattr(radiological, "pop_density_16km", None)),
        "pop_total_16km": getattr(radiological, "pop_total_16km", None),
        "radiological_run_id": getattr(radiological, "run_id", None),
        "radiological_fetched_at": getattr(radiological, "fetched_at", None),
    }


def numeric_summary(values: Iterable[Any]) -> dict[str, float | int | None]:
    nums = sorted(v for v in (_to_float(v) for v in values) if v is not None)
    if not nums:
        return {
            "count": 0, "min": None, "p05": None, "p25": None, "median": None,
            "p75": None, "p95": None, "max": None, "mean": None, "stdev": None,
        }
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


def write_coverage_report(
    records: list[AuditRecord],
    path: Path,
    *,
    run_id: str,
    smr_key: str,
) -> None:
    lines = [
        "<!-- man_hours: 1.5 -->",
        "# Phase 2 Partial Data Coverage Report",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"Baseline run: `{run_id}` · SMR: `{smr_key}`",
        "",
        "Read-only cohort fill for Bucket C criteria. Verdicts gate band work per",
        "`criteria/tier2_partial_data_parallel_workflows.md`.",
        "",
    ]
    for cid in CRITERIA:
        subset = [r for r in records if r.criterion_id == cid]
        n = len(subset)
        lines += [f"## {cid}", ""]
        if n == 0:
            lines.append("- **No site rows** (local DB unavailable or empty).")
            lines.append(
                "- Seed fill rates from "
                "`audit/post_processing/06_scoring/20260517_criteria_db_fields_and_site_samples.md`."
            )
            lines += [
                "",
                f"- **Verdict:** `{COVERAGE_VERDICT[cid]}`",
                f"- **Remediation class:** `{REMEDIATION_CLASS[cid]}`",
                "",
            ]
            continue
        lines.append(f"- Cohort rows: **{n}**")
        for field in FIELD_MAP[cid]:
            nulls = sum(r.fields.get(field) in (None, "") for r in subset)
            fill = round(100.0 * (n - nulls) / n, 1)
            lines.append(f"- `{field}`: {fill}% fill ({n - nulls}/{n})")
        qf = QUALITY_FIELD.get(cid)
        if qf:
            counts: dict[str, int] = {}
            for r in subset:
                key = str(r.fields.get(qf) or "<null>")
                counts[key] = counts.get(key, 0) + 1
            top = sorted(counts.items(), key=lambda x: -x[1])[:6]
            lines.append(f"- `{qf}` distribution: " + ", ".join(f"{k}={v}" for k, v in top))
        cand = numeric_summary(r.candidate_score for r in subset)
        unscored = sum(r.candidate_quality_flag == "unscored" for r in subset)
        lines += [
            f"- Candidate unscored: **{unscored}/{n}** ({round(100 * unscored / n, 1)}%)",
            f"- Candidate score stdev: **{cand['stdev']}**",
            f"- **Verdict:** `{COVERAGE_VERDICT[cid]}`",
            f"- **Remediation class:** `{REMEDIATION_CLASS[cid]}`",
            "",
        ]
    path.write_text("\n".join(lines) + "\n")


def write_outputs(
    records: list[AuditRecord],
    out_dir: Path,
    stamp: str,
    *,
    run_id: str,
    smr_key: str,
    coverage_only: bool = False,
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    coverage_path = out_dir / f"{stamp}_phase2_data_coverage_report.md"
    write_coverage_report(records, coverage_path, run_id=run_id, smr_key=smr_key)
    paths.append(coverage_path)
    if coverage_only:
        for cid in CRITERIA:
            stub = out_dir / f"phase2_track_{cid}_curation_memo.md"
            _write_track_memo_stub(records, cid, stub, coverage_path)
            paths.append(stub)
        return paths

    detail_path = out_dir / f"{stamp}_phase2_partial_data_detail.csv"
    summary_path = out_dir / f"{stamp}_phase2_partial_data_summary.csv"
    memo_path = out_dir / f"{stamp}_phase2_partial_data_curation_memo.md"
    examples_path = out_dir / f"{stamp}_phase2_scored_site_examples.md"
    _write_detail_csv(records, detail_path)
    _write_summary_csv(records, summary_path)
    _write_markdown(records, memo_path, detail_path, summary_path, coverage_path)
    _write_scored_site_examples(records, examples_path, detail_path, summary_path)
    paths.extend([detail_path, summary_path, memo_path, examples_path])
    for cid in CRITERIA:
        track_path = out_dir / f"phase2_track_{cid}_curation_memo.md"
        _write_track_memo(records, cid, track_path, coverage_path)
        paths.append(track_path)
    return paths


def _write_track_memo_stub(
    records: list[AuditRecord],
    cid: str,
    path: Path,
    coverage_path: Path,
) -> None:
    path.write_text(
        "\n".join([
            f"<!-- man_hours: 0.5 -->",
            f"# Phase 2 Track — {cid}",
            "",
            f"Coverage source: `{coverage_path.name}`",
            "",
            "## Data coverage",
            "",
            f"See coverage report row for **{cid}**.",
            "",
            f"- **Verdict:** {COVERAGE_VERDICT[cid]}",
            f"- **Remediation class:** {REMEDIATION_CLASS[cid]}",
            "",
            "## Remediation decision",
            "",
            "Class A/B in-repo scoring only. **STOP_DB_WRITE** / **STOP_LIVE_API** for backfill/rescore.",
            "",
            "## Acceptance",
            "",
            "- Decision: Accept with conditions (pending consent-gated rescore)",
            "",
        ]) + "\n",
    )


def _write_track_memo(
    records: list[AuditRecord],
    cid: str,
    path: Path,
    coverage_path: Path,
) -> None:
    subset = [r for r in records if r.criterion_id == cid]
    n = len(subset)
    unscored = sum(r.candidate_quality_flag == "unscored" for r in subset)
    cand = numeric_summary(r.candidate_score for r in subset)
    lines = [
        f"<!-- man_hours: 0.5 -->",
        f"# Phase 2 Track — {cid}",
        "",
        f"Coverage source: `{coverage_path.name}`",
        "",
        "## Data coverage",
        "",
        f"- Cohort rows: {n}",
        f"- Candidate unscored: {unscored}/{n}",
        f"- Candidate stdev: {cand['stdev']}",
        f"- **Verdict:** {COVERAGE_VERDICT[cid]}",
        "",
        "## Remediation decision",
        "",
        f"Primary path: Class **{REMEDIATION_CLASS[cid]}** (context alias / alternate column / partial metrics).",
        "STOP_DB_WRITE for LLM backfill or rescore. STOP_LIVE_API for connector top-up.",
        "",
        "## Acceptance",
        "",
        "- Decision: Accept with conditions",
        "- Conditions: consent-gated score run for before/after DB comparison",
        "",
    ]
    path.write_text("\n".join(lines) + "\n")


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
            ctx = _criterion_context(r.criterion_id, dict(r.fields))
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
                "fields_json": json.dumps({k: _jsonable(ctx.get(k, v)) for k, v in r.fields.items()}, sort_keys=True),
            })


def _write_summary_csv(records: list[AuditRecord], path: Path) -> None:
    rows: list[dict[str, Any]] = []
    for cid in CRITERIA:
        subset = [r for r in records if r.criterion_id == cid]
        rows.extend(_field_summary_rows(cid, subset))
        rows.extend(_count_rows(cid, "baseline_quality_flag", (r.baseline_quality_flag for r in subset)))
        rows.extend(_count_rows(cid, "candidate_quality_flag", (r.candidate_quality_flag for r in subset)))
        rows.extend(_count_rows(cid, "candidate_band", (r.candidate_band for r in subset)))
        rows.append({
            "criterion_id": cid,
            "metric": "candidate_score",
            **numeric_summary(r.candidate_score for r in subset),
        })
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
    coverage_path: Path,
) -> None:
    lines = [
        "<!-- man_hours: 1.0 -->",
        "# Phase 2 Partial Data Curation Memo",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"Coverage: `{coverage_path}`",
        f"Detail CSV: `{detail_path}`",
        f"Summary CSV: `{summary_path}`",
        "",
        "Read-only audit of working-tree scoring logic; no DB writes.",
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
        lines.append(
            f"- Candidate scores: unscored {unscored}/{len(subset)}, "
            f"stdev {cand['stdev']}, range {cand['min']} to {cand['max']}"
        )
        lines.append(f"- Verdict: {COVERAGE_VERDICT[cid]} · class {REMEDIATION_CLASS[cid]}")
    path.write_text("\n".join(lines) + "\n")


def _write_scored_site_examples(
    records: list[AuditRecord],
    path: Path,
    detail_path: Path,
    summary_path: Path,
) -> None:
    lines = [
        "<!-- man_hours: 1.2 -->",
        "# Phase 2 Scored Site Examples",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"Detail CSV: `{detail_path}`",
        f"Summary CSV: `{summary_path}`",
        "",
        "Examples are from read-only in-memory evaluation of working-tree scoring logic.",
        "They are not persisted `ranking_scores` rows; DB-writing rescore remains consent-gated.",
        "",
    ]
    for cid in CRITERIA:
        subset = [r for r in records if r.criterion_id == cid]
        examples = _representative_examples(subset)
        lines += [f"## {cid}", ""]
        if not examples:
            lines += ["No local examples available.", ""]
            continue
        lines += [
            "| Example | Country | Site | Candidate score | Quality | Matched band | Key fields |",
            "| --- | --- | --- | ---: | --- | --- | --- |",
        ]
        for label, record in examples:
            fields = _format_key_fields(record)
            band = str(record.candidate_band or "").replace("|", "\\|")
            lines.append(
                f"| {label} | {record.country_code} | {record.name} | "
                f"{record.candidate_score} | {record.candidate_quality_flag} | "
                f"{band} | {fields} |"
            )
        lines.append("")
    path.write_text("\n".join(lines) + "\n")


def _representative_examples(records: list[AuditRecord]) -> list[tuple[str, AuditRecord]]:
    scored = sorted(
        (r for r in records if r.candidate_quality_flag != "unscored" and r.candidate_score is not None),
        key=lambda r: (float(r.candidate_score or 0), r.country_code, r.name),
    )
    unscored = sorted(
        (r for r in records if r.candidate_quality_flag == "unscored"),
        key=lambda r: (r.country_code, r.name),
    )
    picks: list[tuple[str, AuditRecord]] = []
    if scored:
        picks.append(("low scored", scored[0]))
        picks.append(("median scored", scored[len(scored) // 2]))
        picks.append(("high scored", scored[-1]))
    if unscored:
        picks.append(("unscored caveat", unscored[0]))

    deduped: list[tuple[str, AuditRecord]] = []
    seen: set[tuple[str, str]] = set()
    for label, record in picks:
        key = (record.site_id, str(record.candidate_score))
        if key not in seen:
            deduped.append((label, record))
            seen.add(key)
    return deduped


def _format_key_fields(record: AuditRecord) -> str:
    keys = FIELD_MAP[record.criterion_id]
    parts: list[str] = []
    for key in keys:
        value = record.fields.get(key)
        if value in (None, ""):
            continue
        if isinstance(value, float):
            value = round(value, 3)
        parts.append(f"`{key}`={value}")
        if len(parts) >= 5:
            break
    return "<br>".join(parts) if parts else "no populated key fields"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--smr-key", default=DEFAULT_SMR_KEY)
    parser.add_argument("--rubric-dir", default="config/scoring_rubrics")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--stamp", default="20260517")
    parser.add_argument(
        "--coverage-only",
        action="store_true",
        help="Emit coverage report and per-track memo stubs only.",
    )
    args = parser.parse_args(argv)
    try:
        records = fetch_records(args.run_id, args.smr_key, args.rubric_dir)
    except Exception as exc:
        print(f"DB read failed ({exc}); writing coverage stubs from static verdicts.")
        records = []
    paths = write_outputs(
        records,
        args.out_dir,
        args.stamp,
        run_id=args.run_id,
        smr_key=args.smr_key,
        coverage_only=args.coverage_only,
    )
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
