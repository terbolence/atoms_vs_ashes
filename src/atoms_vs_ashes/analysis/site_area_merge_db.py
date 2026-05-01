# man_hours: 2.0
"""DB routines for resolving merged site area from API, LLM, and favourable area."""

from __future__ import annotations

import os
from collections import Counter
from dataclasses import dataclass
from typing import Any

import psycopg2
import psycopg2.extras

from atoms_vs_ashes.analysis.site_area_resolution import resolve_site_area_ha

API_DB = "atoms_vs_ashes"
LLM_DB = "atoms_vs_ashes_llm"
MERGED_DB = "atoms_vs_ashes_merged"
CRITERION_ID = "NS-05"
RULE_ID = "site_area_resolve_v1"
OBSERVATION_TEXT = "area could not be identified"

SITE_KEY_SQL = """
SELECT site_id::text, name, country_code, round(latitude::numeric, 5)::text,
       round(longitude::numeric, 5)::text, COALESCE(gem_location_id, 'NA'),
       site_area_ha::float
FROM sites
"""

MERGED_SQL = """
SELECT s.site_id::text, s.name, s.country_code, round(s.latitude::numeric, 5)::text,
       round(s.longitude::numeric, 5)::text, COALESCE(s.gem_location_id, 'NA'),
       i.favourable_area_ha::float
FROM sites s
LEFT JOIN site_infrastructure_v2 i ON i.site_id = s.site_id
"""


@dataclass(frozen=True)
class AreaInputs:
    site_id: str
    name: str
    country_code: str | None
    llm_ha: float | None
    api_ha: float | None
    favourable_ha: float | None


def _conn_kwargs(db: str) -> dict[str, str]:
    return {
        "host": os.environ.get("POSTGRES_HOST", "localhost"),
        "port": os.environ.get("POSTGRES_PORT", "5432"),
        "user": os.environ.get("POSTGRES_USER", "atoms"),
        "password": os.environ.get("POSTGRES_PASSWORD", "changeme"),
        "dbname": db,
    }


def _connect(db: str):
    return psycopg2.connect(**_conn_kwargs(db))


def _key(row: tuple[Any, ...]) -> tuple[str, str | None, str, str, str]:
    return (row[1], row[2], row[3], row[4], row[5])


def _load_site_area_lookup(db: str) -> tuple[dict[tuple, float | None], set[tuple]]:
    lookup: dict[tuple, float | None] = {}
    duplicates: set[tuple] = set()
    with _connect(db) as conn, conn.cursor() as cur:
        cur.execute(SITE_KEY_SQL)
        for row in cur.fetchall():
            key = _key(row)
            if key in lookup:
                duplicates.add(key)
            else:
                lookup[key] = row[6]
    for key in duplicates:
        lookup.pop(key, None)
    return lookup, duplicates


def _load_merged_inputs() -> tuple[list[tuple], set[tuple]]:
    rows: list[tuple] = []
    seen: set[tuple] = set()
    duplicates: set[tuple] = set()
    with _connect(MERGED_DB) as conn, conn.cursor() as cur:
        cur.execute(MERGED_SQL)
        for row in cur.fetchall():
            key = _key(row)
            if key in seen:
                duplicates.add(key)
            seen.add(key)
            rows.append(row)
    return rows, duplicates


def build_inputs() -> tuple[list[AreaInputs], Counter]:
    api_lookup, api_dupes = _load_site_area_lookup(API_DB)
    llm_lookup, llm_dupes = _load_site_area_lookup(LLM_DB)
    merged_rows, merged_dupes = _load_merged_inputs()
    stats = Counter({
        "api_duplicate_keys": len(api_dupes),
        "llm_duplicate_keys": len(llm_dupes),
        "merged_duplicate_keys": len(merged_dupes),
    })
    inputs: list[AreaInputs] = []
    for row in merged_rows:
        key = _key(row)
        if key in merged_dupes:
            stats["skipped_merged_duplicate_key"] += 1
            continue
        if key in api_dupes or key not in api_lookup:
            stats["skipped_no_api_key"] += 1
            continue
        inputs.append(AreaInputs(
            site_id=row[0],
            name=row[1],
            country_code=row[2],
            llm_ha=llm_lookup.get(key),
            api_ha=api_lookup.get(key),
            favourable_ha=row[6],
        ))
    stats["inputs"] = len(inputs)
    return inputs, stats


def _comment(source: str, value: float | None) -> str:
    if value is None:
        return f"[resolved_site_area {source}: {OBSERVATION_TEXT}]"
    return f"[resolved_site_area {source}: {value:.2f} ha]"


def _json(value: dict[str, Any]) -> psycopg2.extras.Json:
    return psycopg2.extras.Json(value)


def apply_resolution(conn, item: AreaInputs, result, run_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE sites SET site_area_ha = %s, source_db = 'merged', merge_run_id = %s
            WHERE site_id = %s
            """,
            (result.value_ha, run_id, item.site_id),
        )
        if result.value_ha is None:
            _upsert_infra_null(cur, item.site_id, result.source, run_id)
            _insert_unidentified_observation(cur, item.site_id, run_id)
        else:
            _upsert_infra_value(cur, item.site_id, result.source, result.value_ha, run_id)
        _insert_audit(cur, item, result, run_id)


def _insert_unidentified_observation(cur, site_id: str, run_id: str) -> None:
    cur.execute(
        """
        INSERT INTO site_observations (
            observation_id, site_id, criterion_id, source_type, observation,
            impact, confidence, run_id, created_at
        ) VALUES (
            gen_random_uuid(), %s, %s, 'api', %s, 'negative', 'low', %s, now()
        )
        """,
        (site_id, CRITERION_ID, OBSERVATION_TEXT, run_id),
    )


def _insert_audit(cur, item: AreaInputs, result, run_id: str) -> None:
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
            item.site_id,
            CRITERION_ID,
            _json({"api_site_area_ha": item.api_ha, "favourable_area_ha": item.favourable_ha}),
            _json({"llm_site_area_ha": item.llm_ha}),
            _json({
                "site_area_ha": result.value_ha,
                "source": result.source,
                "observation": result.observation,
            }),
            RULE_ID,
            "Resolved site_area_ha using LLM >10 ha, API >10 ha, favourable >10 ha.",
        ),
    )


def _upsert_infra_value(cur, site_id: str, source: str, value: float, run_id: str) -> None:
    _upsert_infra(cur, site_id, source, value, run_id, quality="medium")


def _upsert_infra_null(cur, site_id: str, source: str, run_id: str) -> None:
    _upsert_infra(cur, site_id, source, None, run_id, quality="low")


def _upsert_infra(
    cur,
    site_id: str,
    source: str,
    value: float | None,
    run_id: str,
    *,
    quality: str,
) -> None:
    marker = _comment(source, value)
    cur.execute(
        """
        INSERT INTO site_infrastructure_v2 (
            site_id, buildable_area_ha, largest_contiguous_ha, ns05_quality,
            ns05_comment, fetched_at, run_id, source_db, merge_run_id
        ) VALUES (%s, %s, %s, %s, %s, now(), %s, 'merged', %s)
        ON CONFLICT (site_id) DO UPDATE
           SET buildable_area_ha = EXCLUDED.buildable_area_ha,
               largest_contiguous_ha = EXCLUDED.largest_contiguous_ha,
               ns05_comment = CASE
                   WHEN site_infrastructure_v2.ns05_comment LIKE '%%resolved_site_area%%'
                       THEN site_infrastructure_v2.ns05_comment
                   WHEN site_infrastructure_v2.ns05_comment IS NULL
                       OR site_infrastructure_v2.ns05_comment = ''
                       THEN EXCLUDED.ns05_comment
                   ELSE site_infrastructure_v2.ns05_comment || ' ' || EXCLUDED.ns05_comment
               END,
               fetched_at = now(),
               run_id = EXCLUDED.run_id,
               source_db = 'merged',
               merge_run_id = EXCLUDED.merge_run_id
        """,
        (site_id, value, value, quality, marker, run_id, run_id),
    )


def run(*, run_id: str, dry_run: bool) -> Counter:
    inputs, stats = build_inputs()
    source_counts: Counter = Counter()
    examples: list[str] = []
    with _connect(MERGED_DB) as conn:
        if not dry_run:
            _clear_run_rows(conn, run_id)
        for item in inputs:
            result = resolve_site_area_ha(item.llm_ha, item.api_ha, item.favourable_ha)
            source_counts[result.source] += 1
            if len(examples) < 12:
                examples.append(_example(item, result))
            if not dry_run:
                apply_resolution(conn, item, result, run_id)
        conn.rollback() if dry_run else conn.commit()
    stats.update({f"chosen_{k}": v for k, v in source_counts.items()})
    stats["updated"] = 0 if dry_run else len(inputs)
    print_summary(stats, examples, dry_run=dry_run, run_id=run_id)
    return stats


def _clear_run_rows(conn, run_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM merge_audit WHERE merge_run_id = %s AND rule_id = %s",
            (run_id, RULE_ID),
        )
        cur.execute(
            """
            DELETE FROM site_observations
            WHERE run_id = %s AND criterion_id = %s
              AND source_type = 'api' AND observation = %s
            """,
            (run_id, CRITERION_ID, OBSERVATION_TEXT),
        )


def _example(item: AreaInputs, result) -> str:
    return (
        f"{item.country_code} | {item.name}: {result.value_ha} ha "
        f"({result.source}; llm={item.llm_ha}, api={item.api_ha}, fav={item.favourable_ha})"
    )


def print_summary(stats: Counter, examples: list[str], *, dry_run: bool, run_id: str) -> None:
    mode = "DRY RUN" if dry_run else "WRITE"
    print(f"[{mode}] Site-area resolution run_id={run_id}")
    for key in sorted(stats):
        print(f"  {key}: {stats[key]}")
    print("  examples:")
    for line in examples:
        print(f"    - {line}")
