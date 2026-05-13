#!/usr/bin/env python
# man_hours: 0.5
"""Read-only inventory of persisted scoring runs in the local project DB.

Lists every distinct ``run_id`` present in ``ranking_scores``,
``composite_rankings``, and ``screening_verdicts`` with row counts,
distinct site count, distinct SMR count, and the first / last
``scored_at`` timestamp where available. The result is written to
``audit/post_processing/scoring_conformity/run_inventory.json`` and a
human-readable Markdown summary.

This script does not initiate any scoring or sensitivity run. It only
issues SELECT statements.
"""

from __future__ import annotations

import json
import sys
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


def _safe_select(engine, sql: str, mapper) -> list[dict[str, Any]] | list[dict[str, str]]:
    """Run *sql* in its own short-lived transaction; return rows or one {error: ...}."""
    try:
        with engine.connect() as conn:
            rows = conn.execute(sa_text(sql)).mappings().all()
    except Exception as exc:
        return [{"error": str(exc)}]
    return [mapper(r) for r in rows]


def _ranking_mapper(r) -> dict[str, Any]:
    return {
        "run_id": r["run_id"],
        "rows": int(r["rows"]),
        "distinct_sites": int(r["distinct_sites"]),
        "distinct_smrs": int(r["distinct_smrs"]),
        "first_scored_at": r["first_scored_at"].isoformat() if r["first_scored_at"] else None,
        "last_scored_at": r["last_scored_at"].isoformat() if r["last_scored_at"] else None,
    }


def _composite_mapper(r) -> dict[str, Any]:
    return {
        "run_id": r["run_id"],
        "rows": int(r["rows"]),
        "distinct_sites": int(r["distinct_sites"]),
        "distinct_smrs": int(r["distinct_smrs"]),
        "weight_profiles": r["weight_profiles"],
        "first_ranked_at": r["first_ranked_at"].isoformat() if r["first_ranked_at"] else None,
        "last_ranked_at": r["last_ranked_at"].isoformat() if r["last_ranked_at"] else None,
    }


def _verdict_mapper(r) -> dict[str, Any]:
    return {
        "run_id": r["run_id"],
        "rows": int(r["rows"]),
        "distinct_sites": int(r["distinct_sites"]),
        "distinct_smrs": int(r["distinct_smrs"]),
        "fail_rows": int(r["fail_rows"]),
        "first_screened_at": r["first_screened_at"].isoformat() if r["first_screened_at"] else None,
        "last_screened_at": r["last_screened_at"].isoformat() if r["last_screened_at"] else None,
    }


def _snapshot_mapper(r) -> dict[str, Any]:
    return {
        "run_id": r["run_id"],
        "snapshot_id": r.get("snapshot_id"),
        "created_at": r["created_at"].isoformat() if r["created_at"] else None,
    }


def main() -> int:
    engine = create_engine(Settings().database.url, pool_pre_ping=True)

    ranking = _safe_select(
        engine,
        """
        SELECT run_id,
               COUNT(*) AS rows,
               COUNT(DISTINCT site_id) AS distinct_sites,
               COUNT(DISTINCT smr_key) AS distinct_smrs,
               MIN(scored_at) AS first_scored_at,
               MAX(scored_at) AS last_scored_at
        FROM ranking_scores
        GROUP BY run_id
        ORDER BY MAX(scored_at) DESC NULLS LAST, run_id
        """,
        _ranking_mapper,
    )
    composite = _safe_select(
        engine,
        """
        SELECT run_id,
               COUNT(*) AS rows,
               COUNT(DISTINCT site_id) AS distinct_sites,
               COUNT(DISTINCT smr_key) AS distinct_smrs,
               string_agg(DISTINCT weight_profile, ',' ORDER BY weight_profile) AS weight_profiles,
               MIN(ranked_at) AS first_ranked_at,
               MAX(ranked_at) AS last_ranked_at
        FROM composite_rankings
        GROUP BY run_id
        ORDER BY MAX(ranked_at) DESC NULLS LAST, run_id
        """,
        _composite_mapper,
    )
    verdicts = _safe_select(
        engine,
        """
        SELECT run_id,
               COUNT(*) AS rows,
               COUNT(DISTINCT site_id) AS distinct_sites,
               COUNT(DISTINCT smr_key) AS distinct_smrs,
               COUNT(*) FILTER (WHERE verdict = 'fail') AS fail_rows,
               MIN(screened_at) AS first_screened_at,
               MAX(screened_at) AS last_screened_at
        FROM screening_verdicts
        GROUP BY run_id
        ORDER BY MAX(screened_at) DESC NULLS LAST, run_id
        """,
        _verdict_mapper,
    )
    snapshot_rows = _safe_select(
        engine,
        """
        SELECT run_id, snapshot_id, created_at
        FROM scoring_run_snapshots
        ORDER BY created_at DESC
        LIMIT 100
        """,
        _snapshot_mapper,
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "run_inventory.json"
    md_path = OUT_DIR / "run_inventory.md"

    payload = {
        "ranking_scores": ranking,
        "composite_rankings": composite,
        "screening_verdicts": verdicts,
        "scoring_run_snapshots": snapshot_rows,
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines: list[str] = ["<!-- man_hours: 0.0 -->"]
    lines.append("# Local scoring run inventory")
    lines.append("")
    lines.append(
        "Read-only inventory of ``ranking_scores`` / ``composite_rankings`` / "
        "``screening_verdicts`` / ``scoring_run_snapshots``. Generated by "
        "``src/scripts/inventory_scoring_runs.py``. No scoring or sensitivity job was triggered."
    )
    lines.append("")
    lines.append("## ranking_scores")
    lines.append("")
    lines.append("| run_id | rows | sites | SMRs | first_scored_at | last_scored_at |")
    lines.append("| --- | ---: | ---: | ---: | --- | --- |")
    for row in ranking:
        lines.append(
            f"| `{row['run_id']}` | {row['rows']:,} | {row['distinct_sites']} | "
            f"{row['distinct_smrs']} | {row['first_scored_at'] or '-'} | "
            f"{row['last_scored_at'] or '-'} |"
        )
    lines.append("")
    lines.append("## composite_rankings")
    lines.append("")
    if composite and "error" not in composite[0]:
        lines.append("| run_id | rows | sites | SMRs | weight_profiles | first_ranked_at | last_ranked_at |")
        lines.append("| --- | ---: | ---: | ---: | --- | --- | --- |")
        for row in composite:
            lines.append(
                f"| `{row['run_id']}` | {row['rows']:,} | {row['distinct_sites']} | "
                f"{row['distinct_smrs']} | {row['weight_profiles'] or '-'} | "
                f"{row['first_ranked_at'] or '-'} | {row['last_ranked_at'] or '-'} |"
            )
    else:
        err = composite[0].get("error") if composite else "(no rows)"
        lines.append(f"_Not available: {err}_")
    lines.append("")
    lines.append("## screening_verdicts")
    lines.append("")
    if verdicts and "error" not in verdicts[0]:
        lines.append("| run_id | rows | sites | SMRs | fail rows | first_screened_at | last_screened_at |")
        lines.append("| --- | ---: | ---: | ---: | ---: | --- | --- |")
        for row in verdicts:
            lines.append(
                f"| `{row['run_id']}` | {row['rows']:,} | {row['distinct_sites']} | "
                f"{row['distinct_smrs']} | {row['fail_rows']:,} | "
                f"{row['first_screened_at'] or '-'} | {row['last_screened_at'] or '-'} |"
            )
    else:
        err = verdicts[0].get("error") if verdicts else "(no rows)"
        lines.append(f"_Not available: {err}_")
    lines.append("")
    lines.append("## scoring_run_snapshots (newest 100)")
    lines.append("")
    if snapshot_rows and "error" not in snapshot_rows[0]:
        lines.append("| run_id | snapshot_id | created_at |")
        lines.append("| --- | --- | --- |")
        for row in snapshot_rows:
            lines.append(
                f"| `{row['run_id']}` | `{row['snapshot_id'] or '-'}` | {row['created_at'] or '-'} |"
            )
    else:
        err = snapshot_rows[0].get("error") if snapshot_rows else "(no rows)"
        lines.append(f"_Not available: {err}_")
    lines.append("")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"ranking_scores: {len(ranking)} distinct run_ids")
    print(f"composite_rankings: {len(composite)} distinct run_ids")
    print(f"screening_verdicts: {len(verdicts)} distinct run_ids")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
