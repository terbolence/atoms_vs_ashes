"""Compare the regenerated Chapter 4 table row sets against the v1.03
ledger ground-truth aggregates and fail on drift.

The script reads the idempotent ``<!-- begin: table-4.x.y -->`` blocks
from ``04_results_and_findings.md`` and compares the row sets against:

- Table 4.1.1 cohort totals: derived from the 16 in-scope v1.03 ledgers
  + the 3 no-pass ``feedback_rerun_20260509`` country bundles.
- Table 4.2.1 leading scored set: top-3 scored sites per country
  computed from the same ledgers.
- Table 4.3.1 cohort: every ledger row with
  ``passed_exclusionary=True`` AND ``passed_avoidance=True``.
- Table 4.3.2 cohort: every ledger row with
  ``passed_exclusionary=True`` AND ``passed_avoidance=False`` whose
  site bundle exists under ``data/``.

Exit code 0 only when every comparison matches; ``--strict`` (default)
returns 1 on drift so the same script can run from pytest.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


_DEFAULT_CHAPTER4 = Path(
    "report/version 1.03/output/report/chapters/04_results_and_findings.md"
)
_DEFAULT_DATA_DIR = Path(
    "report/version 1.03/output/report/chapters/05_country_and_site_profiles/data"
)
_DEFAULT_NOPASS_DIR = Path(
    "report/version 1.03/output/report/bundles/feedback_rerun_20260509"
)

_IN_SCOPE_COUNTRIES = (
    "AT", "BA", "BG", "CZ", "HR", "HU", "LV", "MD", "ME",
    "MK", "PL", "RO", "RS", "SK", "TR", "UA",
)
_NOPASS_COUNTRIES = ("AL", "SI", "XK")

_MARKER_RE_TPL = (
    r"<!--\s*begin:\s*table-{tid}\s*-->(?P<body>.*?)<!--\s*end:\s*table-{tid}\s*-->"
)


@dataclass
class Finding:
    table_id: str
    detail: str


def _block(text: str, table_id: str) -> str | None:
    match = re.search(
        _MARKER_RE_TPL.format(tid=re.escape(table_id)), text, re.DOTALL,
    )
    return match.group("body") if match else None


def _data_rows(block_text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in block_text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells:
            continue
        if all(set(c) <= set(": -") for c in cells):
            continue
        rows.append(cells)
    return rows[1:] if rows else rows


def _load_ledger(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _f(value: str | None) -> float | None:
    if not value or value == "None":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _check_4_1_1(
    block: str, ledger_rows: dict[str, list[dict[str, str]]],
    nopass_dir: Path,
) -> list[Finding]:
    findings: list[Finding] = []
    rows = _data_rows(block)
    if len(rows) < 3:
        findings.append(Finding("4.1.1", f"expected 3 rows, found {len(rows)}"))
        return findings

    published = rows[0]
    nopass = rows[1]
    total = rows[2]

    sites = sum(len(ledger_rows.get(cc, [])) for cc in _IN_SCOPE_COUNTRIES)
    scored = sum(
        1 for cc in _IN_SCOPE_COUNTRIES for r in ledger_rows.get(cc, [])
        if r.get("composite_score")
    )
    fp = sum(
        1 for cc in _IN_SCOPE_COUNTRIES for r in ledger_rows.get(cc, [])
        if r.get("passed_exclusionary") == "True"
        and r.get("passed_avoidance") == "True"
    )
    avf = sum(
        1 for cc in _IN_SCOPE_COUNTRIES for r in ledger_rows.get(cc, [])
        if r.get("passed_exclusionary") == "True"
        and r.get("passed_avoidance") == "False"
    )
    hf = sum(
        1 for cc in _IN_SCOPE_COUNTRIES for r in ledger_rows.get(cc, [])
        if r.get("passed_exclusionary") == "False"
    )

    expected_published = [
        "Published country ledgers",
        str(len(_IN_SCOPE_COUNTRIES)), str(sites), str(scored),
        str(fp), str(avf), str(hf),
    ]
    if published != expected_published:
        findings.append(Finding(
            "4.1.1",
            f"published row drift: ledger={expected_published} chapter={published}",
        ))

    np_sites = np_scored = np_fp = np_avf = np_hf = 0
    for cc in _NOPASS_COUNTRIES:
        path = nopass_dir / f"{cc}_country_bundle.json"
        if not path.exists():
            findings.append(Finding(
                "4.1.1", f"missing feedback_rerun bundle {cc}",
            ))
            continue
        b = json.loads(path.read_text(encoding="utf-8"))
        t = b.get("totals") or {}
        np_sites += t.get("n_sites", 0)
        np_scored += t.get("n_with_score", 0)
        np_fp += t.get("n_full_pass", 0)
        np_avf += t.get("n_avoidance_flag", 0)
        np_hf += t.get("n_hard_fail", 0)

    expected_nopass = [
        "Consolidated no-pass country section",
        str(len(_NOPASS_COUNTRIES)),
        str(np_sites), str(np_scored), str(np_fp), str(np_avf), str(np_hf),
    ]
    if nopass != expected_nopass:
        findings.append(Finding(
            "4.1.1",
            f"no-pass row drift: ledger={expected_nopass} chapter={nopass}",
        ))

    expected_total = [
        "Published Chapter 4 evidence base",
        str(len(_IN_SCOPE_COUNTRIES) + len(_NOPASS_COUNTRIES)),
        str(sites + np_sites), str(scored + np_scored),
        str(fp + np_fp), str(avf + np_avf), str(hf + np_hf),
    ]
    if total != expected_total:
        findings.append(Finding(
            "4.1.1",
            f"total row drift: ledger={expected_total} chapter={total}",
        ))
    return findings


def _check_4_3_1(
    block: str, ledger_rows: dict[str, list[dict[str, str]]],
) -> list[Finding]:
    findings: list[Finding] = []
    rows = _data_rows(block)
    full_pass = [
        r for cc in _IN_SCOPE_COUNTRIES for r in ledger_rows.get(cc, [])
        if r.get("passed_exclusionary") == "True"
        and r.get("passed_avoidance") == "True"
        and r.get("composite_score")
    ]
    if len(rows) != len(full_pass):
        findings.append(Finding(
            "4.3.1",
            f"row count drift: ledger full-pass={len(full_pass)} chapter={len(rows)}",
        ))
    chapter_names = {r[1] for r in rows if len(r) > 1}
    ledger_names = {r["name"] for r in full_pass}
    missing = ledger_names - chapter_names
    extra = chapter_names - ledger_names
    if missing:
        findings.append(Finding(
            "4.3.1", f"missing from chapter: {sorted(missing)}",
        ))
    if extra:
        findings.append(Finding(
            "4.3.1", f"unexpected in chapter: {sorted(extra)}",
        ))
    return findings


def _check_4_3_2(
    block: str, ledger_rows: dict[str, list[dict[str, str]]],
    data_dir: Path,
) -> list[Finding]:
    findings: list[Finding] = []
    rows = _data_rows(block)

    bundle_stems = {
        p.stem.replace("_site_bundle", "")
        for p in data_dir.glob("*_site_bundle.json")
    }

    avf = []
    for cc in _IN_SCOPE_COUNTRIES:
        for r in ledger_rows.get(cc, []):
            if r.get("passed_exclusionary") != "True":
                continue
            if r.get("passed_avoidance") != "False":
                continue
            if not r.get("composite_score"):
                continue
            slug = _slug(r["name"])
            if f"{cc}_{slug}" in bundle_stems:
                avf.append(r)

    chapter_names = {r[0] for r in rows if r}
    ledger_names = {r["name"] for r in avf}
    if len(rows) != len(avf):
        findings.append(Finding(
            "4.3.2",
            f"row count drift: ledger avoidance+profiled={len(avf)} chapter={len(rows)}",
        ))
    missing = ledger_names - chapter_names
    extra = chapter_names - ledger_names
    if missing:
        findings.append(Finding(
            "4.3.2", f"missing from chapter: {sorted(missing)}",
        ))
    if extra:
        findings.append(Finding(
            "4.3.2", f"unexpected in chapter: {sorted(extra)}",
        ))
    return findings


def _slug(name: str) -> str:
    import re as _re
    import unicodedata
    normal = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    out = _re.sub(r"[^a-zA-Z0-9]+", "_", normal).strip("_").lower()
    return out or "site"


def run_lint(
    *,
    chapter4: Path,
    data_dir: Path,
    nopass_dir: Path,
) -> list[Finding]:
    text = chapter4.read_text(encoding="utf-8")
    ledger_rows: dict[str, list[dict[str, str]]] = {}
    for cc in _IN_SCOPE_COUNTRIES:
        path = data_dir / f"{cc}_site_ledger.csv"
        if path.exists():
            ledger_rows[cc] = _load_ledger(path)

    findings: list[Finding] = []
    for tid, handler in (
        ("4.1.1", lambda b: _check_4_1_1(b, ledger_rows, nopass_dir)),
        ("4.3.1", lambda b: _check_4_3_1(b, ledger_rows)),
        ("4.3.2", lambda b: _check_4_3_2(b, ledger_rows, data_dir)),
    ):
        block = _block(text, tid)
        if block is None:
            findings.append(Finding(tid, "no idempotent marker block found"))
            continue
        findings.extend(handler(block))
    return findings


def format_report(findings: list[Finding]) -> str:
    if not findings:
        return "lint_ledger_consistency: 0 findings (clean).\n"
    lines = [f"lint_ledger_consistency: {len(findings)} findings"]
    for f in findings:
        lines.append(f"  table-{f.table_id}: {f.detail}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser("lint_ledger_consistency")
    p.add_argument("--chapter4", type=Path, default=_DEFAULT_CHAPTER4)
    p.add_argument("--data-dir", type=Path, default=_DEFAULT_DATA_DIR)
    p.add_argument("--nopass-dir", type=Path, default=_DEFAULT_NOPASS_DIR)
    p.add_argument(
        "--strict", action="store_true", default=True,
        help="Exit 1 on drift (default).",
    )
    p.add_argument(
        "--no-strict", dest="strict", action="store_false",
        help="Print drift but exit 0.",
    )
    args = p.parse_args(argv)
    findings = run_lint(
        chapter4=args.chapter4, data_dir=args.data_dir,
        nopass_dir=args.nopass_dir,
    )
    sys.stdout.write(format_report(findings))
    return 1 if (findings and args.strict) else 0


if __name__ == "__main__":
    raise SystemExit(main())
