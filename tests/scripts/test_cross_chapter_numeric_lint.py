# man_hours: 0.4
"""Slow-marked pytest wrapper for the cross-chapter numeric lint (FB-LL-06)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.mark.slow
def test_cross_chapter_numeric_lint_is_clean() -> None:
    """Fail when any canonical numeric fact has drifted across chapters.

    Run with ``pytest -m slow tests/scripts/test_cross_chapter_numeric_lint.py``
    or directly via ``python src/scripts/cross_chapter_numeric_lint.py
    --strict``.
    """
    from scripts.cross_chapter_numeric_lint import format_report, run_lint

    findings = run_lint()
    assert not findings, "\n" + format_report(findings)
