# man_hours: 4.0
"""Targeted threshold sensitivity — perturbs each user-controlled E/A code.

Implements §8 stage 3 (``targeted`` mode) of
``.cursor/plans/scoring_control_gui_872d4eb7.plan.md``: for every named
fail threshold the analyst can edit (every numeric
:class:`atoms_vs_ashes.criterion_spec.schema.FailConditionSpec`), this
driver

1. compiles a **baseline bundle** from the user's RunProfile,
2. shifts that single threshold by ``±pct`` (configurable list of
   percentages — typically ``[10, 25]``),
3. recompiles the bundle with **only** that one override,
4. re-evaluates every scoped (site, SMR) pair against the new bundle
   reusing the cached metric contexts and band scores (bands never
   change in this mode), and
5. reports the membership delta of the surviving set vs. baseline plus
   the per-pair composite-score delta.

The dataclasses + small helpers live in
:mod:`._suite_threshold_targeted_helpers`; this module only orchestrates
the sweep so it stays under the project's 300-line file budget.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from sqlalchemy.orm import Session

from atoms_vs_ashes.criterion_spec.loader import TemplateBundle
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.runprofile.schema import RunProfile
from atoms_vs_ashes.scoring._suite_threshold import (
    _evaluate_pair,
    _load_sites,
    _load_smr_designs,
    _precompute_site_scaled,
)
from atoms_vs_ashes.scoring._suite_threshold_targeted_helpers import (
    TargetedThreshold,
    TargetedThresholdRow,
    TargetedThresholdSuiteResult,
    build_overrides,
    compile_for_profile,
    diff_results,
    list_targeted_thresholds,
    make_row,
    perturb_value,
)
from atoms_vs_ashes.scoring.composite import CompositeResult
from atoms_vs_ashes.scoring.rubric import Criterion

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from atoms_vs_ashes.runtime import RunScope

log = get_logger(__name__)


def _evaluate_all(
    sites,
    smrs,
    bundle: dict[str, Criterion],
    site_caches: dict,
    *,
    weights: dict[str, float],
    run_id: str,
) -> dict[tuple, CompositeResult]:
    out: dict[tuple, CompositeResult] = {}
    for site in sites:
        ctxs, values = site_caches[site.site_id]
        for smr in smrs:
            out[(site.site_id, smr.smr_key)] = _evaluate_pair(
                site=site,
                smr=smr,
                bundle=bundle,
                site_ctxs=ctxs,
                site_values=values,
                weights=weights,
                run_id=run_id,
            )
    return out


def _sweep_one_target(
    *,
    target: TargetedThreshold,
    pcts: tuple[float, ...],
    template_bundle: TemplateBundle,
    profile: RunProfile,
    sites,
    smrs,
    site_caches: dict,
    weights: dict[str, float],
    run_id: str,
    base_results: dict[tuple, CompositeResult],
    n_pairs: int,
    progress_cb,
) -> list[TargetedThresholdRow]:
    rows: list[TargetedThresholdRow] = []
    for pct in pcts:
        for direction in ("down", "up"):
            perturbed_value = perturb_value(target.base_value, pct, direction)
            overrides = build_overrides(
                profile, target.criterion_id, target.code, perturbed_value
            )
            try:
                perturbed_bundle = compile_for_profile(
                    template_bundle, profile, fail_thresholds=overrides
                )
            except ValueError as exc:
                log.warning(
                    "targeted_threshold_compile_skip",
                    criterion=target.criterion_id,
                    code=target.code,
                    pct=pct,
                    direction=direction,
                    reason=str(exc),
                )
                continue
            perturbed_results = _evaluate_all(
                sites, smrs, perturbed_bundle, site_caches,
                weights=weights, run_id=run_id,
            )
            added, removed, deltas = diff_results(base_results, perturbed_results)
            rows.append(
                make_row(
                    target,
                    pct,
                    direction,
                    perturbed_value,
                    added=added,
                    removed=removed,
                    deltas=deltas,
                    n_pairs=n_pairs,
                )
            )
            if progress_cb is not None:
                progress_cb(1)
    return rows


def run_targeted_threshold_sensitivity(  # noqa: PLR0913 - user-facing API
    session: Session,
    template_bundle: TemplateBundle,
    profile: RunProfile,
    *,
    weights: dict[str, float],
    run_id: str,
    pct_steps: Iterable[float] = (10.0, 25.0),
    scope: "RunScope | None" = None,
    progress_cb=None,
) -> TargetedThresholdSuiteResult:
    """Run the targeted-threshold sweep across every numeric E/A code.

    The baseline pass is evaluated once; subsequent passes reuse cached
    site contexts and band scores (only ``fail_conditions`` differ
    between bundles in this mode), so the cost scales as
    ``O(n_pairs * (1 + 2 * |pct_steps| * |targets|))``.
    """
    pcts = tuple(float(p) for p in pct_steps)
    targets = list_targeted_thresholds(template_bundle, profile)
    sites = _load_sites(session, scope=scope)
    smrs = _load_smr_designs(session, scope=scope)
    if not sites or not smrs or not targets:
        return TargetedThresholdSuiteResult(
            rows=[], targets=targets, pct_steps=pcts, n_pairs=0
        )

    base_bundle = compile_for_profile(
        template_bundle, profile, fail_thresholds=profile.fail_thresholds
    )
    site_caches = {
        site.site_id: _precompute_site_scaled(
            session, site, base_bundle, factor=1.0
        )
        for site in sites
    }
    base_results = _evaluate_all(
        sites, smrs, base_bundle, site_caches,
        weights=weights, run_id=run_id,
    )
    n_pairs = len(base_results)

    rows: list[TargetedThresholdRow] = []
    for target in targets:
        rows.extend(
            _sweep_one_target(
                target=target,
                pcts=pcts,
                template_bundle=template_bundle,
                profile=profile,
                sites=sites,
                smrs=smrs,
                site_caches=site_caches,
                weights=weights,
                run_id=run_id,
                base_results=base_results,
                n_pairs=n_pairs,
                progress_cb=progress_cb,
            )
        )
    log.info(
        "targeted_threshold_sensitivity_complete",
        rows=len(rows),
        targets=len(targets),
        pct_steps=pcts,
    )
    return TargetedThresholdSuiteResult(
        rows=rows, targets=targets, pct_steps=pcts, n_pairs=n_pairs
    )


__all__ = [
    "TargetedThreshold",
    "TargetedThresholdRow",
    "TargetedThresholdSuiteResult",
    "list_targeted_thresholds",
    "run_targeted_threshold_sensitivity",
]
