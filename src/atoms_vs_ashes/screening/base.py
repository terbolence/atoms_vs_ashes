# man_hours: 5.0
"""Base class and registry for screening checks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.models import AuditLog, ScreeningVerdict
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)


@dataclass
class CheckSummary:
    """Aggregated results returned after a screening check completes."""

    criterion_id: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    inconclusive: int = 0
    caution: int = 0
    detail: dict[str, Any] = field(default_factory=dict)


class ScreeningCheck(ABC):
    """Protocol that every screening check must follow.

    Subclasses implement ``evaluate`` which yields per-site-per-SMR verdicts.
    The ``run`` method handles the write-to-DB + audit boilerplate.
    """

    criterion_id: str
    phase: str = "screening"

    @abstractmethod
    def evaluate(
        self,
        session: Session,
        settings: Settings,
        run_id: str,
    ) -> list[ScreeningVerdict]:
        """Produce screening verdicts for all relevant sites × SMR designs."""
        ...

    def run(
        self,
        session: Session,
        settings: Settings,
        run_id: str,
    ) -> CheckSummary:
        """Execute the check, persist results, and return a summary."""
        log.info("screening_check_start", criterion=self.criterion_id, run_id=run_id)

        verdicts = self.evaluate(session, settings, run_id)

        for v in verdicts:
            session.merge(v)

        session.add(
            AuditLog(
                operation="screening",
                table_name="screening_verdicts",
                run_id=run_id,
                message=(
                    f"BF check {self.criterion_id}: "
                    f"{len(verdicts)} verdicts written"
                ),
            )
        )

        summary = CheckSummary(criterion_id=self.criterion_id, total=len(verdicts))
        for v in verdicts:
            if v.verdict == "pass":
                summary.passed += 1
            elif v.verdict == "fail":
                summary.failed += 1
            elif v.verdict == "caution":
                summary.caution += 1
            else:
                summary.inconclusive += 1

        log.info(
            "screening_check_done",
            criterion=self.criterion_id,
            total=summary.total,
            passed=summary.passed,
            failed=summary.failed,
            inconclusive=summary.inconclusive,
            caution=summary.caution,
        )
        return summary


# ---------------------------------------------------------------------------
# Registry — checks register themselves on import
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, type[ScreeningCheck]] = {}


def register_check(cls: type[ScreeningCheck]) -> type[ScreeningCheck]:
    """Class decorator that registers a screening check by criterion_id."""
    _REGISTRY[cls.criterion_id] = cls
    return cls


def get_check(criterion_id: str) -> ScreeningCheck:
    """Instantiate a registered check by its criterion ID."""
    cls = _REGISTRY.get(criterion_id)
    if cls is None:
        raise KeyError(
            f"No screening check registered for '{criterion_id}'. "
            f"Available: {sorted(_REGISTRY)}"
        )
    return cls()


def all_checks() -> list[ScreeningCheck]:
    """Return instances of every registered screening check."""
    return [cls() for cls in _REGISTRY.values()]
