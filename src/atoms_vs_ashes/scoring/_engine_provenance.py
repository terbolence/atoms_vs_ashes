# man_hours: 1.0
"""Engine-side provenance helpers — keeps :mod:`engine` ≤ 300 lines.

These were inline methods of :class:`ScoringEngine`; extracted into a
small module so the orchestrator stays focused on the per-site loop.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from dataclasses import replace

from atoms_vs_ashes.db.models import AuditLog, Site, SmrDesign
from atoms_vs_ashes.db.runs import DatasetMeta, start_run
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring._codes import check_rubric_coverage
from atoms_vs_ashes.scoring.rubric import Criterion

log = get_logger(__name__)


def open_scoring_run(
    session: Session,
    *,
    run_id: str,
    rubric_dir: str,
    bundle: dict[str, Criterion],
    sites: list[Site],
    smrs: list[SmrDesign],
    weight_profile: str,
    dataset_meta: DatasetMeta | None = None,
):
    """Open the ``runs`` row plus a ``dataset_snapshot``.

    When the caller hands in a pre-built :class:`DatasetMeta` (e.g.
    from :func:`atoms_vs_ashes.runprofile.dataset_meta_for_profile`)
    we layer the runtime cardinalities — ``n_sites_total`` /
    ``n_smrs`` / ``n_criteria_ranking`` — on top of the user-supplied
    fields so RunProfile-driven runs preserve the richer provenance
    (``run_profile_sha256``, ``spec_bundle_sha256``,
    ``scope_summary``, etc.).
    """
    runtime_fields = dict(
        rubric_file_path=rubric_dir,
        n_sites_total=len(sites),
        n_smrs=len(smrs),
        n_criteria_ranking=sum(1 for c in bundle.values() if c.is_ranking),
        weight_normalisation_profile=weight_profile,
    )
    if dataset_meta is None:
        meta = DatasetMeta(**runtime_fields)
    else:
        meta = replace(dataset_meta, **runtime_fields)
    return start_run(
        session, run_kind="scoring", run_id=run_id, dataset_meta=meta,
    )


def check_code_coverage(
    bundle: dict[str, Criterion], summary
) -> None:
    """Warn if the loaded rubric drifts from the E1-E9 / A1-A15 catalog."""
    rubric_codes = {
        fc.code
        for c in bundle.values()
        for fc in c.fail_conditions
        if fc.action in ("exclude", "avoidance_penalty")
    }
    missing, extra = check_rubric_coverage(rubric_codes)
    if missing:
        summary.warnings.append(
            f"catalog_codes_missing_from_rubric={sorted(missing)}"
        )
        log.warning("scoring_catalog_mismatch", missing=sorted(missing))
    if extra:
        summary.warnings.append(f"rubric_codes_not_in_catalog={sorted(extra)}")
        log.warning("scoring_catalog_mismatch", extra=sorted(extra))


def write_scoring_audit(session: Session, summary) -> None:
    session.add(
        AuditLog(
            operation="scoring",
            table_name="ranking_scores",
            run_id=summary.run_id,
            message=(
                f"profile={summary.weight_profile} "
                f"sites={summary.sites_processed} smrs={summary.smr_designs} "
                f"rows={summary.ranking_rows} verdicts={summary.verdict_rows} "
                f"composites={summary.composite_rows} "
                f"excluded={summary.excluded_pairs}"
            ),
        )
    )


__all__ = [
    "check_code_coverage",
    "open_scoring_run",
    "write_scoring_audit",
]
