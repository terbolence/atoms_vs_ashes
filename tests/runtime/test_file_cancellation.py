# man_hours: 0.25
"""File-watching cancellation token + sigint handler glue."""

from __future__ import annotations

import signal
from pathlib import Path

import pytest

from atoms_vs_ashes.runtime.cancellation import (
    CancellationRequested,
    FileWatchedCancellationToken,
    install_sigint_handler,
)


def test_file_token_starts_disarmed(tmp_path: Path) -> None:
    sentinel = tmp_path / "cancel.flag"
    token = FileWatchedCancellationToken(sentinel_path=sentinel)
    assert token.is_cancelled is False


def test_file_token_trips_when_sentinel_appears(tmp_path: Path) -> None:
    sentinel = tmp_path / "cancel.flag"
    token = FileWatchedCancellationToken(sentinel_path=sentinel)
    sentinel.write_text("")
    assert token.is_cancelled is True
    with pytest.raises(CancellationRequested) as exc:
        token.raise_if_cancelled()
    assert "sentinel" in (exc.value.reason or "")


def test_file_token_without_sentinel_behaves_like_base() -> None:
    token = FileWatchedCancellationToken(sentinel_path=None)
    assert token.is_cancelled is False
    token.cancel(reason="programmatic")
    assert token.is_cancelled is True


def test_install_sigint_handler_restores_previous_handler() -> None:
    from atoms_vs_ashes.runtime.cancellation import CancellationToken

    token = CancellationToken()
    previous = signal.getsignal(signal.SIGINT)
    with install_sigint_handler(token):
        new = signal.getsignal(signal.SIGINT)
        assert new is not previous
    assert signal.getsignal(signal.SIGINT) is previous
