# man_hours: 0.5
"""Merged-DB-specific sheet builders (Phase-2 and Phase-5 artefacts).

Only meaningful against ``atoms_vs_ashes_merged``. The orchestrator
conditionally includes these sheets when the ``--database merged`` flag
is set.

Covers:

- LLM verdicts promoted into the merged DB.
- LLM observations (narrative / site_llm_observations).
- Per-cell merge audit (``merge_audit``).
- Per-table source_db provenance summary.
- The ``enrichment_runs`` ledger.
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

_PROVENANCE_TABLES = (
    "sites",
    "site_natural_hazards",
    "site_human_hazards",
    "site_radiological",
    "site_emergency_planning",
    "site_infrastructure_v2",
)


def build_llm_verdicts_df(session: Session) -> pd.DataFrame:
    """One row per promoted ``site_llm_verdicts`` entry."""
    sql = text(
        """
        SELECT v.llm_verdict_id,
               v.site_id,
               s.name              AS site_name,
               s.country_code      AS country,
               v.criterion_id,
               c.name              AS criterion_name,
               c.category          AS criterion_category,
               c.phase             AS criterion_phase,
               v.prompt_key,
               v.llm_verdict::text AS llm_verdict,
               v.llm_verdict_confidence,
               v.smr_consensus_count,
               v.smr_disagreement,
               v.llm_verdict_smr_key,
               v.llm_verdict_run_id,
               v.llm_justification,
               v.llm_sources_needed,
               v.source_db,
               v.merge_run_id,
               v.created_at
        FROM site_llm_verdicts v
        JOIN sites s         ON v.site_id      = s.site_id
        LEFT JOIN criteria c ON v.criterion_id = c.criterion_id
        ORDER BY s.country_code, s.name, v.criterion_id, v.prompt_key
        """
    )
    rows = session.execute(sql).mappings().all()
    return pd.DataFrame([dict(r) for r in rows])


def build_llm_observations_df(session: Session) -> pd.DataFrame:
    """One row per promoted ``site_llm_observations`` entry."""
    sql = text(
        """
        SELECT o.observation_id,
               o.site_id,
               s.name              AS site_name,
               s.country_code      AS country,
               o.criterion_id,
               c.name              AS criterion_name,
               c.category          AS criterion_category,
               o.source_type,
               o.impact,
               o.confidence,
               o.observation,
               o.llm_run_id,
               o.source_db,
               o.merge_run_id,
               o.created_at
        FROM site_llm_observations o
        JOIN sites s         ON o.site_id      = s.site_id
        LEFT JOIN criteria c ON o.criterion_id = c.criterion_id
        ORDER BY s.country_code, s.name, o.criterion_id
        """
    )
    rows = session.execute(sql).mappings().all()
    return pd.DataFrame([dict(r) for r in rows])


def build_merge_audit_df(session: Session) -> pd.DataFrame:
    """Cell-level provenance: one row per Phase-5 promotion / rejection."""
    sql = text(
        """
        SELECT a.audit_id,
               a.merge_run_id,
               a.site_id,
               s.name              AS site_name,
               s.country_code      AS country,
               a.criterion_id,
               c.name              AS criterion_name,
               a.table_name,
               a.column_name,
               a.source_chosen,
               a.api_value,
               a.llm_value,
               a.final_value,
               a.rule_id,
               a.rule_explanation,
               a.created_at
        FROM merge_audit a
        JOIN sites s         ON a.site_id      = s.site_id
        LEFT JOIN criteria c ON a.criterion_id = c.criterion_id
        ORDER BY a.merge_run_id, a.table_name, a.column_name,
                 s.country_code, s.name
        """
    )
    rows = session.execute(sql).mappings().all()
    return pd.DataFrame([dict(r) for r in rows])


def build_provenance_summary_df(session: Session) -> pd.DataFrame:
    """Per-table count of rows by ``source_db``."""
    rows = []
    for tbl in _PROVENANCE_TABLES:
        try:
            res = session.execute(
                text(
                    f"SELECT source_db, count(*) AS n FROM {tbl} "
                    f"GROUP BY source_db ORDER BY source_db"
                )
            ).all()
        except Exception:
            continue
        counts = {r[0]: r[1] for r in res}
        rows.append({
            "table": tbl,
            "api": counts.get("api", 0),
            "llm": counts.get("llm", 0),
            "merged": counts.get("merged", 0),
            "total": sum(counts.values()),
        })
    return pd.DataFrame(rows)


def build_enrichment_runs_df(session: Session) -> pd.DataFrame:
    """Full ``enrichment_runs`` ledger."""
    sql = text(
        """
        SELECT run_id, run_type, connector_slug,
               started_at, completed_at, status,
               site_count, success_count, error_count,
               config_hash, notes
        FROM enrichment_runs
        ORDER BY started_at DESC, run_id
        """
    )
    rows = session.execute(sql).mappings().all()
    return pd.DataFrame([dict(r) for r in rows])
