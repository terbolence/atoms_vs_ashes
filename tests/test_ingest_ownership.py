"""Unit tests for ownership ingestion helpers (no DB required)."""

from atoms_vs_ashes.ingest.ownership import _safe_float, _str_or_none


def test_safe_float():
    assert _safe_float("100") == 100.0
    assert _safe_float("50.5") == 50.5
    assert _safe_float(None) is None
    assert _safe_float("--") is None
    assert _safe_float("") is None


def test_str_or_none():
    assert _str_or_none("hello") == "hello"
    assert _str_or_none("  hello  ") == "hello"
    assert _str_or_none(None) is None
    assert _str_or_none("--") is None
    assert _str_or_none("") is None
    assert _str_or_none("nan") is None
    assert _str_or_none("NaN") is None
