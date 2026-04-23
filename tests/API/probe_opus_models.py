#!/usr/bin/env python3
"""List Anthropic models (markdown table) and probe claude-opus-4-6 with/without thinking.

Uses ``httpx`` only (no ``anthropic`` package required).

Usage (from repo root)::

    python tests/API/probe_opus_models.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

MODEL_ID = "claude-opus-4-6"
API = "https://api.anthropic.com/v1"
ANTHROPIC_VERSION = "2023-06-01"


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for d in (here.parent, *here.parents):
        if (d / "pyproject.toml").exists():
            return d
    return Path.cwd()


def _headers(api_key: str) -> dict[str, str]:
    return {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }


def _thinking_supported(cap: dict) -> str:
    t = cap.get("thinking") or {}
    if not t.get("supported"):
        return "no"
    types = (t.get("types") or {})
    parts = []
    for name in ("enabled", "adaptive"):
        sub = types.get(name) or {}
        if sub.get("supported"):
            parts.append(name)
    return ", ".join(parts) if parts else "yes"


def fetch_models_json(client: httpx.Client, api_key: str) -> list[dict]:
    r = client.get(f"{API}/models", headers=_headers(api_key))
    r.raise_for_status()
    payload = r.json()
    return list(payload.get("data") or [])


def print_models_table(models: list[dict]) -> None:
    rows: list[tuple[str, str, str, str, str]] = []
    for m in models:
        mid = m.get("id") or ""
        name = m.get("display_name") or ""
        cap = m.get("capabilities") or {}
        tin = m.get("max_input_tokens")
        tout = m.get("max_tokens")
        think = _thinking_supported(cap)
        rows.append((mid, name, str(tin or ""), str(tout or ""), think))
    rows.sort(key=lambda x: x[0].lower())

    headers = ("Model id", "Display name", "Max input", "Max output", "Thinking")
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def fmt_row(cells: tuple[str, ...]) -> str:
        return "| " + " | ".join(c.ljust(widths[i]) for i, c in enumerate(cells)) + " |"

    sep = "|" + "|".join("-" * (w + 2) for w in widths) + "|"
    print(fmt_row(headers))
    print(sep)
    for row in rows:
        print(fmt_row(row))


def _message_content_summary(body: dict) -> tuple[int, int, str]:
    content = body.get("content") or []
    n_text = 0
    n_think = 0
    first_text = ""
    for block in content:
        if not isinstance(block, dict):
            continue
        t = block.get("type")
        if t == "text":
            n_text += 1
            if not first_text:
                first_text = (block.get("text") or "")[:80]
        elif t == "thinking":
            n_think += 1
    return n_text, n_think, first_text


def post_messages(
    client: httpx.Client,
    api_key: str,
    payload: dict,
) -> tuple[bool, str, dict]:
    r = client.post(f"{API}/messages", headers=_headers(api_key), json=payload)
    try:
        body = r.json()
    except Exception:
        body = {}
    if not r.is_success:
        err = body.get("error") if isinstance(body.get("error"), dict) else body
        return False, f"HTTP {r.status_code} {err!r}", body

    n_text, n_think, preview = _message_content_summary(body)
    detail = f"text_blocks={n_text} thinking_blocks={n_think} text_preview={preview!r} usage={body.get('usage', {})}"
    return True, detail, body


def main() -> int:
    load_dotenv(_repo_root() / ".env")
    key = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
    if not key:
        print("ANTHROPIC_API_KEY is not set.", file=sys.stderr)
        return 1

    print("## Available models\n")
    with httpx.Client(timeout=120.0) as client:
        try:
            models = fetch_models_json(client, key)
        except Exception as e:
            print(f"Models list failed: {e}", file=sys.stderr)
            return 1

        print_models_table(models)
        print()

        if not any(m.get("id") == MODEL_ID for m in models):
            print(f"No `{MODEL_ID}` in catalog — skipping probes.", file=sys.stderr)
            return 1

        print(f"## Probes for `{MODEL_ID}`\n")

        ok_raw, det_nt, body_nt = post_messages(
            client,
            key,
            {
                "model": MODEL_ID,
                "max_tokens": 128,
                "temperature": 0.0,
                "messages": [{"role": "user", "content": "Reply with exactly one word: OK"}],
            },
        )
        n_text, n_think, _ = _message_content_summary(body_nt)
        ok_nt = ok_raw and n_text >= 1 and n_think == 0
        print(f"- **Non-thinking**: {'PASS' if ok_nt else 'FAIL'} — {det_nt}")

        budget = 4096
        max_tokens = budget + 2048
        ok_raw2, det_t, body_t = post_messages(
            client,
            key,
            {
                "model": MODEL_ID,
                "max_tokens": max_tokens,
                "temperature": 1.0,
                "thinking": {"type": "enabled", "budget_tokens": budget},
                "messages": [{
                    "role": "user",
                    "content": (
                        "Use your reasoning briefly, then end your visible reply with the token <END>."
                    ),
                }],
            },
        )
        n_text2, n_think2, _ = _message_content_summary(body_t)
        ok_t = ok_raw2 and n_think2 >= 1 and n_text2 >= 1
        print(f"- **Thinking (enabled)**: {'PASS' if ok_t else 'FAIL'} — {det_t}")

    return 0 if (ok_nt and ok_t) else 1


if __name__ == "__main__":
    raise SystemExit(main())
