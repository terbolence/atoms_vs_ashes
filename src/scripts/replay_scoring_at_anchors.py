# man_hours: 1.5
"""Replay the scoring engine for the three anchor sites against persisted context.

Read-only utility used by the scoring-engine fix iteration loop. For each
anchor site (Timelkam, Brăila, Riedersbach), the script:

1. Loads the site and its merged-context inputs from the DB (no scoring run
   is created — only :func:`build_context_for_site` is called).
2. Iterates the rubric bundle and evaluates each criterion with the current
   in-repo rubrics and the just-fixed ``safe_eval`` AST walker.
3. Prints a Markdown table per site listing the matched band, score, and
   descriptor.

Optional filters:

- ``--criterion HI-01`` (repeatable) narrows the table to one criterion at a
  time; used by the P1-1 / P1-2 audits.
- ``--cohort`` switches to a cohort-level distribution mode (no per-site
  detail). The distribution counts how many sites land in each
  ``score_range`` for the selected criterion.

The script never writes to the DB. Output is a single Markdown file at the
``--output`` path (default: stdout).
"""

from __future__ import annotations

import argparse
import sys
import uuid
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models import Site
from atoms_vs_ashes.scoring.bands import evaluate_criterion_value
from atoms_vs_ashes.scoring.merge_resolver import build_context_for_site
from atoms_vs_ashes.scoring.rubric import load_rubric_bundle

REPO_ROOT = Path(__file__).resolve().parents[2]
RUBRIC_DIR = REPO_ROOT / "config" / "scoring_rubrics"

ANCHOR_SITES: dict[str, uuid.UUID] = {
    "Timelkam (AT)": uuid.UUID("2dcd2c6d-f375-4408-9492-7910662fac03"),
    "Brăila (RO)": uuid.UUID("29836b52-a882-4921-95a7-6417e636d9a2"),
    "Riedersbach (AT)": uuid.UUID("660d9d71-6733-4294-951b-1c58614d58cf"),
}


@dataclass
class ReplayRow:
    site_label: str
    criterion_id: str
    score: float
    score_low: float
    score_high: float
    band_range: tuple[float, float] | None
    descriptor: str
    notes: str


def _band_range(result) -> tuple[float, float] | None:
    if result.matched_band is None:
        return None
    lo, hi = result.matched_band.score_range
    return (float(lo), float(hi))


def _replay_one(session: Session, site: Site, criterion) -> ReplayRow:
    ctx = build_context_for_site(session, site, criterion)
    result = evaluate_criterion_value(criterion, ctx.values, quality=ctx.quality)
    notes_str = ", ".join(result.notes or []) if result.notes else ""
    return ReplayRow(
        site_label="",
        criterion_id=criterion.criterion_id,
        score=result.score,
        score_low=result.score_low,
        score_high=result.score_high,
        band_range=_band_range(result),
        descriptor=result.descriptor,
        notes=notes_str,
    )


def _format_band(band_range: tuple[float, float] | None) -> str:
    if band_range is None:
        return "unscored"
    lo, hi = band_range
    if lo == hi:
        return f"[{lo:.0f}]"
    return f"[{lo:.0f},{hi:.0f}]"


def _render_anchor_table(rows: list[ReplayRow]) -> str:
    lines = [
        "| Site | Criterion | Band | Score | [low, high] | Descriptor | Notes |",
        "|---|---|---|---:|---|---|---|",
    ]
    for r in rows:
        descriptor = (r.descriptor or "").replace("|", "\\|")
        notes = (r.notes or "").replace("|", "\\|")
        lines.append(
            f"| {r.site_label} | {r.criterion_id} | {_format_band(r.band_range)} "
            f"| {r.score:.1f} | [{r.score_low:.1f}, {r.score_high:.1f}] "
            f"| {descriptor} | {notes} |"
        )
    return "\n".join(lines)


def _render_cohort_distribution(
    criterion_id: str,
    rows: list[ReplayRow],
) -> str:
    counter: Counter[str] = Counter()
    for r in rows:
        counter[_format_band(r.band_range)] += 1
    total = sum(counter.values())
    lines = [
        f"### Cohort distribution for {criterion_id} ({total} sites)",
        "",
        "| Band | Count | Share |",
        "|---|---:|---:|",
    ]
    band_order = ["[9,10]", "[7,8]", "[5,6]", "[3,4]", "[1,2]", "[0]", "unscored"]
    for band in band_order:
        n = counter.get(band, 0)
        if n == 0:
            continue
        share = n / total * 100 if total else 0.0
        lines.append(f"| {band} | {n} | {share:.1f}% |")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-id",
        default="20260513T030738_70d5bc2c",
        help="Used only for the output header; the engine replay reads the "
        "current DB state, not a specific run snapshot.",
    )
    parser.add_argument(
        "--criterion",
        action="append",
        default=None,
        help="Limit replay to one criterion (repeatable). Default: all criteria.",
    )
    parser.add_argument(
        "--cohort",
        action="store_true",
        help="Cohort distribution mode: count how many sites land in each band "
        "for the selected criterion (requires --criterion).",
    )
    parser.add_argument(
        "--diff-against-prev",
        type=Path,
        default=None,
        help="Optional path to a previous replay markdown; differences are "
        "annotated in the new file's tail.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to write the Markdown report. Default: stdout.",
    )
    args = parser.parse_args()

    bundle = load_rubric_bundle(RUBRIC_DIR)
    criterion_filter = set(args.criterion) if args.criterion else None
    if args.cohort and not criterion_filter:
        print(
            "--cohort requires --criterion (cohort distribution is per-criterion)",
            file=sys.stderr,
        )
        return 2

    pieces: list[str] = [
        "<!-- man_hours: 0.3 -->",
        f"# Engine replay against persisted context (run anchor: {args.run_id})",
        "",
        "Read-only replay of the scoring engine for the three anchor sites "
        "(Timelkam, Brăila, Riedersbach). The engine reads the merged DB "
        "context but does not persist a new ranking row. Use to compare the "
        "post-fix band against the reviewer expectations recorded in "
        "[anchor_score_conformity.md](anchor_score_conformity.md).",
        "",
    ]

    cohort_rows: list[ReplayRow] = []

    with session_scope() as session:
        if args.cohort:
            sites = session.query(Site).all()
            target_criterion = bundle[next(iter(criterion_filter))]
            for site in sites:
                row = _replay_one(session, site, target_criterion)
                row.site_label = str(site.site_id)
                cohort_rows.append(row)
            pieces.append(
                _render_cohort_distribution(
                    target_criterion.criterion_id, cohort_rows
                )
            )
            pieces.append("")
        else:
            for label, site_id in ANCHOR_SITES.items():
                site = session.query(Site).filter(Site.site_id == site_id).one_or_none()
                if site is None:
                    pieces.append(f"## {label}\n\n*Site not in DB.*\n")
                    continue
                rows: list[ReplayRow] = []
                for cid in sorted(bundle):
                    if criterion_filter and cid not in criterion_filter:
                        continue
                    criterion = bundle[cid]
                    row = _replay_one(session, site, criterion)
                    row.site_label = label
                    rows.append(row)
                pieces.append(f"## {label}")
                pieces.append("")
                pieces.append(_render_anchor_table(rows))
                pieces.append("")

    text = "\n".join(pieces).rstrip() + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
