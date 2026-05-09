# man_hours: 1.4
"""Body of the ``score run`` CLI command.

Pulled out of :mod:`atoms_vs_ashes.scoring._cli` so the CLI shell stays
under the per-file size cap. The two public helpers
:func:`execute_score_run` and :func:`emit_cancelled_payload` /
:func:`emit_summary_payload` are stable seams for the click command and
for tests.
"""

from __future__ import annotations

import json
from typing import Any

import click
from sqlalchemy import select

from atoms_vs_ashes.db.models import SmrDesign
from atoms_vs_ashes.runprofile.loader import load_run_profile
from atoms_vs_ashes.runtime.cancellation import CancellationRequested
from atoms_vs_ashes.runtime.heartbeat import HeartbeatWriter
from atoms_vs_ashes.runtime.scope import scope_from_run_profile
from atoms_vs_ashes.scoring._smr_bundles import smr_aware_criteria_bundles
from atoms_vs_ashes.scoring.engine import ScoringSummary, run_scoring


def apply_profile_scope_to_sensitivity_cfg(
    cfg: Any, profile_path: str, *, session: Any, default_rubric_dir: str
) -> None:
    """Hydrate ``cfg.scope`` from ``profile_path`` (in place).

    Mirrors the scope-fix done for ``score run --profile`` so the
    sensitivity suite operates on the same in-scope subset. When the
    caller did not override ``--rubric-dir`` away from the default, the
    profile's ``spec_dir`` wins so the suite uses the same rubric set
    that the GUI exported.
    """
    loaded = load_run_profile(profile_path, session=session)
    cfg.scope = scope_from_run_profile(loaded.profile)
    if cfg.rubric_dir == default_rubric_dir:
        cfg.rubric_dir = loaded.profile.spec_dir


def _assert_basis_populated(
    bundle: dict, basis: str | None, *, where: str
) -> None:
    """Raise NotImplementedError if the requested basis is not populated.

    Loud-fail guard for the SP-B EPRI-weights mechanism (FB-LL-09 family):
    when an operator passes ``--weight-basis epri`` but no criterion in the
    bundle carries ``weight_factors['epri']``, fall through to baseline
    silently is exactly the failure mode FB-LL-09 was promoted to prevent.
    """
    if basis in (None, "baseline"):
        return
    populated = any(
        (c.weight_factors or {}).get(basis) is not None for c in bundle.values()
    )
    if not populated:
        raise NotImplementedError(
            f"weight_basis '{basis}' not populated on any criterion in {where}; "
            "the canonical source document has not yet been threaded into "
            "config/scoring_rubrics/. SP-B records the swap protocol in "
            "report/sites_evaluation/02_master_weights.md."
        )


def execute_score_run(
    *,
    session: Any,
    weight_profile: str,
    weight_basis: str | None = None,
    rubric_dir: str,
    profile_path: str | None,
    run_id: str | None,
    token: Any,
    hb: HeartbeatWriter,
) -> ScoringSummary:
    """Run the engine, optionally hydrating SMR-aware bundles from a YAML.

    When ``profile_path`` is provided the run profile's
    ``scope.smr_keys`` / ``scope.countries`` is honoured: the SMR
    bundle build is restricted to scope-allowed designs and the same
    scope is forwarded to ``run_scoring`` so the engine itself loads
    only the in-scope sites and SMRs.
    """
    if profile_path is not None:
        loaded = load_run_profile(profile_path, session=session)
        runscope = scope_from_run_profile(loaded.profile)
        smrs = list(
            session.execute(
                runscope.apply_to_smrs(
                    select(SmrDesign).order_by(SmrDesign.smr_key)
                )
            ).scalars()
        )
        smr_bundles = smr_aware_criteria_bundles(
            loaded.template_bundle, loaded.profile, smrs
        )
        from atoms_vs_ashes.scoring.rubric import weight_normalisation

        first_bundle = next(iter(smr_bundles.values()))
        _assert_basis_populated(
            first_bundle, weight_basis, where=loaded.profile.spec_dir
        )
        w = weight_normalisation(
            first_bundle, profile=weight_profile, basis=weight_basis
        )
        return run_scoring(
            session, rubric_dir=loaded.profile.spec_dir,
            weight_profile=weight_profile, run_id=run_id,
            cancellation=token, heartbeat=hb,
            smr_bundles=smr_bundles, weights=w,
            threshold_overrides=dict(loaded.profile.fail_thresholds),
            scope=runscope,
        )
    if weight_basis not in (None, "baseline"):
        from atoms_vs_ashes.scoring.rubric import (
            load_rubric_bundle, weight_normalisation,
        )

        bundle = load_rubric_bundle(rubric_dir)
        _assert_basis_populated(bundle, weight_basis, where=rubric_dir)
        weights = weight_normalisation(
            bundle, profile=weight_profile, basis=weight_basis
        )
        return run_scoring(
            session, rubric_dir=rubric_dir, weight_profile=weight_profile,
            bundle=bundle, weights=weights,
            run_id=run_id, cancellation=token, heartbeat=hb,
        )
    return run_scoring(
        session, rubric_dir=rubric_dir, weight_profile=weight_profile,
        run_id=run_id, cancellation=token, heartbeat=hb,
    )


def emit_cancelled_payload(
    run_id: str | None, exc: CancellationRequested, *, kind: str
) -> None:
    """Emit a clean ``{"status": "cancelled"}`` JSON line."""
    note = (
        f"session_scope rolled back; no partial {kind} rows were "
        "committed to the database."
    )
    click.echo(
        json.dumps(
            {
                "run_id": run_id,
                "status": "cancelled",
                "reason": exc.reason or "requested",
                "note": note,
            },
            indent=2,
        )
    )


def emit_summary_payload(summary: ScoringSummary) -> None:
    """Emit the success summary for ``score run``."""
    click.echo(
        json.dumps(
            {
                "run_id": summary.run_id,
                "weight_profile": summary.weight_profile,
                "sites_processed": summary.sites_processed,
                "smr_designs": summary.smr_designs,
                "verdict_rows": summary.verdict_rows,
                "ranking_rows": summary.ranking_rows,
                "composite_rows": summary.composite_rows,
                "excluded_pairs": summary.excluded_pairs,
                "warnings": summary.warnings,
            },
            indent=2, default=str,
        )
    )


__all__ = [
    "emit_cancelled_payload",
    "emit_summary_payload",
    "execute_score_run",
]
