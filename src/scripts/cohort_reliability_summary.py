#!/usr/bin/env python
# man_hours: 0.9
"""Cohort-wide reliability signals for the chosen scoring runs.

Read-only. Compares the canonical anchor run, the feedback rerun, and
the latest run on:

- ranking_scores distribution by criterion family and unscored count;
- specific reviewer-targeted criteria (5.0 unscored count vs total);
- screening_verdicts exclusionary fail count per criterion, plus raw fail
  phase breakdown so legacy screening rows cannot be mistaken for exclusions;
- composite_rankings: per-country full-pass count and composite-score distribution.

Writes Markdown to ``audit/post_processing/scoring_conformity/cohort_reliability.md``
and a parallel JSON payload.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from sqlalchemy import create_engine, text as sa_text

from atoms_vs_ashes.config import Settings

OUT_DIR = PROJECT_ROOT / "audit/post_processing/scoring_conformity"

RUNS = [
    {"run_id": "score-214bab4e", "label": "canonical (May 2)"},
    {"run_id": "feedback_rerun_20260509", "label": "feedback rerun (May 9)"},
    {"run_id": "20260513T030738_70d5bc2c", "label": "latest (May 13)"},
]

REVIEWER_TARGETED = [
    # Per Ovidiu's comments
    "NH-03", "NH-04", "NH-05", "NH-07", "NH-08", "NH-09",
    "NH-11", "NH-13", "NH-14",
    "HI-01", "HI-02", "HI-04", "HI-05", "HI-06", "HI-08",
    "EP-01", "RI-04",
]


def _run(engine, sql: str, params: dict | None = None):
    with engine.connect() as conn:
        return conn.execute(sa_text(sql), params or {}).mappings().all()


def _safe_run(engine, sql: str, params: dict | None = None):
    try:
        return list(_run(engine, sql, params))
    except Exception as exc:
        return [{"_error": str(exc)}]


def _smr_filter() -> str:
    # Anchor / report narrative is nuscale_voygr6.
    return "nuscale_voygr6"


def per_criterion_distribution(engine, run_id: str) -> dict[str, Any]:
    """Per reviewer-targeted criterion: count of unscored vs scored, mean score."""
    rows = _safe_run(
        engine,
        """
        SELECT criterion_id,
               COUNT(*) AS rows,
               COUNT(*) FILTER (WHERE quality_flag = 'unscored') AS unscored_rows,
               COUNT(*) FILTER (WHERE score_0_10 = 5.0) AS at_default_5,
               COUNT(*) FILTER (WHERE score_0_10 >= 8.0) AS favorable_rows,
               COUNT(*) FILTER (WHERE score_0_10 >= 4.5 AND score_0_10 <= 6.5) AS mid_band_rows,
               ROUND(AVG(score_0_10)::numeric, 2) AS mean_score,
               ROUND(MIN(score_0_10)::numeric, 2) AS min_score,
               ROUND(MAX(score_0_10)::numeric, 2) AS max_score
        FROM ranking_scores
        WHERE run_id = :rid
          AND smr_key = :smr
          AND criterion_id = ANY(:cids)
        GROUP BY criterion_id
        ORDER BY criterion_id
        """,
        {"rid": run_id, "smr": _smr_filter(), "cids": REVIEWER_TARGETED},
    )
    if rows and "_error" in rows[0]:
        return {"error": rows[0]["_error"]}
    out: list[dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "criterion_id": r["criterion_id"],
                "rows": int(r["rows"]),
                "unscored": int(r["unscored_rows"]),
                "at_default_5": int(r["at_default_5"]),
                "favorable": int(r["favorable_rows"]),
                "mid_band": int(r["mid_band_rows"]),
                "mean_score": float(r["mean_score"]) if r["mean_score"] is not None else None,
                "min_score": float(r["min_score"]) if r["min_score"] is not None else None,
                "max_score": float(r["max_score"]) if r["max_score"] is not None else None,
            }
        )
    return {"rows": out}


def composite_distribution(engine, run_id: str) -> dict[str, Any]:
    """Composite score distribution for the run (baseline weight profile)."""
    rows = _safe_run(
        engine,
        """
        SELECT COUNT(*) AS rows,
               COUNT(*) FILTER (WHERE composite_score IS NULL) AS null_composite,
               COUNT(*) FILTER (WHERE passed_exclusionary AND passed_avoidance) AS full_pass,
               COUNT(*) FILTER (WHERE NOT passed_exclusionary) AS failed_exclusionary,
               COUNT(*) FILTER (WHERE passed_exclusionary AND NOT passed_avoidance) AS failed_avoidance_only,
               ROUND(AVG(composite_score)::numeric, 2) AS mean_composite,
               ROUND(MIN(composite_score)::numeric, 2) AS min_composite,
               ROUND(MAX(composite_score)::numeric, 2) AS max_composite,
               ROUND(percentile_cont(0.25) WITHIN GROUP (ORDER BY composite_score)::numeric, 2) AS p25,
               ROUND(percentile_cont(0.50) WITHIN GROUP (ORDER BY composite_score)::numeric, 2) AS p50,
               ROUND(percentile_cont(0.75) WITHIN GROUP (ORDER BY composite_score)::numeric, 2) AS p75
        FROM composite_rankings
        WHERE run_id = :rid
          AND weight_profile = 'baseline'
          AND smr_key = :smr
        """,
        {"rid": run_id, "smr": _smr_filter()},
    )
    if rows and "_error" in rows[0]:
        return {"error": rows[0]["_error"]}
    if not rows:
        return {"rows": 0}
    r = rows[0]
    return {
        "rows": int(r["rows"]),
        "null_composite": int(r["null_composite"]),
        "full_pass": int(r["full_pass"]),
        "failed_exclusionary": int(r["failed_exclusionary"]),
        "failed_avoidance_only": int(r["failed_avoidance_only"]),
        "mean_composite": float(r["mean_composite"]) if r["mean_composite"] is not None else None,
        "min_composite": float(r["min_composite"]) if r["min_composite"] is not None else None,
        "max_composite": float(r["max_composite"]) if r["max_composite"] is not None else None,
        "p25": float(r["p25"]) if r["p25"] is not None else None,
        "p50": float(r["p50"]) if r["p50"] is not None else None,
        "p75": float(r["p75"]) if r["p75"] is not None else None,
    }


def per_country_full_pass(engine, run_id: str) -> list[dict[str, Any]]:
    rows = _safe_run(
        engine,
        """
        SELECT s.country_code,
               COUNT(*) AS sites_total,
               COUNT(*) FILTER (WHERE c.passed_exclusionary AND c.passed_avoidance) AS full_pass
        FROM composite_rankings c
        JOIN sites s USING (site_id)
        WHERE c.run_id = :rid
          AND c.weight_profile = 'baseline'
          AND c.smr_key = :smr
        GROUP BY s.country_code
        ORDER BY s.country_code
        """,
        {"rid": run_id, "smr": _smr_filter()},
    )
    if rows and "_error" in rows[0]:
        return [{"error": rows[0]["_error"]}]
    return [
        {
            "country_code": r["country_code"],
            "sites_total": int(r["sites_total"]),
            "full_pass": int(r["full_pass"]),
        }
        for r in rows
    ]


def fail_code_breakdown(engine, run_id: str) -> list[dict[str, Any]]:
    """Exclusionary fail counts only; other fail phases are reported separately."""
    rows = _safe_run(
        engine,
        """
        SELECT criterion_id,
               COUNT(*) AS fail_rows,
               COUNT(DISTINCT site_id) AS distinct_sites
        FROM screening_verdicts
        WHERE run_id = :rid
          AND smr_key = :smr
          AND verdict = 'fail'
          AND phase = 'exclusionary'
        GROUP BY criterion_id
        ORDER BY COUNT(*) DESC
        LIMIT 25
        """,
        {"rid": run_id, "smr": _smr_filter()},
    )
    if rows and "_error" in rows[0]:
        return [{"error": rows[0]["_error"]}]
    return [
        {
            "criterion_id": r["criterion_id"],
            "fail_rows": int(r["fail_rows"]),
            "distinct_sites": int(r["distinct_sites"]),
        }
        for r in rows
    ]


def fail_phase_breakdown(engine, run_id: str) -> list[dict[str, Any]]:
    rows = _safe_run(
        engine,
        """
        SELECT phase, prompt_key,
               COUNT(*) AS fail_rows,
               COUNT(DISTINCT site_id) AS distinct_sites
        FROM screening_verdicts
        WHERE run_id = :rid
          AND smr_key = :smr
          AND verdict = 'fail'
        GROUP BY phase, prompt_key
        ORDER BY COUNT(*) DESC
        LIMIT 25
        """,
        {"rid": run_id, "smr": _smr_filter()},
    )
    if rows and "_error" in rows[0]:
        return [{"error": rows[0]["_error"]}]
    return [
        {
            "phase": r["phase"],
            "prompt_key": r["prompt_key"],
            "fail_rows": int(r["fail_rows"]),
            "distinct_sites": int(r["distinct_sites"]),
        }
        for r in rows
    ]


def main() -> int:
    engine = create_engine(Settings().database.url, pool_pre_ping=True)

    payload: dict[str, Any] = {"runs": [], "smr_filter": _smr_filter()}

    for run in RUNS:
        rid = run["run_id"]
        run_block: dict[str, Any] = {"run_id": rid, "label": run["label"]}
        run_block["per_criterion"] = per_criterion_distribution(engine, rid)
        run_block["composite"] = composite_distribution(engine, rid)
        run_block["per_country_full_pass"] = per_country_full_pass(engine, rid)
        run_block["fail_by_criterion"] = fail_code_breakdown(engine, rid)
        run_block["fail_by_phase"] = fail_phase_breakdown(engine, rid)
        payload["runs"].append(run_block)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "cohort_reliability.json"
    md_path = OUT_DIR / "cohort_reliability.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Render Markdown
    lines: list[str] = ["<!-- man_hours: 0.0 -->"]
    lines.append("# Cohort reliability signals")
    lines.append("")
    lines.append(
        f"All figures filtered to `smr_key = {_smr_filter()}` (matches the report narrative single-SMR baseline). "
        "Generated by `src/scripts/cohort_reliability_summary.py`. No scoring or sensitivity job was triggered."
    )
    lines.append("")

    for run in payload["runs"]:
        rid = run["run_id"]
        label = run["label"]
        lines.append(f"## Run `{rid}` — {label}")
        lines.append("")

        # Composite block
        comp = run["composite"]
        lines.append("### Composite distribution (baseline weight profile)")
        lines.append("")
        if "error" in comp:
            lines.append(f"_Not available: {comp['error']}_")
        else:
            lines.append(
                f"- rows: **{comp['rows']}** sites; full pass: **{comp['full_pass']}**; "
                f"failed exclusionary: **{comp['failed_exclusionary']}**; "
                f"failed avoidance only: **{comp['failed_avoidance_only']}**."
            )
            lines.append(
                f"- composite mean: **{comp['mean_composite']}**, "
                f"p25 / p50 / p75: **{comp['p25']} / {comp['p50']} / {comp['p75']}**, "
                f"min / max: **{comp['min_composite']} / {comp['max_composite']}**."
            )
        lines.append("")

        # Per-country full pass
        per_country = run["per_country_full_pass"]
        lines.append("### Per-country full-pass count (composite baseline)")
        lines.append("")
        if per_country and "error" in per_country[0]:
            lines.append(f"_Not available: {per_country[0]['error']}_")
        else:
            lines.append("| country | sites | full pass |")
            lines.append("| --- | ---: | ---: |")
            for row in per_country:
                lines.append(f"| {row['country_code']} | {row['sites_total']} | {row['full_pass']} |")
        lines.append("")

        # Per criterion
        pc = run["per_criterion"]
        lines.append("### Reviewer-targeted criteria — distribution")
        lines.append("")
        if "error" in pc:
            lines.append(f"_Not available: {pc['error']}_")
        else:
            lines.append("| criterion | rows | unscored | =5.0 | favorable (>=8) | mid (4.5-6.5) | mean | min | max |")
            lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
            for row in pc["rows"]:
                lines.append(
                    f"| {row['criterion_id']} | {row['rows']} | {row['unscored']} | "
                    f"{row['at_default_5']} | {row['favorable']} | {row['mid_band']} | "
                    f"{row['mean_score']} | {row['min_score']} | {row['max_score']} |"
                )
        lines.append("")

        # Fail breakdown
        fc = run["fail_by_criterion"]
        lines.append("### Top exclusionary fail-contributing criteria")
        lines.append("")
        if fc and "error" in fc[0]:
            lines.append(f"_Not available: {fc[0]['error']}_")
        else:
            lines.append("| criterion | fail rows | distinct sites |")
            lines.append("| --- | ---: | ---: |")
            for row in fc:
                lines.append(f"| {row['criterion_id']} | {row['fail_rows']} | {row['distinct_sites']} |")
        lines.append("")

        fp = run["fail_by_phase"]
        lines.append("### Raw fail prompts by phase (legacy screening rows separated)")
        lines.append("")
        if fp and "error" in fp[0]:
            lines.append(f"_Not available: {fp[0]['error']}_")
        else:
            lines.append("| phase | prompt_key | fail rows | distinct sites |")
            lines.append("| --- | --- | ---: | ---: |")
            for row in fp:
                lines.append(
                    f"| {row['phase']} | `{row['prompt_key'] or '-'}` | "
                    f"{row['fail_rows']} | {row['distinct_sites']} |"
                )
        lines.append("")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
