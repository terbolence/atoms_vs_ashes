# man_hours: 1.6
"""Unit coverage for the canonical DB profile resolver and the
GUI-side bootstrap that binds the engine to the active profile."""

from __future__ import annotations

import os
from unittest.mock import MagicMock

import pytest

from atoms_vs_ashes.db.profiles import (
    DB_PROFILES,
    DEFAULT_PROFILE,
    resolve_db_name,
)


def test_resolve_db_name_returns_canonical_for_each_known_profile():
    assert resolve_db_name("api") == "atoms_vs_ashes"
    assert resolve_db_name("llm") == "atoms_vs_ashes_llm"
    assert resolve_db_name("merged") == "atoms_vs_ashes_merged"


def test_default_profile_is_merged_after_cutover():
    assert DEFAULT_PROFILE == "merged"
    assert DB_PROFILES[DEFAULT_PROFILE] == "atoms_vs_ashes_merged"


def test_resolve_db_name_unknown_profile_raises_helpful_value_error():
    with pytest.raises(ValueError) as exc:
        resolve_db_name("typo")
    msg = str(exc.value)
    assert "typo" in msg
    assert "api" in msg and "merged" in msg and "llm" in msg


def _patch_engine(*, returned_row, monkeypatch):
    """Stub ``create_engine`` and ``init_engine`` for the bootstrap path.

    Returns the bootstrap mock connection so the test can assert which
    statement was executed.
    """
    fake_conn = MagicMock()
    fake_result = MagicMock()
    fake_result.first.return_value = returned_row
    fake_conn.execute.return_value = fake_result

    from atoms_vs_ashes.db import engine as engine_mod

    init_calls: list[tuple] = []

    def fake_init_engine(settings=None):
        init_calls.append((settings,))
    monkeypatch.setattr(engine_mod, "init_engine", fake_init_engine)
    return fake_conn, init_calls


def test_init_engine_for_active_profile_falls_back_to_env_when_row_missing(
    monkeypatch,
):
    monkeypatch.setenv("POSTGRES_DB", "atoms_vs_ashes")
    _fake_conn, init_calls = _patch_engine(returned_row=None, monkeypatch=monkeypatch)

    from atoms_vs_ashes.db.engine import init_engine_for_active_profile

    resolved = init_engine_for_active_profile()
    assert resolved == "atoms_vs_ashes_merged"
    assert init_calls == [(None,)]
    assert os.environ["POSTGRES_DB"] == "atoms_vs_ashes_merged"


def test_init_engine_for_active_profile_ignores_non_merged_active_profile(
    monkeypatch,
):
    monkeypatch.setenv("POSTGRES_DB", "atoms_vs_ashes")
    _fake_conn, init_calls = _patch_engine(
        returned_row=({"db_profile": "api"},), monkeypatch=monkeypatch,
    )

    from atoms_vs_ashes.db.engine import init_engine_for_active_profile

    resolved = init_engine_for_active_profile()
    assert resolved == "atoms_vs_ashes_merged"
    assert os.environ["POSTGRES_DB"] == "atoms_vs_ashes_merged"
    assert len(init_calls) == 1


def test_init_engine_for_active_profile_ignores_unknown_active_profile(
    monkeypatch,
):
    monkeypatch.setenv("POSTGRES_DB", "atoms_vs_ashes")
    _fake_conn, init_calls = _patch_engine(
        returned_row=({"db_profile": "ghost"},), monkeypatch=monkeypatch,
    )

    from atoms_vs_ashes.db.engine import init_engine_for_active_profile

    resolved = init_engine_for_active_profile()
    assert resolved == "atoms_vs_ashes_merged"
    assert init_calls == [(None,)]


def test_init_engine_for_active_profile_treats_db_error_as_fallback(
    monkeypatch,
):
    monkeypatch.setenv("POSTGRES_DB", "atoms_vs_ashes")
    from atoms_vs_ashes.db import engine as engine_mod

    init_calls: list[tuple] = []
    monkeypatch.setattr(
        engine_mod, "init_engine",
        lambda settings=None: init_calls.append((settings,)),
    )

    from atoms_vs_ashes.db.engine import init_engine_for_active_profile

    resolved = init_engine_for_active_profile()
    assert resolved == "atoms_vs_ashes_merged"
    assert init_calls == [(None,)]


def test_cli_default_db_profile_is_merged():
    from atoms_vs_ashes.cli import main

    db_param = next(p for p in main.params if p.name == "db_profile")
    assert db_param.default == "merged"
