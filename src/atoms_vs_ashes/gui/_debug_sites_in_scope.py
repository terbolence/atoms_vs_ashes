# man_hours: 0.4
"""TEMPORARY debug instrumentation for the "362 vs 361 sites in scope" bug.

This file is added in debug session ``1b151b`` and is intended to be
removed once the discrepancy is understood. It writes NDJSON entries
to the workspace debug log (``.cursor/debug-1b151b.log``) so the
analysis can compare engine view vs GUI view of the active run.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from atoms_vs_ashes.db.models import CompositeRanking, Site
from atoms_vs_ashes.runtime.scope import RunScope

_LOG_PATH = Path(
    "/Users/terbolence/projects/atoms_vs_ashes/.cursor/debug-1b151b.log"
)


def _emit(payload: dict[str, Any]) -> None:
    payload.setdefault("sessionId", "1b151b")
    payload.setdefault("timestamp", int(time.time() * 1000))
    try:
        with _LOG_PATH.open("a") as fh:
            fh.write(json.dumps(payload, default=str) + "\n")
    except Exception:
        pass


def diagnose_sites_in_scope(
    *,
    session: Session,
    run_id: str,
    weight_profile: str,
    scope: RunScope | None,
    sites_all: Iterable[Any],
) -> None:
    """Compare engine site scope vs GUI scope vs raw composite_rankings.

    Writes three NDJSON entries:
    * counts_overview — H1/H4 summary numbers (engine vs unscoped composite vs GUI scoped).
    * composite_per_profile_for_run — H2 weight-profile breakdown for this run.
    * missing_sites_detail — H1/H3/H4 per-site detail for any candidate IDs.
    """
    sites_all_set = {str(s) for s in sites_all}

    cr_unscoped_rows = session.execute(
        select(CompositeRanking.site_id)
        .where(
            (CompositeRanking.run_id == run_id)
            & (CompositeRanking.weight_profile == weight_profile)
        )
        .distinct()
    ).scalars().all()
    cr_unscoped_set = {str(s) for s in cr_unscoped_rows}

    if scope is not None:
        engine_stmt = scope.apply_to_sites(select(Site.site_id))
    else:
        engine_stmt = select(Site.site_id)
    engine_rows = session.execute(engine_stmt).scalars().all()
    engine_set = {str(s) for s in engine_rows}

    sites_total_in_db = session.execute(
        select(func.count(Site.site_id))
    ).scalar_one()

    missing_engine_minus_gui = engine_set - sites_all_set
    engine_minus_unscoped = engine_set - cr_unscoped_set
    unscoped_minus_gui = cr_unscoped_set - sites_all_set

    _emit({
        "runId": "pre-fix",
        "hypothesisId": "H1+H4+H5",
        "location": "_results_data_failure.run_kpis:diag",
        "message": "counts_overview",
        "data": {
            "run_id": str(run_id),
            "weight_profile": str(weight_profile),
            "scope": scope.to_dict() if scope is not None else None,
            "n_sites_total_in_db": int(sites_total_in_db),
            "n_sites_engine_scope": len(engine_set),
            "n_sites_composite_unscoped": len(cr_unscoped_set),
            "n_sites_in_scope_gui": len(sites_all_set),
            "n_engine_minus_gui": len(missing_engine_minus_gui),
            "n_engine_minus_unscoped": len(engine_minus_unscoped),
            "n_unscoped_minus_gui": len(unscoped_minus_gui),
        },
    })

    by_profile = session.execute(
        select(
            CompositeRanking.weight_profile,
            func.count(func.distinct(CompositeRanking.site_id)),
        )
        .where(CompositeRanking.run_id == run_id)
        .group_by(CompositeRanking.weight_profile)
    ).all()
    _emit({
        "runId": "pre-fix",
        "hypothesisId": "H2",
        "location": "_results_data_failure.run_kpis:diag",
        "message": "composite_per_profile_for_run",
        "data": {
            "run_id": str(run_id),
            "by_profile": {str(p): int(c) for p, c in by_profile},
        },
    })

    candidate_set = (
        missing_engine_minus_gui | engine_minus_unscoped | unscoped_minus_gui
    )
    candidates = list(candidate_set)[:20]
    if candidates:
        rows = session.execute(
            select(
                Site.site_id, Site.name, Site.country_code, Site.status,
            ).where(Site.site_id.in_(candidates))
        ).all()
        comp_rows = session.execute(
            select(
                CompositeRanking.site_id,
                CompositeRanking.run_id,
                CompositeRanking.weight_profile,
                CompositeRanking.smr_key,
            ).where(CompositeRanking.site_id.in_(candidates))
        ).all()
        comp_summary: dict[str, list[dict[str, str]]] = {}
        for sid, rid, wp, sk in comp_rows:
            comp_summary.setdefault(str(sid), []).append({
                "run_id": str(rid),
                "weight_profile": str(wp),
                "smr_key": str(sk),
            })
        _emit({
            "runId": "pre-fix",
            "hypothesisId": "H1+H3+H4",
            "location": "_results_data_failure.run_kpis:diag",
            "message": "missing_sites_detail",
            "data": {
                "n_candidates": len(candidate_set),
                "showing": len(candidates),
                "sites": [
                    {
                        "site_id": str(sid),
                        "name": str(name),
                        "country_code": str(cc),
                        "status": str(status),
                        "in_engine_scope": str(sid) in engine_set,
                        "in_unscoped_composite": str(sid) in cr_unscoped_set,
                        "in_gui_scope": str(sid) in sites_all_set,
                        "composite_rows_any_run": comp_summary.get(
                            str(sid), [],
                        ),
                    }
                    for sid, name, cc, status in rows
                ],
            },
        })


__all__ = ["diagnose_sites_in_scope"]
