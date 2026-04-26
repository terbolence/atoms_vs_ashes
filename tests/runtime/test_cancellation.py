# man_hours: 0.25
"""Cancellation token semantics."""

from __future__ import annotations

import pytest

from atoms_vs_ashes.runtime.cancellation import (
    CancellationRequested,
    CancellationToken,
)


def test_default_token_is_not_cancelled() -> None:
    token = CancellationToken()
    assert token.is_cancelled is False
    token.raise_if_cancelled()


def test_cancel_then_raise() -> None:
    token = CancellationToken()
    token.cancel(reason="user_clicked_stop")
    assert token.is_cancelled is True
    with pytest.raises(CancellationRequested) as exc:
        token.raise_if_cancelled()
    assert exc.value.reason == "user_clicked_stop"


def test_cancel_is_idempotent() -> None:
    token = CancellationToken()
    token.cancel(reason="first")
    token.cancel(reason="second")
    assert token.reason == "first"


def test_preset_reason_in_constructor_arms_token() -> None:
    token = CancellationToken(reason="started_already_cancelled")
    assert token.is_cancelled is True
    with pytest.raises(CancellationRequested):
        token.raise_if_cancelled()
