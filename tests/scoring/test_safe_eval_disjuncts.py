# man_hours: 0.4
"""Disjunct-level error isolation in :func:`safe_eval`.

Regression for the bug diagnosed during the May 2026 conformity assessment:
a rubric of the shape ``"x > N or (x is null and search_completed == true)"``
was returning ``None`` (= "band did not match") whenever ``x`` was ``None``
because the single ``eval`` over the whole expression raised ``TypeError``
on the left disjunct and the exception swallowed the entire condition.

The fix walks the AST in :func:`safe_eval` and evaluates top-level ``Or`` /
``And`` operands independently so an error in one operand cannot poison the
result of the others. Per the plan:

- ``or`` returns ``True`` as soon as any disjunct evaluates ``True``.
- ``and`` returns ``True`` only when all conjuncts evaluate ``True``;
  an indeterminate conjunct (``TypeError`` / ``NameError``) counts as
  ``False`` so the AND is fail-closed.
"""

from __future__ import annotations

from atoms_vs_ashes.scoring.bands import safe_eval


class TestOrShortCircuitsErroringDisjunct:
    """The Or operator must reach the right-hand True disjunct even when the
    left raises ``TypeError`` on a ``None`` operand."""

    def test_or_with_typeerror_left_and_true_right(self) -> None:
        assert safe_eval("a > 5 or b == true", {"a": None, "b": True}) is True

    def test_sp_f_sentinel_pattern(self) -> None:
        """The HI-02 / HI-04 / HI-05 / HI-08 favourable-band shape."""
        ctx = {"a": None, "b": True}
        assert safe_eval("a > 5 or (a is null and b == true)", ctx) is True

    def test_or_with_sentinel_pattern_inverted_order(self) -> None:
        """Reordering disjuncts must not change the outcome (P0-3 belt and braces)."""
        ctx = {"a": None, "b": True}
        assert safe_eval("(a is null and b == true) or a > 5", ctx) is True

    def test_or_with_all_false_returns_false(self) -> None:
        ctx = {"a": 3, "b": False}
        assert safe_eval("a > 5 or b == true", ctx) is False

    def test_or_with_all_indeterminate_returns_none(self) -> None:
        ctx = {"a": None, "b": None}
        assert safe_eval("a > 5 or b > 5", ctx) is None


class TestAndIsFailClosed:
    """The And operator must return False as soon as any conjunct cannot be
    confirmed True (including indeterminate operands)."""

    def test_and_with_typeerror_left_and_true_right_is_false(self) -> None:
        ctx = {"a": None, "b": True}
        assert safe_eval("a > 5 and (a is null or b == true)", ctx) is False

    def test_and_with_all_true_is_true(self) -> None:
        ctx = {"a": 10, "b": True}
        assert safe_eval("a > 5 and b == true", ctx) is True

    def test_and_with_explicit_false_is_false(self) -> None:
        ctx = {"a": 10, "b": False}
        assert safe_eval("a > 5 and b == true", ctx) is False


class TestSingleNodeBehaviourUnchanged:
    """The single-comparison and the ``default`` sentinel paths must not regress."""

    def test_single_comparison_with_none_returns_none(self) -> None:
        assert safe_eval("a > 5", {"a": None}) is None

    def test_single_comparison_with_value(self) -> None:
        assert safe_eval("a > 5", {"a": 10}) is True
        assert safe_eval("a > 5", {"a": 1}) is False

    def test_default_sentinel(self) -> None:
        assert safe_eval("default", {}) is True
        assert safe_eval("  default  ", {}) is True

    def test_syntax_error_returns_none(self) -> None:
        assert safe_eval("a >> > b", {"a": 1, "b": 2}) is None


class TestNestedBoolOp:
    """Nested ``or`` / ``and`` must still isolate erroring branches."""

    def test_nested_or_within_and(self) -> None:
        ctx = {"a": 10, "b": None, "c": True}
        assert safe_eval("a > 5 and (b > 5 or c == true)", ctx) is True

    def test_nested_and_within_or(self) -> None:
        ctx = {"a": None, "b": True, "c": True}
        expr = "a > 5 or (a is null and b == true and c == true)"
        assert safe_eval(expr, ctx) is True

    def test_nested_or_all_indeterminate_under_and(self) -> None:
        ctx = {"a": 10, "b": None, "c": None}
        assert safe_eval("a > 5 and (b > 5 or c > 5)", ctx) is False
