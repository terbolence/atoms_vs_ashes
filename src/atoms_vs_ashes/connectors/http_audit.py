# man_hours: 1.5
"""File-based HTTP audit logging shared across data connectors.

Each run writes paired JSON files under::

    logs/<subsystem>/<run_id>/requests/
    logs/<subsystem>/<run_id>/responses/

Sensitive query keys (e.g. ``securityToken``) are redacted in persisted
request payloads by default.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

_DEFAULT_REDACT_KEYS = frozenset({
    "securityToken",
    "security_token",
    "api_key",
    "apiKey",
    "password",
    "token",
})


def _redact_params(
    params: dict[str, str],
    extra_redact: frozenset[str] | None,
) -> dict[str, str]:
    keys = _DEFAULT_REDACT_KEYS | (extra_redact or frozenset())
    out: dict[str, str] = {}
    for k, v in params.items():
        if k in keys and v:
            out[k] = "***REDACTED***"
        else:
            out[k] = v
    return out


class ConnectorHttpAuditLogger:
    """Captures every HTTP GET exchange for offline debugging and compliance."""

    def __init__(
        self,
        subsystem: str,
        run_id: str,
        *,
        extra_redact_keys: frozenset[str] | None = None,
    ) -> None:
        self._run_id = run_id
        self._subsystem = subsystem
        self._extra_redact = extra_redact_keys
        self._base = Path.cwd() / "logs" / subsystem / run_id
        (self._base / "requests").mkdir(parents=True, exist_ok=True)
        (self._base / "responses").mkdir(parents=True, exist_ok=True)
        self._seq = 0

    @property
    def base_dir(self) -> Path:
        return self._base

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def log(
        self,
        *,
        url: str,
        params: dict[str, str],
        response: httpx.Response | None,
        error: str | None = None,
        attempt: int = 1,
        elapsed_ms: int = 0,
        endpoint_slug: str | None = None,
    ) -> None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        seq = self._next_seq()
        slug = endpoint_slug or (
            url.rsplit("/", 1)[-1] if "/" in url else "unknown"
        )
        safe_params = _redact_params(params, self._extra_redact)

        req_payload = {
            "seq": seq,
            "run_id": self._run_id,
            "subsystem": self._subsystem,
            "timestamp": ts,
            "method": "GET",
            "url": url,
            "params": safe_params,
            "attempt": attempt,
        }
        req_fname = f"{ts}_{seq:04d}_{slug}_req.json"
        (self._base / "requests" / req_fname).write_text(
            json.dumps(req_payload, indent=2, default=str),
            encoding="utf-8",
        )

        resp_payload: dict[str, Any] = {
            "seq": seq,
            "run_id": self._run_id,
            "subsystem": self._subsystem,
            "timestamp": ts,
            "url": url,
            "endpoint": slug,
            "elapsed_ms": elapsed_ms,
            "attempt": attempt,
        }
        if response is not None:
            resp_payload["status_code"] = response.status_code
            resp_payload["headers"] = dict(response.headers)
            resp_payload["body"] = response.text
        if error is not None:
            resp_payload["error"] = error

        resp_fname = f"{ts}_{seq:04d}_{slug}_resp.json"
        (self._base / "responses" / resp_fname).write_text(
            json.dumps(resp_payload, indent=2, default=str),
            encoding="utf-8",
        )
