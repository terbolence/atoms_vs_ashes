# man_hours: 3.0
"""E-code exclusionary evaluator.

For every criterion × site × SMR, walks the ``fail_conditions`` with
``action == 'exclude'`` (E1–E9) and writes a ``ScreeningVerdict``
row with ``phase = 'exclusionary'``. Caller is responsible for
committing the session.

The shared ``evaluate_one`` helper returns a verdict tuple so the
avoidance module can reuse the plumbing with a different phase label
(see :mod:`atoms_vs_ashes.scoring.avoidance`).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any, Literal

from atoms_vs_ashes.db.models import ScreeningVerdict
from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring._codes import (
    EXCLUSIONARY_CODE_NAMES,
    ScreeningCode,
    codes_for_criterion,
)
from atoms_vs_ashes.scoring.bands import BandResult, safe_eval
from atoms_vs_ashes.scoring.rubric import Criterion, FailCondition

log = get_logger(__name__)


@dataclass
class FailEvaluation:
    """Result of evaluating a single ``fail_condition``."""

    criterion_id: str
    code: str
    verdict: Literal["pass", "fail", "inconclusive"]
    matched: bool | None
    justification: str
    measured_value: dict[str, Any]
    threshold: str


def _serialise_measured(context: dict[str, Any], fc: FailCondition) -> dict[str, Any]:
    """Extract the subset of ``context`` keys referenced in the expr."""
    subset: dict[str, Any] = {}
    expr = fc.condition_expr
    for key, val in context.items():
        if key in expr:
            subset[key] = _jsonable(val)
    return subset


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


def _verdict_for_fail(
    fc: FailCondition,
    matched: bool | None,
) -> Literal["pass", "fail", "inconclusive"]:
    """Convert the expr truthiness into a verdict label."""
    if matched is True:
        return "fail"
    if matched is False:
        return "pass"
    return "inconclusive"


def evaluate_fail_conditions(
    criterion: Criterion,
    context: dict[str, Any],
    *,
    action: Literal["exclude", "avoidance_penalty"],
) -> list[FailEvaluation]:
    """Evaluate every fail_condition with matching ``action``."""
    out: list[FailEvaluation] = []
    for fc in criterion.fail_conditions:
        if fc.action != action:
            continue
        matched = safe_eval(fc.condition_expr, context)
        verdict = _verdict_for_fail(fc, matched)
        out.append(
            FailEvaluation(
                criterion_id=criterion.criterion_id,
                code=fc.code,
                verdict=verdict,
                matched=matched,
                justification=_justification_text(fc, matched),
                measured_value=_serialise_measured(context, fc),
                threshold=fc.descriptor or fc.condition_expr,
            )
        )
    return out


def _justification_text(fc: FailCondition, matched: bool | None) -> str:
    if matched is True:
        prefix = "TRIGGERED"
    elif matched is False:
        prefix = "not_triggered"
    else:
        prefix = "inconclusive"
    desc = fc.descriptor or fc.condition_expr
    return f"{prefix}: {fc.code} — {desc}"


def build_verdict(
    *,
    site_id: uuid.UUID,
    smr_key: str,
    run_id: str,
    criterion: Criterion,
    evaluation: FailEvaluation,
    phase: str,
    confidence: str,
    data_sources: list[str],
    prompt_key: str | None = None,
) -> ScreeningVerdict:
    """Construct a ``ScreeningVerdict`` row from a ``FailEvaluation``.

    Kept as a shared helper so both exclusionary and avoidance
    evaluators persist identical row shapes.
    """
    return ScreeningVerdict(
        site_id=site_id,
        smr_key=smr_key,
        criterion_id=criterion.criterion_id,
        phase=phase,
        prompt_key=prompt_key,
        verdict=evaluation.verdict,
        measured_value=json.dumps(evaluation.measured_value, sort_keys=True, default=str),
        threshold=evaluation.threshold,
        justification=evaluation.justification,
        confidence=confidence,
        data_sources=data_sources or None,
        run_id=run_id,
    )


def evaluate_exclusionary_for_site(
    criterion: Criterion,
    context: dict[str, Any],
    *,
    site_id: uuid.UUID,
    smr_key: str,
    run_id: str,
    confidence: str,
    data_sources: list[str],
    band_result: BandResult | None = None,
) -> list[ScreeningVerdict]:
    """Return ``ScreeningVerdict`` rows for the E-codes on ``criterion``.

    Every verdict carries ``prompt_key = code`` so the
    ``uq_verdict_site_smr_criterion_prompt_run`` unique constraint fully
    disambiguates the row even when multiple E-codes live on the same
    criterion (e.g. E5 + E6 on NH-05).

    When ``band_result`` is supplied (the criterion was evaluated as part
    of the ranking phase), the safety-floor evaluator runs in addition
    to the hard ``condition_expr`` check and may emit synthetic
    ``<E-code>:floor`` verdicts. See
    :mod:`atoms_vs_ashes.scoring._safety_floor`.

    Returns an empty list when the criterion has no ``action == 'exclude'``
    fail_conditions.
    """
    # Deferred import to avoid an exclusionary <-> _safety_floor module cycle
    # (the floor module needs FailEvaluation defined above).
    from atoms_vs_ashes.scoring._safety_floor import evaluate_safety_floor

    evaluations = evaluate_fail_conditions(criterion, context, action="exclude")
    if band_result is not None:
        evaluations.extend(
            evaluate_safety_floor(
                criterion,
                band_result=band_result,
                hard_evaluations=evaluations,
            )
        )
    return [
        build_verdict(
            site_id=site_id,
            smr_key=smr_key,
            run_id=run_id,
            criterion=criterion,
            evaluation=e,
            phase="exclusionary",
            confidence=confidence,
            data_sources=data_sources,
            prompt_key=_prompt_key_for(e.code),
        )
        for e in evaluations
    ]


def _prompt_key_for(code: str) -> str | None:
    """Return the ``prompt_key`` to stamp on a verdict for ``code``.

    Catalog E-codes (E1..E9 + ``project_wind_envelope``) use the code
    verbatim. Synthetic floor codes (``E1:floor`` etc.) use the floored
    form so they remain distinct from the hard-fail row in the
    ``uq_verdict_site_smr_criterion_prompt_run`` unique constraint.
    Anything else returns ``None`` (legacy behaviour).
    """
    from atoms_vs_ashes.scoring._safety_floor import base_code, is_floor_code

    if is_floor_code(code):
        return code if base_code(code) in EXCLUSIONARY_CODE_NAMES else None
    return code if code in EXCLUSIONARY_CODE_NAMES else None


def expected_exclusionary_codes(criterion: Criterion) -> tuple[ScreeningCode, ...]:
    """Catalog E-codes expected to be anchored on ``criterion``.

    Used by the engine to detect rubric drift (e.g. E4 removed from
    NH-07 accidentally). Returns an empty tuple for criteria with no
    catalog-anchored E-code.
    """
    return codes_for_criterion(criterion.criterion_id, action="exclude")
