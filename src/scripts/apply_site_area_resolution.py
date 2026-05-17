#!/usr/bin/env python
# man_hours: 3.7
"""Consent-gated writer for v2 site-area recommendations.

Default mode is dry-run. Database writes require both ``--write`` and
``--i-consent-to-write`` so recommendation review and mutation stay separate.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg2.extras

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from atoms_vs_ashes.analysis.site_area_db import (
    CRITERION_ID,
    DEFAULT_DB,
    DEFAULT_LLM_DB,
    RULE_ID,
    connect,
    fetch_site_rows,
    load_manual_overrides,
    recommendations_from_rows,
    summarize_recommendations,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-name", default=DEFAULT_DB)
    parser.add_argument("--llm-db-name", default=DEFAULT_LLM_DB)
    parser.add_argument("--manual-overrides", type=Path)
    parser.add_argument("--site-id", action="append", dest="site_ids")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--run-id", default=_default_run_id())
    parser.add_argument("--write", action="store_true", help="Perform DB writes; otherwise dry-run")
    parser.add_argument(
        "--i-consent-to-write",
        action="store_true",
        help="Required with --write; confirms the user approved this DB mutation scope",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.write and not args.i_consent_to_write:
        raise SystemExit("--write requires --i-consent-to-write")

    source_rows = fetch_site_rows(
        db_name=args.db_name,
        llm_db_name=args.llm_db_name,
        limit=args.limit,
        site_ids=args.site_ids,
    )
    recommendations = recommendations_from_rows(
        source_rows,
        manual_overrides=load_manual_overrides(args.manual_overrides),
    )
    eligible = [row for row in recommendations if _truthy(row["write_eligible"])]

    print(f"run_id: {args.run_id}")
    print(f"mode: {'WRITE' if args.write else 'DRY RUN'}")
    print(f"recommendations: {len(recommendations)}")
    print(f"write_eligible: {len(eligible)}")
    for key, value in sorted(summarize_recommendations(recommendations).items()):
        print(f"{key}: {value}")

    if not args.write:
        return 0

    with connect(args.db_name) as conn:
        with conn.cursor() as cur:
            for row in eligible:
                _apply_one(cur, row, args.run_id)
        conn.commit()
    print(f"updated: {len(eligible)}")
    return 0


def _apply_one(cur, row: dict[str, Any], run_id: str) -> None:
    candidates = json.loads(row["candidate_values_json"] or "[]")
    review_flags = [flag for flag in str(row.get("review_flags") or "").split(";") if flag]
    site_id = row["site_id"]
    recommended = row["recommended_site_area_ha"]
    now = datetime.now(timezone.utc)

    cur.execute(
        """
        UPDATE sites
           SET site_area_ha = %s,
               site_area_source = %s,
               site_area_confidence = %s,
               site_area_review_flags = %s,
               site_area_candidates_json = %s,
               expansion_potential_ha = %s,
               site_area_resolved_at = %s,
               site_area_resolve_run_id = %s,
               source_db = 'merged',
               merge_run_id = %s,
               updated_at = now()
         WHERE site_id = %s
        """,
        (
            recommended,
            row["recommended_source"],
            row["recommended_confidence"],
            psycopg2.extras.Json(review_flags),
            psycopg2.extras.Json(candidates),
            row.get("expansion_potential_ha") or None,
            now,
            run_id,
            run_id,
            site_id,
        ),
    )

    cur.execute(
        """
        INSERT INTO merge_audit (
            audit_id, merge_run_id, site_id, criterion_id, table_name,
            column_name, source_chosen, api_value, llm_value, final_value,
            rule_id, rule_explanation, created_at
        ) VALUES (
            gen_random_uuid(), %s, %s, %s, 'sites', 'site_area_ha', 'merged',
            %s, %s, %s, %s, %s, now()
        )
        """,
        (
            run_id,
            site_id,
            CRITERION_ID,
            psycopg2.extras.Json({
                "current_site_area_ha": row.get("current_site_area_ha"),
                "buildable_area_ha": row.get("buildable_area_ha"),
                "largest_contiguous_ha": row.get("largest_contiguous_ha"),
                "favourable_area_ha": row.get("favourable_area_ha"),
            }),
            psycopg2.extras.Json({
                "llm_structured_ha": row.get("llm_structured_ha"),
                "llm_db_site_area_ha": row.get("llm_db_site_area_ha"),
                "llm_observation_text": row.get("llm_observation_text"),
            }),
            psycopg2.extras.Json({
                "site_area_ha": recommended,
                "source": row["recommended_source"],
                "confidence": row["recommended_confidence"],
                "confidence_score": row["confidence_score"],
                "review_flags": review_flags,
                "candidates": candidates,
            }),
            RULE_ID,
            "Resolved site_area_ha from direct evidence plus bounded buildable, contiguous, favourable-envelope, and capacity inference candidates.",
        ),
    )


def _default_run_id() -> str:
    return f"site_area_resolve_v2_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"true", "1", "yes"}


if __name__ == "__main__":
    raise SystemExit(main())
