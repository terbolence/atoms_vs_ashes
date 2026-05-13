# man_hours: 0.7
"""Pure helpers for ``verify_fix04_db_vs_jsonl.py``.

All cell-level decision logic and the markdown rendering live here so
the orchestrator stays under the 300-line file-size limit and so the
three-way comparison is unit-testable without DB or JSONL fixtures.

Notation (matches the orchestrator docstring):

- ``A`` = JSONL.db.<domain>.<col>      — pre-apply DB state.
- ``B`` = JSONL.fetch.<domain>.<key>   — Overpass-derived "proposed".
- ``C`` = post-apply DB read.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from _preview_fix04_diff import (  # noqa: E402
    DOMAINS, coerce, serialise, values_equal,
)


VERDICT_KEYS: tuple[str, ...] = (
    "ok-flip", "ok-stable",
    "fail-flip-no-op", "fail-flip-mismatch",
    "fail-stable-drift-pre", "fail-stable-mismatch",
)


def empty_aggregate() -> dict[str, int]:
    return {k: 0 for k in VERDICT_KEYS}


def empty_flip_counts() -> dict[str, dict[str, dict[str, int]]]:
    return {
        d.label: {col: {"expected": 0, "landed": 0} for _, col in d.columns}
        for d in DOMAINS
    }


def classify_cell(
    *, db_col: str, a: Any, b: Any, c: Any, was_flagged: bool,
) -> str:
    """Return a per-cell verdict given pre/proposed/post values."""
    a, b, c = coerce(a), coerce(b), coerce(c)
    cb = values_equal(db_col, c, b)
    ca = values_equal(db_col, c, a)
    if was_flagged:
        # By construction "flagged" means A != B, so cb and ca cannot both
        # be true. Bucket on whether C landed B, stuck on A, or drifted to
        # a third value.
        if cb:
            return "ok-flip"
        if ca:
            return "fail-flip-no-op"
        return "fail-flip-mismatch"
    if cb and ca:
        return "ok-stable"
    if cb and not ca:
        return "fail-stable-drift-pre"
    return "fail-stable-mismatch"


def flagged_set(rec: dict[str, Any]) -> set[tuple[str, str]]:
    """Extract (domain, db_column) tuples the preview flagged as flips."""
    diffs = rec.get("diff") or []
    return {
        (d["domain"], d["column"])
        for d in diffs if isinstance(d, dict)
        and "domain" in d and "column" in d
    }


def evaluate_record(
    *, rec: dict[str, Any], db_state: dict[str, dict[str, Any]],
    flagged: set[tuple[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Compute failures + per-verdict counts for one record."""
    fetch = rec.get("fetch") or {}
    db_pre = rec.get("db") or {}
    failures: list[dict[str, Any]] = []
    verdicts = empty_aggregate()
    for spec in DOMAINS:
        parsed = fetch.get(spec.label) or {}
        pre = db_pre.get(spec.label) or {}
        post = db_state[spec.label]
        for parsed_key, db_col in spec.columns:
            a = pre.get(db_col)
            b = parsed.get(parsed_key)
            c = post.get(db_col)
            was_flagged = (spec.label, db_col) in flagged
            v = classify_cell(
                db_col=db_col, a=a, b=b, c=c, was_flagged=was_flagged,
            )
            verdicts[v] += 1
            if v.startswith("fail-"):
                failures.append({
                    "domain": spec.label, "column": db_col,
                    "verdict": v,
                    "pre_apply_db": serialise(a),
                    "proposed": serialise(b),
                    "post_apply_db": serialise(c),
                    "was_flagged": was_flagged,
                })
    return failures, verdicts


def update_flip_counts(
    *,
    flip_counts: dict[str, dict[str, dict[str, int]]],
    flagged: set[tuple[str, str]],
    failures: list[dict[str, Any]],
) -> int:
    """Bump per-column flip counts; return how many flips landed cleanly."""
    flagged_failed = {
        (f["domain"], f["column"]) for f in failures if f["was_flagged"]
    }
    landed = 0
    for label, col in flagged:
        flip_counts[label][col]["expected"] += 1
        if (label, col) not in flagged_failed:
            flip_counts[label][col]["landed"] += 1
            landed += 1
    return landed


def render_report(
    *, total: int, flips_expected: int, flips_landed: int,
    sites_with_failures: list[dict[str, Any]],
    aggregate: dict[str, int],
    per_column_flip_counts: dict[str, dict[str, dict[str, int]]],
    jsonl_path: Path, head_limit: int, run_id: str,
) -> str:
    parts: list[str] = []
    parts.append("<!-- man_hours: 0.4 -->")
    parts.append("# FIX-04 — post-apply verification (DB ⨯ JSONL three-way)")
    parts.append("")
    parts.append(f"- Verifier run: `{run_id}`")
    parts.append(f"- Generated: {datetime.now(timezone.utc).isoformat()}")
    parts.append(f"- Source JSONL: `{jsonl_path}`")
    parts.append(f"- Sites verified: **{total}**")
    parts.append(
        f"- (Site, column) tuples flagged as flips by preview: "
        f"**{flips_expected}**"
    )
    parts.append(
        f"- Of those, landed correctly (C == B and C != A): "
        f"**{flips_landed}**"
    )
    parts.append(
        f"- Sites with at least one failure: **{len(sites_with_failures)}**"
    )
    parts.append("")
    parts.append("## Per-cell verdict aggregate")
    parts.append("")
    parts.append("| Verdict | Count | Meaning |")
    parts.append("|---------|------:|---------|")
    parts.append(
        f"| `ok-flip` | {aggregate['ok-flip']} | "
        "Preview flagged this cell; apply landed proposed value (C==B) and "
        "moved off pre-state (C!=A). |"
    )
    parts.append(
        f"| `ok-stable` | {aggregate['ok-stable']} | "
        "Preview did not flag this cell; A==B==C. |"
    )
    parts.append(
        f"| `fail-flip-no-op` | {aggregate['fail-flip-no-op']} | "
        "Preview flagged a flip but DB never moved off A. |"
    )
    parts.append(
        f"| `fail-flip-mismatch` | {aggregate['fail-flip-mismatch']} | "
        "Preview flagged a flip; DB now holds neither A nor B. |"
    )
    parts.append(
        f"| `fail-stable-drift-pre` | {aggregate['fail-stable-drift-pre']} | "
        "Preview said in-sync but pre-apply DB (A) actually differed from "
        "proposed (B); off-target write fixed it. |"
    )
    parts.append(
        f"| `fail-stable-mismatch` | {aggregate['fail-stable-mismatch']} | "
        "Preview said in-sync but post-apply DB now disagrees with both A "
        "and B. |"
    )
    parts.append("")
    parts.append(
        "## Per-column flips landed (preview-flagged ⨯ DB-landed)"
    )
    parts.append("")
    for d in DOMAINS:
        parts.append(f"### {d.criterion} ({d.label})")
        parts.append("")
        parts.append("| Column | Flips expected | Flips landed |")
        parts.append("|--------|---------------:|-------------:|")
        cols = per_column_flip_counts.get(d.label, {})
        for _, col in d.columns:
            data = cols.get(col, {"expected": 0, "landed": 0})
            parts.append(
                f"| `{col}` | {data['expected']} | {data['landed']} |"
            )
        parts.append("")
    if not sites_with_failures:
        parts.append(
            "_All three-way checks passed. The apply transitioned exactly "
            "the cells the preview promised, to the values the preview "
            "promised, and did not touch any cells outside that set._"
        )
        return "\n".join(parts) + "\n"
    parts.append(f"## Sites with failures (showing first {head_limit})")
    parts.append("")
    for entry in sites_with_failures[:head_limit]:
        parts.append(
            f"### {entry['country_code']} — {entry['name']}  "
            f"(`{entry['site_id']}`)"
        )
        parts.append("")
        parts.append(
            "| domain | column | verdict | pre (A) | "
            "proposed (B) | post (C) | flagged |"
        )
        parts.append(
            "|--------|--------|---------|---------|"
            "--------------|----------|--------:|"
        )
        for f in entry["failures"]:
            parts.append(
                f"| {f['domain']} | `{f['column']}` | `{f['verdict']}` | "
                f"`{f['pre_apply_db']}` | `{f['proposed']}` | "
                f"`{f['post_apply_db']}` | "
                f"{'yes' if f['was_flagged'] else 'no'} |"
            )
        parts.append("")
    if len(sites_with_failures) > head_limit:
        parts.append(
            f"_+ {len(sites_with_failures) - head_limit} more sites with "
            "failures._"
        )
        parts.append("")
    return "\n".join(parts) + "\n"
