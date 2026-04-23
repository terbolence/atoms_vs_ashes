# man_hours: 2.0
"""A-code avoidance evaluator.

Writes ``ScreeningVerdict`` rows with ``phase = 'avoidance'`` for
every rubric ``fail_condition`` whose ``action`` is
``avoidance_penalty``. A triggered avoidance does **not** remove the
site from the candidate set — the engine simply flags it so the
ranking stage can apply the scoring penalty mandated in
``report/sites_evaluation/01_framework.md``.

Shares :mod:`exclusionary` for expression evaluation + verdict
construction; the only difference is the phase label and the
``caution`` verdict used for flagged-but-not-failed conditions (e.g.
HI-07 EMI).
"""

from __future__ import annotations

import uuid
from typing import Literal

from atoms_vs_ashes.db.models import ScreeningVerdict
from atoms_vs_ashes.scoring._codes import (
    AVOIDANCE_CODE_NAMES,
    ScreeningCode,
    codes_for_criterion,
)
from atoms_vs_ashes.scoring.exclusionary import (
    FailEvaluation,
    build_verdict,
    evaluate_fail_conditions,
)
from atoms_vs_ashes.scoring.rubric import Criterion


def _promote_caution(e: FailEvaluation) -> FailEvaluation:
    """Avoidance hits are 'caution' not 'fail' — site stays eligible."""
    if e.verdict == "fail":
        return FailEvaluation(
            criterion_id=e.criterion_id,
            code=e.code,
            verdict="caution",
            matched=e.matched,
            justification=e.justification.replace("TRIGGERED", "AVOIDANCE_FLAGGED"),
            measured_value=e.measured_value,
            threshold=e.threshold,
        )
    return e


def evaluate_avoidance_for_site(
    criterion: Criterion,
    context: dict[str, object],
    *,
    site_id: uuid.UUID,
    smr_key: str,
    run_id: str,
    confidence: str,
    data_sources: list[str],
) -> list[ScreeningVerdict]:
    """Return ``ScreeningVerdict`` rows for the A-codes on ``criterion``."""
    evaluations = [
        _promote_caution(e)
        for e in evaluate_fail_conditions(
            criterion, dict(context), action="avoidance_penalty"
        )
    ]
    return [
        build_verdict(
            site_id=site_id,
            smr_key=smr_key,
            run_id=run_id,
            criterion=criterion,
            evaluation=e,
            phase="avoidance",
            confidence=confidence,
            data_sources=data_sources,
            prompt_key=e.code if e.code in AVOIDANCE_CODE_NAMES else None,
        )
        for e in evaluations
    ]


def expected_avoidance_codes(criterion: Criterion) -> tuple[ScreeningCode, ...]:
    """Catalog A-codes expected to be anchored on ``criterion``."""
    return codes_for_criterion(criterion.criterion_id, action="avoidance_penalty")


# ---------------------------------------------------------------------------
# Summary helpers
# ---------------------------------------------------------------------------


VerdictLabel = Literal["pass", "fail", "caution", "inconclusive"]


def count_by_verdict(verdicts: list[ScreeningVerdict]) -> dict[VerdictLabel, int]:
    """Small utility used by the engine's progress log."""
    out: dict[VerdictLabel, int] = {
        "pass": 0,
        "fail": 0,
        "caution": 0,
        "inconclusive": 0,
    }
    for v in verdicts:
        label = v.verdict if v.verdict in out else "inconclusive"
        out[label] += 1  # type: ignore[index]
    return out
