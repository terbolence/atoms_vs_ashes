# man_hours: 1.5
"""Safety-floor evaluator on top of the hard E-code expressions.

For every ``fail_condition`` with ``action: exclude`` AND a declared
``pass_mark``, this module emits a synthetic ``FailEvaluation`` whenever
the criterion's evaluated 0–10 ranking score is strictly below the floor
**and the hard expression did not already trigger**. The synthetic
verdict reuses the existing ``ScreeningVerdict`` plumbing — no schema
changes — and carries ``code = f"{E-code}:floor"`` so audits distinguish
the two paths.

The mechanism is documented in
``report/methodology/exclusionary_floors.md`` and the related test
suite ``tests/scoring/test_exclusionary_floors_doc.py``.
"""

from __future__ import annotations

from typing import Iterable

from atoms_vs_ashes.scoring.bands import BandResult
from atoms_vs_ashes.scoring.exclusionary import FailEvaluation
from atoms_vs_ashes.scoring.rubric import Criterion, FailCondition

FLOOR_SUFFIX = ":floor"


def is_floor_code(code: str) -> bool:
    """Return True for codes emitted by this evaluator (``E1:floor`` etc.)."""
    return code.endswith(FLOOR_SUFFIX)


def base_code(code: str) -> str:
    """Strip the ``:floor`` suffix if present (idempotent)."""
    if is_floor_code(code):
        return code[: -len(FLOOR_SUFFIX)]
    return code


def floor_code(code: str) -> str:
    """Return the floored form of ``code`` (idempotent)."""
    if is_floor_code(code):
        return code
    return f"{code}{FLOOR_SUFFIX}"


def evaluate_safety_floor(
    criterion: Criterion,
    *,
    band_result: BandResult | None,
    hard_evaluations: Iterable[FailEvaluation],
) -> list[FailEvaluation]:
    """Return synthetic floor verdicts for ``criterion``.

    A floor verdict is appended only when:

    1. the criterion has at least one ``action: exclude`` fail condition
       with a numeric ``pass_mark`` declared,
    2. a band score is available (``band_result is not None``),
    3. the score is strictly below the floor, and
    4. the corresponding hard E-code expression did **not** already
       trigger (avoids double-counting the same site).

    Returns an empty list if any of those checks fail.
    """
    pass_marks = criterion.exclusion_pass_marks
    if not pass_marks or band_result is None:
        return []

    score = float(band_result.score)
    triggered_codes = {
        ev.code for ev in hard_evaluations if ev.matched is True
    }

    out: list[FailEvaluation] = []
    for fc in criterion.fail_conditions:
        if fc.action != "exclude" or fc.pass_mark is None:
            continue
        if fc.code in triggered_codes:
            continue
        if score >= float(fc.pass_mark):
            continue
        out.append(_floor_evaluation(criterion=criterion, fc=fc, score=score))
    return out


def _floor_evaluation(
    *,
    criterion: Criterion,
    fc: FailCondition,
    score: float,
) -> FailEvaluation:
    descriptor = (
        f"Safety floor: 0-10 ranking score {score:.1f} < pass_mark "
        f"{float(fc.pass_mark):.1f} (anchor E-code {fc.code})."
    )
    justification = f"TRIGGERED: {floor_code(fc.code)} — {descriptor}"
    return FailEvaluation(
        criterion_id=criterion.criterion_id,
        code=floor_code(fc.code),
        verdict="fail",
        matched=True,
        justification=justification,
        measured_value={
            "score_0_10": round(score, 4),
            "pass_mark": float(fc.pass_mark),
            "anchor_code": fc.code,
        },
        threshold=f"score_0_10 >= {float(fc.pass_mark):.1f}",
    )
