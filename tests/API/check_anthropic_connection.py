#!/usr/bin/env python3
"""GET https://api.anthropic.com/v1/models — verifies API key and connectivity.

Loads ``ANTHROPIC_API_KEY`` from the project root ``.env`` (via python-dotenv).

Usage (from repo root)::

    python tests/API/check_anthropic_connection.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for d in (here.parent, *here.parents):
        if (d / "pyproject.toml").exists():
            return d
    return Path.cwd()


def main() -> int:
    load_dotenv(_repo_root() / ".env")
    key = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
    if not key:
        print("ANTHROPIC_API_KEY is not set. Add it to .env at the repo root.", file=sys.stderr)
        return 1

    url = "https://api.anthropic.com/v1/models"
    headers = {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.get(url, headers=headers)
    except httpx.RequestError as e:
        print(f"Request failed: {e}", file=sys.stderr)
        return 1

    print(f"HTTP {r.status_code} {r.reason_phrase}")
    for h in ("content-type", "request-id"):
        if r.headers.get(h):
            print(f"{h}: {r.headers[h]}")

    body = r.text
    max_len = 4000
    if len(body) > max_len:
        body = body[:max_len] + "\n... [truncated]"
    print(body)

    return 0 if r.is_success else 1


if __name__ == "__main__":
    raise SystemExit(main())
