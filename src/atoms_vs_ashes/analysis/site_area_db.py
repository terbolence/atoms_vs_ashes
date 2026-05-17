# man_hours: 4.5
"""Database and CSV helpers for v2 site-area resolution."""

from __future__ import annotations

import csv
import json
import os
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import psycopg2
import psycopg2.extras

from atoms_vs_ashes.analysis.site_area_resolution import (
    SiteAreaContext,
    build_site_area_recommendation,
    parse_site_area_observation,
)

DEFAULT_DB = "atoms_vs_ashes_merged"
DEFAULT_LLM_DB = "atoms_vs_ashes_llm"
CRITERION_ID = "NS-05"
RULE_ID = "site_area_resolve_v2"

CSV_FIELDS = [
    "site_id",
    "country_code",
    "name",
    "status",
    "current_site_area_ha",
    "recommended_site_area_ha",
    "recommended_source",
    "recommended_confidence",
    "confidence_score",
    "write_eligible",
    "review_flags",
    "candidate_values_json",
    "regional_developable_ha",
    "regional_developable_method",
    "expansion_potential_ha",
    "buildable_text_ha",
    "buildable_area_ha",
    "largest_contiguous_ha",
    "favourable_area_ha",
    "ns05_quality",
    "ns05_comment",
    "merge_audit_final_ha",
    "llm_structured_ha",
    "llm_db_site_area_ha",
    "llm_observation_text",
]


@dataclass(frozen=True)
class ManualOverride:
    value_ha: float
    note: str


def conn_kwargs(db_name: str) -> dict[str, str]:
    return {
        "host": os.environ.get("POSTGRES_HOST", "localhost"),
        "port": os.environ.get("POSTGRES_PORT", "5432"),
        "user": os.environ.get("POSTGRES_USER", "atoms"),
        "password": os.environ.get("POSTGRES_PASSWORD", "changeme"),
        "dbname": db_name,
    }


def connect(db_name: str):
    return psycopg2.connect(**conn_kwargs(db_name))


def load_manual_overrides(path: str | Path | None) -> dict[str, ManualOverride]:
    """Load optional ``site_id,value_ha,note`` CSV overrides."""
    if path is None:
        return {}

    overrides: dict[str, ManualOverride] = {}
    with Path(path).open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            site_id = (row.get("site_id") or "").strip()
            raw_value = row.get("value_ha") or row.get("site_area_ha")
            if not site_id or raw_value in {None, ""}:
                continue
            overrides[site_id] = ManualOverride(
                value_ha=float(raw_value),
                note=(row.get("note") or "manual override").strip(),
            )
    return overrides


def fetch_site_rows(
    *,
    db_name: str = DEFAULT_DB,
    llm_db_name: str = DEFAULT_LLM_DB,
    limit: int | None = None,
    site_ids: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """Read candidate inputs from merged DB plus LLM DB site-area values."""
    ids = [str(site_id) for site_id in (site_ids or [])]
    where = ""
    params: list[Any] = []
    if ids:
        where = "WHERE s.site_id::text = ANY(%s)"
        params.append(ids)

    limit_sql = ""
    if limit is not None:
        limit_sql = "LIMIT %s"
        params.append(limit)

    sql = f"""
        SELECT
            s.site_id::text,
            s.name,
            s.country_code,
            s.status::text,
            s.installed_capacity_mw::float,
            s.site_area_ha::float,
            i.buildable_area_ha::float,
            i.largest_contiguous_ha::float,
            i.favourable_area_ha::float,
            i.favourable_area_method,
            i.ns05_quality,
            i.ns05_comment,
            (ma.llm_value->>'llm_site_area_ha')::float AS llm_structured_ha,
            (ma.final_value->>'site_area_ha')::float AS merge_audit_final_ha,
            obs.observation AS llm_observation
        FROM sites s
        LEFT JOIN site_infrastructure_v2 i ON i.site_id = s.site_id
        LEFT JOIN LATERAL (
            SELECT llm_value, final_value
            FROM merge_audit ma
            WHERE ma.site_id = s.site_id
              AND ma.criterion_id = %s
              AND ma.column_name = 'site_area_ha'
            ORDER BY ma.created_at DESC
            LIMIT 1
        ) ma ON true
        LEFT JOIN LATERAL (
            SELECT observation
            FROM site_llm_observations o
            WHERE o.site_id = s.site_id
              AND o.criterion_id = %s
            ORDER BY o.created_at DESC
            LIMIT 1
        ) obs ON true
        {where}
        ORDER BY s.country_code, s.name
        {limit_sql}
    """

    rows: list[dict[str, Any]]
    with connect(db_name) as conn:
        conn.set_session(readonly=True, autocommit=True)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, [CRITERION_ID, CRITERION_ID, *params])
            rows = [dict(row) for row in cur.fetchall()]

    llm_values = _fetch_llm_site_area_map(llm_db_name, [row["site_id"] for row in rows])
    for row in rows:
        row["llm_db_site_area_ha"] = llm_values.get(row["site_id"])
    return rows


def recommendations_from_rows(
    rows: Iterable[dict[str, Any]],
    *,
    manual_overrides: dict[str, ManualOverride] | None = None,
) -> list[dict[str, Any]]:
    overrides = manual_overrides or {}
    output: list[dict[str, Any]] = []
    for row in rows:
        site_id = row["site_id"]
        observation = parse_site_area_observation(row.get("llm_observation"))
        context = SiteAreaContext(
            site_id=site_id,
            name=row["name"],
            country_code=row.get("country_code"),
            status=row.get("status"),
            installed_capacity_mw=row.get("installed_capacity_mw"),
            current_site_area_ha=row.get("site_area_ha"),
            ns05_quality=row.get("ns05_quality"),
            ns05_comment=row.get("ns05_comment"),
            buildable_area_ha=row.get("buildable_area_ha"),
            largest_contiguous_ha=row.get("largest_contiguous_ha"),
            favourable_area_ha=row.get("favourable_area_ha"),
            favourable_area_method=row.get("favourable_area_method"),
            merge_audit_final_ha=row.get("merge_audit_final_ha"),
            llm_observation=observation,
        )
        override = overrides.get(site_id)
        recommendation = build_site_area_recommendation(
            context,
            manual_verified_ha=override.value_ha if override else None,
            manual_note=override.note if override else None,
            llm_structured_ha=row.get("llm_structured_ha"),
            llm_db_site_ha=row.get("llm_db_site_area_ha"),
        )
        output.append(render_recommendation_row(row, recommendation))
    return output


def render_recommendation_row(row: dict[str, Any], recommendation) -> dict[str, Any]:
    return {
        "site_id": recommendation.site_id,
        "country_code": row.get("country_code"),
        "name": recommendation.name,
        "status": row.get("status"),
        "current_site_area_ha": row.get("site_area_ha"),
        "recommended_site_area_ha": recommendation.proposed_site_area_ha,
        "recommended_source": recommendation.source,
        "recommended_confidence": recommendation.confidence_tier,
        "confidence_score": recommendation.confidence_score,
        "write_eligible": recommendation.write_eligible,
        "review_flags": ";".join(recommendation.review_flags),
        "candidate_values_json": json.dumps(
            recommendation.candidates_json(),
            ensure_ascii=False,
            sort_keys=True,
        ),
        "regional_developable_ha": recommendation.regional_developable_ha,
        "regional_developable_method": recommendation.regional_developable_method,
        "expansion_potential_ha": recommendation.expansion_potential_ha,
        "buildable_text_ha": recommendation.buildable_text_ha,
        "buildable_area_ha": row.get("buildable_area_ha"),
        "largest_contiguous_ha": row.get("largest_contiguous_ha"),
        "favourable_area_ha": row.get("favourable_area_ha"),
        "ns05_quality": row.get("ns05_quality"),
        "ns05_comment": row.get("ns05_comment"),
        "merge_audit_final_ha": row.get("merge_audit_final_ha"),
        "llm_structured_ha": row.get("llm_structured_ha"),
        "llm_db_site_area_ha": row.get("llm_db_site_area_ha"),
        "llm_observation_text": row.get("llm_observation"),
    }


def write_recommendations_csv(rows: list[dict[str, Any]], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def summarize_recommendations(rows: Iterable[dict[str, Any]]) -> Counter:
    counter: Counter = Counter()
    for row in rows:
        counter["rows"] += 1
        if _truthy(row.get("write_eligible")):
            counter["write_eligible"] += 1
        counter[f"source_{row.get('recommended_source') or 'none'}"] += 1
        counter[f"confidence_{row.get('recommended_confidence') or 'none'}"] += 1
        for flag in str(row.get("review_flags") or "").split(";"):
            if flag:
                counter[f"flag_{flag}"] += 1
    return counter


def _fetch_llm_site_area_map(db_name: str, site_ids: list[str]) -> dict[str, float | None]:
    if not site_ids:
        return {}
    with connect(db_name) as conn:
        conn.set_session(readonly=True, autocommit=True)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT site_id::text, site_area_ha::float
                FROM sites
                WHERE site_id::text = ANY(%s)
                """,
                (site_ids,),
            )
            return {site_id: value for site_id, value in cur.fetchall()}


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"true", "1", "yes"}
