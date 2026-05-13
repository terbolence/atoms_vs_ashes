#!/usr/bin/env python
# man_hours: 0.6
"""Compare ``ranking_scores`` between two scoring runs for anchor sites.

Local-only: reads from the project DB, writes a Markdown delta report.
No external API calls.

Use this after the SP-F scoring rerun to confirm Ovidiu-commented anchor
sites (Timelkam, Riedersbach, Braila) move in the expected direction
across the criteria affected by the rubric/spec changes (BF-01, BF-02,
NH-04, NH-09, NH-11, NH-13, NH-14, HI-02/04/05/06/08, EP-01, NS-02,
NS-05).

Usage::

    PYTHONPATH=src .venv/bin/python src/scripts/compare_anchor_scores.py \\
        --before-run-id feedback_rerun_20260509 \\
        --after-run-id  <new_score_run_id> \\
        --smr-key nuscale_voygr6 \\
        --out audit/post_processing/scoring_rerun_runbook/anchor_delta.md

Omit ``--smr-key`` to include every SMR design present in both runs.
Repeat ``--smr-key`` for multiple designs.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from sqlalchemy import create_engine, text as sa_text

from atoms_vs_ashes.config import Settings

DEFAULT_ANCHOR_NAMES: tuple[str, ...] = (
    "Timelkam power station",
    "Riedersbach power station",
    "Braila power station",
)
DEFAULT_CRITERIA: tuple[str, ...] = (
    "BF-01", "BF-02", "NS-02", "NS-05",
    "NH-04", "NH-09", "NH-11", "NH-13", "NH-14",
    "HI-02", "HI-04", "HI-05", "HI-06", "HI-08",
    "EP-01",
)


def _resolve_anchor_sites(conn, names: Iterable[str]) -> list[dict]:
    rows = conn.execute(
        sa_text(
            "SELECT site_id, country_code, name FROM sites "
            "WHERE name = ANY(:names) ORDER BY country_code, name"
        ),
        {"names": list(names)},
    ).mappings().all()
    return [dict(r) for r in rows]


def _fetch_scores(
    conn,
    *,
    site_ids: list,
    run_id: str,
    criteria: list[str],
    smr_keys: list[str] | None = None,
) -> dict:
    """Return ``{(site_id, smr_key, criterion_id): row_dict}`` for *run_id*."""
    smr_clause = ""
    params: dict = {"rid": run_id, "sids": site_ids, "cids": criteria}
    if smr_keys:
        smr_clause = " AND smr_key = ANY(:smr_keys)"
        params["smr_keys"] = smr_keys
    rows = conn.execute(
        sa_text(
            "SELECT site_id, smr_key, criterion_id, score_0_10, quality_flag, "
            "       confidence, scored_at "
            "FROM ranking_scores "
            "WHERE run_id = :rid AND site_id = ANY(:sids) "
            "      AND criterion_id = ANY(:cids)"
            + smr_clause
        ),
        params,
    ).mappings().all()
    out: dict = {}
    for r in rows:
        key = (r["site_id"], r["smr_key"], r["criterion_id"])
        out[key] = dict(r)
    return out


def _format_score(val) -> str:
    return f"{float(val):.1f}" if val is not None else "—"


def _format_delta(before, after) -> str:
    if before is None or after is None:
        return "—"
    delta = float(after) - float(before)
    if abs(delta) < 0.05:
        return f"={delta:+.1f}"
    return f"{delta:+.1f}"


def _render_markdown(
    anchors: list[dict],
    criteria: list[str],
    before_run_id: str,
    after_run_id: str,
    before_scores: dict,
    after_scores: dict,
    *,
    smr_filter: list[str] | None,
) -> str:
    smr_keys = sorted({
        smr for (_, smr, _) in {**before_scores, **after_scores}
    })
    lines: list[str] = ["<!-- man_hours: 0.0 -->"]
    lines.append("# Anchor-Site Score Delta — SP-F Rerun")
    lines.append("")
    lines.append(f"- Baseline `run_id`: `{before_run_id}`")
    lines.append(f"- SP-F `run_id`: `{after_run_id}`")
    if smr_filter:
        lines.append(f"- SMR filter: `{', '.join(sorted(smr_filter))}`")
    lines.append(f"- SMR designs present: {', '.join(smr_keys) or '(none)'}")
    lines.append("")
    lines.append("Negative deltas mean the SP-F change lowered the score; positive deltas raised it. `=` marks a numerically identical score.")
    lines.append("")

    for anchor in anchors:
        sid = anchor["site_id"]
        cc = anchor["country_code"]
        name = anchor["name"]
        lines.append(f"## {cc} — {name}")
        lines.append("")
        lines.append(f"`site_id = {sid}`")
        lines.append("")
        for smr in smr_keys:
            relevant_before = {
                (s, k, c): row for (s, k, c), row in before_scores.items()
                if s == sid and k == smr
            }
            relevant_after = {
                (s, k, c): row for (s, k, c), row in after_scores.items()
                if s == sid and k == smr
            }
            if not relevant_before and not relevant_after:
                continue
            lines.append(f"### SMR `{smr}`")
            lines.append("")
            lines.append("| Criterion | Before | After | Δ | Quality (before → after) |")
            lines.append("| --- | --- | --- | --- | --- |")
            for cid in criteria:
                b = relevant_before.get((sid, smr, cid))
                a = relevant_after.get((sid, smr, cid))
                bs = b.get("score_0_10") if b else None
                as_ = a.get("score_0_10") if a else None
                bq = (b or {}).get("quality_flag") or "—"
                aq = (a or {}).get("quality_flag") or "—"
                lines.append(
                    f"| {cid} | {_format_score(bs)} | {_format_score(as_)} | "
                    f"{_format_delta(bs, as_)} | {bq} → {aq} |"
                )
            lines.append("")
    return "\n".join(lines) + "\n"


def _summary_counts(
    anchors: list[dict],
    criteria: list[str],
    before_scores: dict,
    after_scores: dict,
) -> dict:
    """Quick stats: missing rows, score-change counts."""
    smr_keys = sorted({
        smr for (_, smr, _) in {**before_scores, **after_scores}
    })
    delta_counts: dict[str, int] = defaultdict(int)
    missing_before = 0
    missing_after = 0
    for anchor in anchors:
        for smr in smr_keys:
            for cid in criteria:
                key = (anchor["site_id"], smr, cid)
                b = before_scores.get(key)
                a = after_scores.get(key)
                if b is None and a is None:
                    continue
                if b is None:
                    missing_before += 1
                if a is None:
                    missing_after += 1
                if b is not None and a is not None:
                    delta = float(a["score_0_10"]) - float(b["score_0_10"])
                    if abs(delta) < 0.05:
                        delta_counts["unchanged"] += 1
                    elif delta > 0:
                        delta_counts["up"] += 1
                    else:
                        delta_counts["down"] += 1
    return {
        "missing_before": missing_before,
        "missing_after": missing_after,
        "delta": dict(delta_counts),
    }


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--before-run-id", required=True)
    parser.add_argument("--after-run-id", required=True)
    parser.add_argument(
        "--anchor", action="append", default=None,
        help="Site name (exact). Repeatable. Defaults to Timelkam/Riedersbach/Braila.",
    )
    parser.add_argument(
        "--criterion", action="append", default=None,
        help="Criterion id (e.g. NH-04). Repeatable. Defaults to SP-F-affected ids.",
    )
    parser.add_argument(
        "--out", type=Path,
        default=Path("audit/post_processing/scoring_rerun_runbook/anchor_delta.md"),
    )
    parser.add_argument(
        "--smr-key",
        action="append",
        default=None,
        help=(
            "SMR design key (e.g. nuscale_voygr6). Repeatable. "
            "Omit to compare all SMR keys present in both runs."
        ),
    )
    args = parser.parse_args(argv)

    anchors = list(args.anchor) if args.anchor else list(DEFAULT_ANCHOR_NAMES)
    criteria = list(args.criterion) if args.criterion else list(DEFAULT_CRITERIA)
    smr_keys = list(dict.fromkeys(args.smr_key)) if args.smr_key else None

    engine = create_engine(Settings().database.url, pool_pre_ping=True)
    with engine.connect() as conn:
        sites = _resolve_anchor_sites(conn, anchors)
        if not sites:
            print(f"ERROR: no sites matched {anchors!r}", file=sys.stderr)
            return 1
        sids = [s["site_id"] for s in sites]
        before_scores = _fetch_scores(
            conn, site_ids=sids, run_id=args.before_run_id, criteria=criteria,
            smr_keys=smr_keys,
        )
        after_scores = _fetch_scores(
            conn, site_ids=sids, run_id=args.after_run_id, criteria=criteria,
            smr_keys=smr_keys,
        )

    if not before_scores and not after_scores:
        print(
            "ERROR: neither run_id produced rows for the chosen anchors and criteria.",
            file=sys.stderr,
        )
        return 2

    summary = _summary_counts(sites, criteria, before_scores, after_scores)
    md = _render_markdown(
        sites, criteria, args.before_run_id, args.after_run_id,
        before_scores, after_scores,
        smr_filter=smr_keys,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(md, encoding="utf-8")
    print(f"Wrote {args.out}")
    print(
        f"Summary: up={summary['delta'].get('up', 0)}, "
        f"down={summary['delta'].get('down', 0)}, "
        f"unchanged={summary['delta'].get('unchanged', 0)}, "
        f"missing_before={summary['missing_before']}, "
        f"missing_after={summary['missing_after']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
