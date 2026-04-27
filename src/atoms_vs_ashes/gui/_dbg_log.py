# man_hours: 0.1
"""Debug-mode NDJSON logger (temporary; removed once fix is verified).

Centralises the agent-log emission used by the Results page data
helpers while we verify the ``DetachedInstanceError`` fix. One log
file per debug session lives in ``.cursor/debug-<id>.log``; entries
are appended best-effort and never raise on I/O failure so they
cannot mask real bugs.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from sqlalchemy import func, select

# region agent log
_DBG_LOG = Path(
    "/Users/terbolence/Library/CloudStorage/GoogleDrive-bogdan@fulcrum-web.com"
    "/My Drive/SNN/01_proiecte/atoms_vs_ashes/.cursor/debug-f405ef.log"
)


def dbg(location: str, message: str, data: dict, hypothesis_id: str) -> None:
    """Append one NDJSON line to the debug-mode log (best-effort, no raise)."""
    try:
        payload = {
            "sessionId": "f405ef", "hypothesisId": hypothesis_id,
            "location": location, "message": message, "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with _DBG_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, default=str) + "\n")
    except Exception:
        pass


def probe_verdict_source(
    session, run_id: str, sites: set, smrs: set,
    pair_list: list, n_strict: int,
) -> None:
    """Diagnostic only: cross-tabulate fail verdicts by run_id (H4 / H5)."""
    try:
        from atoms_vs_ashes.db.models import ScreeningVerdict
        from atoms_vs_ashes.db.models_analytics import Run
        per_run = session.execute(
            select(ScreeningVerdict.run_id, func.count())
            .where((ScreeningVerdict.verdict == "fail")
                   & (ScreeningVerdict.site_id.in_(sites))
                   & (ScreeningVerdict.smr_key.in_(smrs)))
            .group_by(ScreeningVerdict.run_id)
        ).all()
        meta = session.execute(
            select(Run.run_id, Run.run_kind, Run.parent_run_id)
            .where(Run.run_id == run_id)).first()
        dbg(
            "_results_data_failure.py:_load_failed_verdicts",
            "verdict-source run_id probe",
            {
                "requested_run_id": run_id,
                "n_distinct_sites": len(sites),
                "n_distinct_smrs": len(smrs),
                "n_distinct_pairs": len(set(pair_list)),
                "n_strict_match_rows": n_strict,
                "fail_verdicts_by_run": [
                    {"run_id": str(r), "n": int(n)} for r, n in per_run],
                "run_meta": (
                    None if meta is None else
                    {
                        "run_id": str(meta[0]), "run_kind": str(meta[1]),
                        "parent_run_id": (
                            str(meta[2]) if meta[2] else None
                        ),
                    }
                ),
            },
            "H4",
        )
    except Exception as exc:
        dbg(
            "_results_data_failure.py:_load_failed_verdicts",
            "diagnostic probe raised",
            {"requested_run_id": run_id, "error": repr(exc)}, "H4",
        )
# endregion agent log


__all__ = ["dbg", "probe_verdict_source"]
