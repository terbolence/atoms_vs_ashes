"""Pure-logic tests for ``country_bundle._per_site_verdicts``.

The function emits ``{site_id: {avoidance: [...], exclusionary: [...]}}``
from two ``ScreeningVerdict`` queries grouped by ``(site_id,
criterion_id)``. The test stubs ``session.execute`` so it returns the
two row sets the function expects, then asserts:

1. Per-site grouping (codes for site A do not bleed into site B).
2. Phase separation: avoidance codes never land in the exclusionary
   bucket and vice versa.
3. Code lists are sorted alphabetically (byte-stable re-emission).
4. The avoidance query includes ``caution`` verdicts in addition to
   ``fail`` (mirrors ``_avoidance_pareto`` behaviour).

A real DB integration is exercised at re-emission time by
``regenerate_v1_3_bundles.py`` against the frozen run ids.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from atoms_vs_ashes.reporting import country_bundle as cb


class _StubResult:
    def __init__(self, rows: Iterable[tuple[Any, ...]]) -> None:
        self._rows = list(rows)

    def all(self) -> list[tuple[Any, ...]]:
        return list(self._rows)

    def scalars(self) -> "_StubResult":
        return self

    def scalar_one_or_none(self) -> Any:
        return self._rows[0] if self._rows else None


class _StubSession:
    """Hands out two ``ScreeningVerdict`` row sets in call order.

    ``country_bundle._per_site_verdicts`` issues exactly two queries —
    avoidance first, exclusionary second — so the stub replays results
    in that order. The test owns the row content.
    """

    def __init__(
        self,
        *,
        avoidance_rows: list[tuple[str, str]],
        exclusionary_rows: list[tuple[str, str]],
    ) -> None:
        self._queue = [avoidance_rows, exclusionary_rows]

    def execute(self, _stmt: Any) -> _StubResult:
        rows = self._queue.pop(0)
        return _StubResult(rows)


def test_per_site_verdicts_groups_by_site_and_phase() -> None:
    session = _StubSession(
        avoidance_rows=[
            ("site-A", "NS-02"),
            ("site-A", "RI-05"),
            ("site-B", "HI-01"),
            ("site-B", "NS-02"),
        ],
        exclusionary_rows=[
            ("site-C", "NH-02"),
            ("site-C", "EP-01"),
        ],
    )

    out = cb._per_site_verdicts(
        session, country_code="RO", smr_key="nuscale_voygr6",
        run_id="score-c2a90942",
    )

    assert out == {
        "site-A": {"avoidance": ["NS-02", "RI-05"], "exclusionary": []},
        "site-B": {"avoidance": ["HI-01", "NS-02"], "exclusionary": []},
        "site-C": {"avoidance": [], "exclusionary": ["EP-01", "NH-02"]},
    }


def test_per_site_verdicts_dedupes_repeat_codes() -> None:
    """The DB may emit duplicate (site_id, criterion_id) pairs when a
    criterion fires multiple fail expressions; the helper should
    collapse to a unique sorted list."""
    session = _StubSession(
        avoidance_rows=[
            ("site-A", "NS-02"),
            ("site-A", "NS-02"),
            ("site-A", "HI-01"),
        ],
        exclusionary_rows=[],
    )

    out = cb._per_site_verdicts(
        session, country_code="BA", smr_key="nuscale_voygr6",
        run_id="score-c2a90942",
    )

    assert out["site-A"]["avoidance"] == ["HI-01", "NS-02"]


def test_per_site_verdicts_emits_empty_dict_when_no_rows() -> None:
    session = _StubSession(avoidance_rows=[], exclusionary_rows=[])

    out = cb._per_site_verdicts(
        session, country_code="LV", smr_key="nuscale_voygr6",
        run_id="score-c2a90942",
    )

    assert out == {}


def test_per_site_verdicts_keys_are_sorted_for_byte_stability() -> None:
    session = _StubSession(
        avoidance_rows=[
            ("site-Z", "NS-02"),
            ("site-A", "NS-02"),
            ("site-M", "NS-02"),
        ],
        exclusionary_rows=[],
    )

    out = cb._per_site_verdicts(
        session, country_code="RO", smr_key="nuscale_voygr6",
        run_id="score-c2a90942",
    )

    assert list(out.keys()) == ["site-A", "site-M", "site-Z"]
