# man_hours: 1.0
"""Tests for LOC and token estimation helpers."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS = _ROOT / "src" / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _man_hours_metrics import (  # noqa: E402
    INPUT_TO_OUTPUT_RATIO,
    THINKING_FRACTION,
    estimate_tokens_from_chars,
    parse_cloc_languages,
    parse_cloc_sum,
    stats_for_paths,
)


def test_stats_for_paths_counts_lines_and_chars(tmp_path: Path) -> None:
    f = tmp_path / "a.py"
    f.write_text("line1\nline2\n", encoding="utf-8")
    st = stats_for_paths([f])
    assert st.files == 1
    assert st.lines == 2
    assert st.chars == len("line1\nline2\n")


def test_estimate_tokens_monotonic_with_corpus_size() -> None:
    small = estimate_tokens_from_chars({"python": 1000, "markdown": 0, "yaml": 0})
    large = estimate_tokens_from_chars({"python": 100_000, "markdown": 50_000, "yaml": 10_000})
    assert large.output_tokens > small.output_tokens
    assert large.input_tokens > small.input_tokens
    assert large.total_tokens > small.total_tokens


def test_estimate_tokens_thinking_fraction() -> None:
    est = estimate_tokens_from_chars({"python": 3600, "markdown": 0, "yaml": 0})
    assert est.output_tokens == 1000
    assert est.input_tokens == int(round(1000 * INPUT_TO_OUTPUT_RATIO))
    expected_think = int(round((est.input_tokens + est.output_tokens) * THINKING_FRACTION))
    assert est.thinking_tokens == expected_think


def test_parse_cloc_json() -> None:
    sample = {
        "header": {"cloc_version": "2.08", "n_files": 3},
        "Python": {"nFiles": 2, "blank": 10, "comment": 5, "code": 100},
        "SUM": {"nFiles": 2, "blank": 10, "comment": 5, "code": 100},
    }
    langs = parse_cloc_languages(sample)
    assert len(langs) == 1
    assert langs[0].language == "Python"
    assert langs[0].code == 100
    n, code, comment, blank = parse_cloc_sum(sample)
    assert (n, code, comment, blank) == (2, 100, 5, 10)


def test_collect_project_inventory_totals() -> None:
    if not (_ROOT / ".git").is_dir():
        pytest.skip("not a git checkout")
    from _man_hours_metrics import collect_project_inventory  # noqa: E402

    inv = collect_project_inventory(_ROOT)
    assert inv.prose.files > 100
    assert inv.prose.lines > 50_000
    assert inv.programs.lines > 50_000


def test_project_python_excludes_venv_test() -> None:
    """Regression: src/venv_test must not inflate application LOC."""
    if not (_ROOT / ".git").is_dir():
        pytest.skip("not a git checkout")
    from _man_hours_metrics import collect_python_metrics, measure_bucket  # noqa: E402

    venv_only = measure_bucket(_ROOT, "src/venv_test", ".py")
    if venv_only.files > 0:
        pytest.fail("venv_test .py files should not be measured via git-tracked paths")
    app = collect_python_metrics(_ROOT)["Application package"]
    assert 0 < app.lines < 500_000
