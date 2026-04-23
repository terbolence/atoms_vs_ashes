#!/usr/bin/env python
# man_hours: 4.0
"""Phase 5 — promote LLM-DB content into ``atoms_vs_ashes_merged``.

Implements the four buckets approved in
``audit/post_processing/02_data_verification/20260421_llm_field_promotion_proposal.md``:

* **Bucket 1** — Verdicts.  One row per ``(site_id, criterion_id,
  prompt_key)`` written to ``site_llm_verdicts``.  Consensus across
  the 8 SMR designs follows the rule in § 2.1 of the proposal:

    1. If **any** SMR design returned ``fail`` → emit ``fail``.
    2. Otherwise pick the *worst* verdict by the ordering
       ``not_assessed > deferred > inconclusive > caution > pass``
       (i.e. most conservative wins).
    3. Tie-break on highest confidence (``high > medium > low``).
    4. Final tie-break on ``run_id`` (lexicographically latest).

  ``smr_consensus_count`` records how many of the 8 designs voted for
  the chosen verdict; ``smr_disagreement = (consensus_count < 8)``.

  ``not_assessed`` rows where *every* SMR returned ``not_assessed``
  are skipped (no signal).

* **Bucket 2** — Justification.  Embedded in Bucket 1 as
  ``llm_justification`` (truncated at ``--justification-chars``,
  default 600).

* **Bucket 3** — Observations.  Rows from
  ``atoms_vs_ashes_llm.site_observations`` where
  ``source_type ∈ {'llm', 'web_search'}`` are copied into
  ``site_llm_observations``.  ``llm_error_migrated`` rows are skipped
  (already mirrored into the API DB by migration 020).

* **Bucket 4** — Structured back-fill.  Nine columns listed in § 2.4
  of the proposal.  For each ``(site, column)`` pair where the merged
  DB has ``NULL`` and the LLM DB has a value, the value is copied
  *only if* it passes the sanity bounds documented in
  ``report/business_logic.md`` (and re-applied here).  Every
  promotion writes a ``merge_audit`` row with ``source_chosen='llm'``
  (or ``source_chosen='rejected'`` if the bound is violated).
  Sites are joined by the composite key
  ``(name, country_code, lat, lon, COALESCE(gem_location_id, 'NA'))``
  because ``site_id`` is a per-DB UUID that does **not** survive the
  jump from the LLM DB to the merged DB.

Operational rules
-----------------

* The script is **idempotent** at the verdict and back-fill layers: a
  re-run does not create duplicate rows because of the unique
  constraints.
* The observations table is *append-only* in the merged DB — re-runs
  with a new ``--run-id`` will append, but the script skips rows
  whose ``observation_id`` already exists in the merged copy.
* ``--dry-run`` prints the planned counts and writes nothing.
* The script never touches ``atoms_vs_ashes`` (the source API DB)
  or ``atoms_vs_ashes_llm`` (read-only).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = PROJECT_ROOT / "audit" / "post_processing" / "02_data_verification"

LLM_DB = "atoms_vs_ashes_llm"
MERGED_DB = "atoms_vs_ashes_merged"

# Verdict ordering for the consensus rule (worst → best).
VERDICT_BADNESS = {
    "fail": 100,            # always wins (handled separately)
    "not_assessed": 5,
    "deferred": 4,
    "inconclusive": 3,
    "caution": 2,
    "pass": 1,
}

CONFIDENCE_BADNESS = {"high": 3, "medium": 2, "low": 1, "unknown": 0}


# ---------------------------------------------------------------------------
# Bucket 4 — back-fill specification
# ---------------------------------------------------------------------------

# In the LLM DB the ``*_quality`` columns store the *source flag*
# (always ``'llm'``), not a quality grade.  The proposal therefore
# gates promotions on **sanity bounds only**; the source flag is
# captured in the merge_audit ``rule_explanation`` for traceability
# but does not block the copy.
#
# Each entry: criterion, table, column, kind, kind-specific bounds.

BACKFILL_SPECS: list[dict] = [
    {
        "criterion": "NH-08",
        "table": "site_natural_hazards",
        "column": "tsunami_risk",
        "kind": "categorical",
        "allow_list": {"none", "negligible", "low", "moderate", "high"},
    },
    {
        "criterion": "NH-05",
        "table": "site_natural_hazards",
        "column": "subsidence_risk_class",
        "kind": "categorical",
        "allow_list": {"none", "low", "moderate", "high", "very_high"},
    },
    {
        "criterion": "NH-08",
        "table": "site_natural_hazards",
        "column": "distance_to_coast_km",
        "kind": "numeric",
        "min": 0,
        "max": 2000,
    },
    {
        "criterion": "NH-07",
        "table": "site_natural_hazards",
        "column": "nearest_holocene_volcano_km",
        "kind": "numeric",
        "min": 0,
        "max": 5000,
    },
    {
        "criterion": "NH-03",
        "table": "site_natural_hazards",
        "column": "groundwater_depth_m",
        "kind": "numeric",
        "min": 0,
        "max": 500,
    },
    {
        "criterion": "NS-03",
        "table": "site_infrastructure_v2",
        "column": "nearest_rail_km",
        "kind": "numeric",
        "min": 0,
        "max": 500,
    },
    {
        "criterion": "NS-03",
        "table": "site_infrastructure_v2",
        "column": "nearest_waterway_km",
        "kind": "numeric",
        "min": 0,
        "max": 500,
    },
    {
        "criterion": "NS-03",
        "table": "site_infrastructure_v2",
        "column": "nearest_highway_km",
        "kind": "numeric",
        "min": 0,
        "max": 500,
    },
    {
        "criterion": "NS-03",
        "table": "site_infrastructure_v2",
        "column": "heavy_haul_capable",
        "kind": "boolean",
    },
]


# Map column → source-flag column to record in the audit log (LLM DB
# always sets these to 'llm', so it's just provenance metadata).
SOURCE_FLAG_COLUMN: dict[tuple[str, str], str] = {
    ("site_natural_hazards", "subsidence_risk_class"): "nh05_quality",
    ("site_natural_hazards", "nearest_holocene_volcano_km"): "nh07_quality",
    ("site_infrastructure_v2", "nearest_rail_km"): "ns03_quality",
    ("site_infrastructure_v2", "nearest_waterway_km"): "ns03_quality",
    ("site_infrastructure_v2", "nearest_highway_km"): "ns03_quality",
    ("site_infrastructure_v2", "heavy_haul_capable"): "ns03_quality",
}


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _conn_kwargs(db: str) -> dict[str, str]:
    return {
        "host": os.environ.get("POSTGRES_HOST", "localhost"),
        "port": os.environ.get("POSTGRES_PORT", "5432"),
        "user": os.environ.get("POSTGRES_USER", "atoms"),
        "password": os.environ.get("POSTGRES_PASSWORD", "changeme"),
        "dbname": db,
    }


def _connect(db: str, *, autocommit: bool = False):
    conn = psycopg2.connect(**_conn_kwargs(db))
    conn.autocommit = autocommit
    return conn


# ---------------------------------------------------------------------------
# Site-ID translation between LLM DB and merged DB
# ---------------------------------------------------------------------------

SITE_KEY_SQL = (
    "SELECT site_id, name, country_code, "
    "round(latitude::numeric, 5) AS lat, "
    "round(longitude::numeric, 5) AS lon, "
    "COALESCE(gem_location_id, 'NA') AS glid "
    "FROM sites"
)


def build_site_id_map() -> dict[str, str]:
    """Return ``{llm_site_id: merged_site_id}`` joining on the composite
    key ``(name, country_code, lat, lon, COALESCE(gem_location_id))``.
    """
    print("[setup] Building LLM↔merged site-id map…")

    llm_rows: dict[tuple, str] = {}
    with _connect(LLM_DB) as conn, conn.cursor() as cur:
        cur.execute(SITE_KEY_SQL)
        for sid, name, cc, lat, lon, glid in cur.fetchall():
            key = (name, cc, lat, lon, glid)
            if key in llm_rows:
                raise RuntimeError(
                    f"Duplicate composite key in LLM DB: {key!r}"
                )
            llm_rows[key] = str(sid)

    mapping: dict[str, str] = {}
    unmatched_merged: list[str] = []
    with _connect(MERGED_DB) as conn, conn.cursor() as cur:
        cur.execute(SITE_KEY_SQL)
        for sid, name, cc, lat, lon, glid in cur.fetchall():
            key = (name, cc, lat, lon, glid)
            llm_sid = llm_rows.get(key)
            if llm_sid is None:
                unmatched_merged.append(f"{name}|{cc}|{lat},{lon}|{glid}")
                continue
            mapping[llm_sid] = str(sid)

    print(f"  LLM sites: {len(llm_rows)}")
    print(f"  merged sites mapped: {len(mapping)}")
    if unmatched_merged:
        print(f"  WARNING: {len(unmatched_merged)} merged sites had no LLM match:")
        for k in unmatched_merged[:5]:
            print(f"    - {k}")
    if len(mapping) < 360:
        raise RuntimeError(
            f"Site-id mapping covers only {len(mapping)} sites; "
            f"expected ≥360.  Aborting."
        )
    return mapping


# ---------------------------------------------------------------------------
# Bucket 1 — verdict consensus
# ---------------------------------------------------------------------------

def fetch_llm_verdicts(conn) -> list[dict]:
    sql = (
        "SELECT site_id, criterion_id, prompt_key, smr_key, run_id, "
        "       verdict::text, confidence, justification, sources_needed "
        "FROM screening_verdicts"
    )
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(sql)
        return [dict(r) for r in cur.fetchall()]


def consensus_for_combo(rows: list[dict]) -> dict | None:
    """Apply the consensus rule to all rows for a single
    ``(site_id, criterion_id, prompt_key)`` combo.

    Returns the chosen row plus aggregate stats, or ``None`` if every
    SMR returned ``not_assessed`` (no signal worth promoting).
    """
    # Most-recent run only (ignore historic runs of the same prompt).
    latest_run = max(r["run_id"] or "" for r in rows)
    rows = [r for r in rows if (r["run_id"] or "") == latest_run]

    # All-not_assessed → skip.
    if all(r["verdict"] == "not_assessed" for r in rows):
        return None

    # Step 1: any fail wins outright.
    fails = [r for r in rows if r["verdict"] == "fail"]
    if fails:
        chosen = max(fails, key=lambda r: CONFIDENCE_BADNESS.get(r["confidence"], 0))
        consensus_count = len(fails)
    else:
        # Step 2: most conservative (worst) verdict wins on majority,
        # then on confidence.
        def sort_key(r):
            return (
                VERDICT_BADNESS.get(r["verdict"], 0),
                CONFIDENCE_BADNESS.get(r["confidence"], 0),
                r["run_id"] or "",
            )
        chosen = max(rows, key=sort_key)
        consensus_count = sum(1 for r in rows if r["verdict"] == chosen["verdict"])

    return {
        **chosen,
        "smr_consensus_count": consensus_count,
        "smr_disagreement": consensus_count < len(rows),
        "smr_total": len(rows),
    }


def build_verdict_consensus(
    llm_rows: list[dict], site_map: dict[str, str], justification_chars: int
) -> tuple[list[dict], dict]:
    """Group all verdict rows by ``(site, criterion, prompt)`` and
    apply the consensus rule.  Returns the list of rows ready to insert
    into ``site_llm_verdicts`` plus a stats dict.
    """
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for r in llm_rows:
        key = (str(r["site_id"]), r["criterion_id"], r["prompt_key"])
        grouped[key].append(r)

    out: list[dict] = []
    skipped_all_not_assessed = 0
    skipped_no_site_map = 0
    disagreement_count = 0

    for (llm_sid, crit, prompt), rows in grouped.items():
        merged_sid = site_map.get(llm_sid)
        if merged_sid is None:
            skipped_no_site_map += 1
            continue
        chosen = consensus_for_combo(rows)
        if chosen is None:
            skipped_all_not_assessed += 1
            continue
        if chosen["smr_disagreement"]:
            disagreement_count += 1

        just = (chosen["justification"] or "")[:justification_chars]
        out.append({
            "site_id": merged_sid,
            "criterion_id": crit,
            "prompt_key": prompt,
            "llm_verdict": chosen["verdict"],
            "llm_verdict_confidence": chosen["confidence"] or "low",
            "llm_verdict_run_id": chosen["run_id"],
            "llm_verdict_smr_key": chosen["smr_key"],
            "smr_consensus_count": chosen["smr_consensus_count"],
            "smr_disagreement": chosen["smr_disagreement"],
            "llm_justification": just,
            "llm_sources_needed": chosen["sources_needed"],
        })

    stats = {
        "total_combos": len(grouped),
        "promoted": len(out),
        "skipped_all_not_assessed": skipped_all_not_assessed,
        "skipped_no_site_map": skipped_no_site_map,
        "disagreement_count": disagreement_count,
    }
    return out, stats


def insert_verdicts(
    rows: list[dict], merge_run_id: str, *, dry_run: bool
) -> int:
    if dry_run:
        print(f"  [dry-run] would insert {len(rows)} verdicts")
        return 0
    inserted = 0
    with _connect(MERGED_DB) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM site_llm_verdicts WHERE merge_run_id = %s", (merge_run_id,))
            for r in rows:
                cur.execute(
                    """
                    INSERT INTO site_llm_verdicts (
                        site_id, criterion_id, prompt_key, llm_verdict,
                        llm_verdict_confidence, llm_verdict_run_id,
                        llm_verdict_smr_key, smr_consensus_count,
                        smr_disagreement, llm_justification, llm_sources_needed,
                        source_db, merge_run_id
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        'llm', %s
                    )
                    ON CONFLICT (site_id, criterion_id, prompt_key)
                    DO UPDATE SET
                        llm_verdict = EXCLUDED.llm_verdict,
                        llm_verdict_confidence = EXCLUDED.llm_verdict_confidence,
                        llm_verdict_run_id = EXCLUDED.llm_verdict_run_id,
                        llm_verdict_smr_key = EXCLUDED.llm_verdict_smr_key,
                        smr_consensus_count = EXCLUDED.smr_consensus_count,
                        smr_disagreement = EXCLUDED.smr_disagreement,
                        llm_justification = EXCLUDED.llm_justification,
                        llm_sources_needed = EXCLUDED.llm_sources_needed,
                        source_db = 'llm',
                        merge_run_id = EXCLUDED.merge_run_id
                    """,
                    (
                        r["site_id"], r["criterion_id"], r["prompt_key"],
                        r["llm_verdict"], r["llm_verdict_confidence"],
                        r["llm_verdict_run_id"], r["llm_verdict_smr_key"],
                        r["smr_consensus_count"], r["smr_disagreement"],
                        r["llm_justification"], r["llm_sources_needed"],
                        merge_run_id,
                    ),
                )
                inserted += 1
        conn.commit()
    return inserted


# ---------------------------------------------------------------------------
# Bucket 3 — site observations
# ---------------------------------------------------------------------------

def promote_observations(
    site_map: dict[str, str], merge_run_id: str, *, dry_run: bool
) -> dict:
    print("[bucket 3] Promoting LLM site_observations…")
    fetch_sql = (
        "SELECT observation_id, site_id, criterion_id, source_type, "
        "       observation, impact, confidence, run_id "
        "FROM site_observations "
        "WHERE source_type IN ('llm', 'web_search')"
    )
    promoted = 0
    skipped_no_site_map = 0
    by_source: dict[str, int] = defaultdict(int)

    with _connect(LLM_DB) as src_conn, _connect(MERGED_DB) as tgt_conn:
        with src_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as src_cur:
            src_cur.execute(fetch_sql)
            llm_rows = src_cur.fetchall()
        with tgt_conn.cursor() as tgt_cur:
            if not dry_run:
                tgt_cur.execute(
                    "DELETE FROM site_llm_observations WHERE merge_run_id = %s",
                    (merge_run_id,),
                )
            for r in llm_rows:
                merged_sid = site_map.get(str(r["site_id"]))
                if merged_sid is None:
                    skipped_no_site_map += 1
                    continue
                by_source[r["source_type"]] += 1
                if dry_run:
                    promoted += 1
                    continue
                tgt_cur.execute(
                    """
                    INSERT INTO site_llm_observations (
                        observation_id, site_id, criterion_id, source_type,
                        observation, impact, confidence, llm_run_id,
                        source_db, merge_run_id
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, 'llm', %s
                    )
                    ON CONFLICT (observation_id) DO NOTHING
                    """,
                    (
                        r["observation_id"], merged_sid, r["criterion_id"],
                        r["source_type"], r["observation"], r["impact"],
                        r["confidence"], r["run_id"], merge_run_id,
                    ),
                )
                promoted += 1
        if not dry_run:
            tgt_conn.commit()

    print(f"  total LLM rows considered: {len(llm_rows)}")
    print(f"  promoted: {promoted}")
    print(f"  skipped (no site map): {skipped_no_site_map}")
    for k, v in sorted(by_source.items()):
        print(f"  by source_type[{k}]: {v}")

    return {
        "considered": len(llm_rows),
        "promoted": promoted,
        "skipped_no_site_map": skipped_no_site_map,
        "by_source_type": dict(by_source),
    }


# ---------------------------------------------------------------------------
# Bucket 4 — structured back-fill
# ---------------------------------------------------------------------------

def _passes_sanity(value: Any, spec: dict) -> tuple[bool, str | None]:
    if value is None:
        return False, "llm value NULL"
    kind = spec["kind"]
    if kind == "categorical":
        if str(value).strip().lower() in {a.lower() for a in spec["allow_list"]}:
            return True, None
        return False, f"value {value!r} not in allow-list {sorted(spec['allow_list'])}"
    if kind == "numeric":
        try:
            v = float(value)
        except (TypeError, ValueError):
            return False, f"value {value!r} not numeric"
        if v < spec["min"] or v > spec["max"]:
            return False, f"value {v} outside [{spec['min']}, {spec['max']}]"
        return True, None
    if kind == "boolean":
        if isinstance(value, bool):
            return True, None
        if str(value).lower() in {"true", "false", "t", "f", "0", "1"}:
            return True, None
        return False, f"value {value!r} not boolean-compatible"
    return False, f"unknown spec kind {kind!r}"


def _to_jsonb(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, default=str)


def promote_backfill(
    site_map: dict[str, str], merge_run_id: str, *, dry_run: bool
) -> dict:
    print("[bucket 4] Structured back-fill…")
    per_column: dict[str, dict] = {}

    with _connect(LLM_DB) as src_conn, _connect(MERGED_DB) as tgt_conn:
        for spec in BACKFILL_SPECS:
            tbl = spec["table"]
            col = spec["column"]
            qcol = SOURCE_FLAG_COLUMN.get((tbl, col))

            # Pull LLM source values (and the source-flag column, if any,
            # for audit logging).
            cols = [col]
            if qcol:
                cols.append(qcol)
            cols_sql = ", ".join(cols)
            with src_conn.cursor() as src_cur:
                src_cur.execute(
                    f"SELECT site_id, {cols_sql} FROM {tbl} WHERE {col} IS NOT NULL"
                )
                llm_records = src_cur.fetchall()

            # Build a {merged_site_id: (llm_value, llm_source_flag)} dict.
            llm_lookup: dict[str, tuple[Any, Any]] = {}
            for row in llm_records:
                llm_sid = str(row[0])
                merged_sid = site_map.get(llm_sid)
                if merged_sid is None:
                    continue
                llm_value = row[1]
                llm_flag = row[2] if qcol else None
                llm_lookup[merged_sid] = (llm_value, llm_flag)

            # Pull current merged values to find gaps.
            with tgt_conn.cursor() as tgt_cur:
                tgt_cur.execute(f"SELECT site_id, {col} FROM {tbl}")
                merged_rows = tgt_cur.fetchall()

            api_null_with_llm = []
            for sid, current in merged_rows:
                sid_s = str(sid)
                if current is not None:
                    continue  # API value present; we never overwrite
                if sid_s not in llm_lookup:
                    continue
                api_null_with_llm.append((sid_s, *llm_lookup[sid_s]))

            promoted = 0
            rejected_sanity = 0
            audit_rows = []
            update_rows = []

            for sid, llm_value, llm_flag in api_null_with_llm:
                ok, reason = _passes_sanity(llm_value, spec)
                if not ok:
                    rejected_sanity += 1
                    audit_rows.append({
                        "site_id": sid,
                        "source_chosen": "rejected",
                        "rule_id": "phase5_backfill_sanity",
                        "rule_explanation": reason,
                        "llm_value": llm_value,
                        "final_value": None,
                    })
                    continue
                promoted += 1
                update_rows.append((llm_value, sid))
                flag_note = (
                    f" (LLM source_flag {qcol}={llm_flag!r})" if qcol else ""
                )
                audit_rows.append({
                    "site_id": sid,
                    "source_chosen": "llm",
                    "rule_id": "phase5_backfill",
                    "rule_explanation": (
                        f"API NULL → copied from LLM{flag_note}"
                    ),
                    "llm_value": llm_value,
                    "final_value": llm_value,
                })

            if not dry_run and update_rows:
                # NOTE: ``source_db`` is set to ``'merged'`` (not
                # ``'llm'``) because the row is now a mix of API +
                # LLM cells.  Per-cell provenance lives in
                # ``merge_audit``.  Only rows that get *every* scalar
                # column from the LLM would warrant ``'llm'``, which
                # is not the case for any back-fill column here.
                with tgt_conn.cursor() as tgt_cur:
                    tgt_cur.executemany(
                        f"UPDATE {tbl} SET {col} = %s, "
                        f"source_db = 'merged', merge_run_id = %s "
                        f"WHERE site_id = %s AND {col} IS NULL",
                        [(v, merge_run_id, s) for (v, s) in update_rows],
                    )
            if not dry_run and audit_rows:
                with tgt_conn.cursor() as tgt_cur:
                    for a in audit_rows:
                        tgt_cur.execute(
                            """
                            INSERT INTO merge_audit (
                                merge_run_id, site_id, criterion_id,
                                table_name, column_name, source_chosen,
                                api_value, llm_value, final_value,
                                rule_id, rule_explanation
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s,
                                NULL, %s::jsonb, %s::jsonb,
                                %s, %s
                            )
                            """,
                            (
                                merge_run_id, a["site_id"], spec["criterion"],
                                tbl, col, a["source_chosen"],
                                _to_jsonb(a["llm_value"]),
                                _to_jsonb(a["final_value"]),
                                a["rule_id"], a["rule_explanation"],
                            ),
                        )

            per_column[f"{tbl}.{col}"] = {
                "criterion": spec["criterion"],
                "candidate_rows": len(api_null_with_llm),
                "promoted": promoted,
                "rejected_sanity": rejected_sanity,
            }
            print(
                f"  {tbl}.{col:30s} "
                f"candidates={len(api_null_with_llm):>4}  "
                f"promoted={promoted:>4}  "
                f"rejected_s={rejected_sanity:>3}"
            )

        if not dry_run:
            tgt_conn.commit()

    return per_column


# ---------------------------------------------------------------------------
# Run-record bookkeeping
# ---------------------------------------------------------------------------

def upsert_run_record(merge_run_id: str, *, dry_run: bool) -> None:
    if dry_run:
        return
    with _connect(MERGED_DB) as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO enrichment_runs "
            "(run_id, run_type, started_at, completed_at, status, notes) "
            "VALUES (%s, 'merge_phase5', %s, %s, 'completed', %s) "
            "ON CONFLICT (run_id) DO UPDATE SET "
            "completed_at = EXCLUDED.completed_at, status = 'completed'",
            (
                merge_run_id,
                datetime.now(timezone.utc),
                datetime.now(timezone.utc),
                "Phase 5: LLM verdict + observation + back-fill promotion",
            ),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def write_report(
    *,
    merge_run_id: str,
    verdict_stats: dict,
    observation_stats: dict,
    backfill_stats: dict,
    report_path: Path,
    dry_run: bool,
) -> None:
    if dry_run:
        return
    report_path.parent.mkdir(parents=True, exist_ok=True)
    today = datetime.now().date().isoformat()
    lines: list[str] = []
    lines.append(f"<!-- man_hours: 1.0 -->")
    lines.append("")
    lines.append(f"# Phase 5 — LLM promotion run report — {today}")
    lines.append("")
    lines.append(f"**Merge run id:** `{merge_run_id}`  ")
    lines.append(f"**Source DB:** `{LLM_DB}`  ")
    lines.append(f"**Target DB:** `{MERGED_DB}`  ")
    lines.append(
        f"**Migration head:** `032_add_llm_verdicts` "
        f"(verdicts + observations tables)"
    )
    lines.append("")
    lines.append("## Bucket 1 — Verdict consensus")
    lines.append("")
    lines.append(f"- `(site, criterion, prompt)` combos in LLM DB: "
                 f"**{verdict_stats['total_combos']}**")
    lines.append(f"- Promoted to `site_llm_verdicts`: "
                 f"**{verdict_stats['promoted']}**")
    lines.append(f"- Skipped (every SMR returned `not_assessed`): "
                 f"**{verdict_stats['skipped_all_not_assessed']}**")
    lines.append(f"- Skipped (site not in merged DB): "
                 f"**{verdict_stats['skipped_no_site_map']}**")
    lines.append(f"- Combos where SMRs disagreed: "
                 f"**{verdict_stats['disagreement_count']}**")
    lines.append("")
    lines.append("## Bucket 3 — Site observations")
    lines.append("")
    lines.append(f"- Considered: **{observation_stats['considered']}**")
    lines.append(f"- Promoted to `site_llm_observations`: "
                 f"**{observation_stats['promoted']}**")
    lines.append(f"- Skipped (site not in merged DB): "
                 f"**{observation_stats['skipped_no_site_map']}**")
    for src, n in sorted(observation_stats["by_source_type"].items()):
        lines.append(f"  - by `source_type` = `{src}`: **{n}**")
    lines.append("")
    lines.append("## Bucket 4 — Structured back-fill")
    lines.append("")
    lines.append("| Column | Criterion | Candidates | Promoted | Rejected (sanity) |")
    lines.append("|--------|-----------|-----------:|---------:|------------------:|")
    for col, st in backfill_stats.items():
        lines.append(
            f"| `{col}` | {st['criterion']} | {st['candidate_rows']} | "
            f"{st['promoted']} | {st['rejected_sanity']} |"
        )
    total_promoted = sum(s["promoted"] for s in backfill_stats.values())
    total_rejected = sum(
        s["rejected_sanity"] for s in backfill_stats.values()
    )
    lines.append("")
    lines.append(f"**Back-fill totals:** {total_promoted} promoted, "
                 f"{total_rejected} rejected.")
    lines.append("")
    lines.append("## Provenance")
    lines.append("")
    lines.append(
        "* All `site_llm_verdicts` and `site_llm_observations` rows "
        f"carry `source_db='llm'` and `merge_run_id='{merge_run_id}'`."
    )
    lines.append(
        "* Every back-fill cell-promotion (or rejection) is recorded "
        "in `merge_audit` with the rule id "
        "`phase5_backfill` (or `phase5_backfill_sanity` for rejections)."
    )
    lines.append(
        "* The post-LLM anomaly sweep "
        "(`scripts/scan_api_db_anomalies.py --target merged --filter "
        "source_db=llm`) runs separately."
    )
    lines.append("")
    report_path.write_text("\n".join(lines) + "\n")
    print(f"[report] wrote {report_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print planned counts without writing.",
    )
    parser.add_argument(
        "--run-id", default=None,
        help="Override merge_run_id (default: merge_phase5_<date>).",
    )
    parser.add_argument(
        "--justification-chars", type=int, default=600,
        help="Truncate llm_justification at this many characters (default 600).",
    )
    parser.add_argument(
        "--report", default=None,
        help="Override report path (default: audit/.../<date>_llm_promotion_report.md).",
    )
    args = parser.parse_args(argv)

    today = datetime.now().date().isoformat().replace("-", "")
    merge_run_id = args.run_id or f"merge_phase5_{today}"
    report_path = Path(args.report) if args.report else (
        REPORT_DIR / f"{today}_llm_promotion_report.md"
    )

    print(f"==> source: {LLM_DB}")
    print(f"==> target: {MERGED_DB}")
    print(f"==> merge_run_id: {merge_run_id}")
    print(f"==> mode: {'dry-run' if args.dry_run else 'apply'}")
    print()

    upsert_run_record(merge_run_id, dry_run=args.dry_run)

    site_map = build_site_id_map()
    print()

    print("[bucket 1] Building verdict consensus…")
    with _connect(LLM_DB) as conn:
        llm_rows = fetch_llm_verdicts(conn)
    print(f"  fetched {len(llm_rows)} verdict rows from LLM DB")
    verdict_rows, verdict_stats = build_verdict_consensus(
        llm_rows, site_map, args.justification_chars
    )
    print(f"  consensus produced {len(verdict_rows)} promotable rows")
    inserted = insert_verdicts(verdict_rows, merge_run_id, dry_run=args.dry_run)
    print(f"  inserted/updated: {inserted}")
    print()

    observation_stats = promote_observations(
        site_map, merge_run_id, dry_run=args.dry_run
    )
    print()

    backfill_stats = promote_backfill(
        site_map, merge_run_id, dry_run=args.dry_run
    )
    print()

    write_report(
        merge_run_id=merge_run_id,
        verdict_stats=verdict_stats,
        observation_stats=observation_stats,
        backfill_stats=backfill_stats,
        report_path=report_path,
        dry_run=args.dry_run,
    )

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
