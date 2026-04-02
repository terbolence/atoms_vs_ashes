"""Per-API rate limiter using a threading semaphore and inter-request delay."""

from __future__ import annotations

import threading
import time


class ApiRateLimiter:
    """Thread-safe rate limiter scoped to a single external API.

    Parameters
    ----------
    name
        Human-readable label (e.g. ``"overpass"``).
    delay_s
        Minimum seconds between successive requests.
    max_concurrency
        Maximum parallel in-flight requests (semaphore slots).
    """

    def __init__(self, name: str, delay_s: float, max_concurrency: int = 1) -> None:
        self.name = name
        self._delay = delay_s
        self._sem = threading.Semaphore(max_concurrency)
        self._lock = threading.Lock()
        self._last_request: float = 0.0

    def wait(self) -> None:
        """Block until both semaphore and delay constraints are satisfied."""
        self._sem.acquire()
        try:
            with self._lock:
                elapsed = time.monotonic() - self._last_request
                remaining = self._delay - elapsed
                if remaining > 0:
                    time.sleep(remaining)
                self._last_request = time.monotonic()
        finally:
            self._sem.release()
