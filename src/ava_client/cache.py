"""Thread-safe cache for connector results shared between Phase 2 workers."""

from __future__ import annotations

import threading
from typing import Any

from ava_client.resolver import ResolvedSite


class SiteDataCache:
    """Keyed store for connector and analysis results.

    Workers write per-site, per-source data.  The main thread reads
    after all workers have finished (no concurrent read/write expected
    in practice, but the lock makes it safe regardless).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data: dict[str, dict[str, Any]] = {}
        self._snapshots: dict[str, str] = {}

    def _site_key(self, site: ResolvedSite) -> str:
        return f"{site.country}:{site.name}"

    def put(self, site: ResolvedSite, source: str, value: Any) -> None:
        with self._lock:
            key = self._site_key(site)
            self._data.setdefault(key, {})[source] = value

    def get(self, site: ResolvedSite, source: str) -> Any | None:
        with self._lock:
            return self._data.get(self._site_key(site), {}).get(source)

    def put_snapshot(self, filename: str, content: str) -> None:
        with self._lock:
            self._snapshots[filename] = content

    def get_snapshot(self, filename: str) -> str | None:
        with self._lock:
            return self._snapshots.get(filename)

    @property
    def all_snapshots(self) -> dict[str, str]:
        with self._lock:
            return dict(self._snapshots)
