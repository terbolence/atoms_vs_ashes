"""Phase 6 prerequisite: Ovidiu-comments closure audit.

Reads the v1.03 feedback triage YAML, filters to Ovidiu Lucian Coman's 10
reviewer comments, and runs one programmatic anchor check per comment
against the live chapter / annex source tree. Emits a one-row-per-comment
pass/fail table to stdout and persists the structured report to
``audit/v1_03_phase_6/ovidiu_closure_audit.json``.

Exit code: 0 iff every Ovidiu comment passes its anchor check. The Phase 6
build is gated on this script.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_ROOT = REPO_ROOT / "report" / "version 1.03" / "output" / "report"
CHAPTERS = REPORT_ROOT / "chapters"
ANNEXES = REPORT_ROOT / "annexes"
TRIAGE_YAML = (
    REPORT_ROOT
    / "feedback"
    / "synthesised_comments"
    / "atoms_vs_ashes_report_feedback_triage.yaml"
)
JSON_REPORT_PATH = (
    REPO_ROOT / "audit" / "v1_03_phase_6" / "ovidiu_closure_audit.json"
)

OVIDIU_IDS = {"32", "38", "43", "50", "54", "57", "60", "61", "63", "70"}


@dataclass
class CheckResult:
    comment_id: str
    closure_status: str
    description: str
    findings: list[str] = field(default_factory=list)
    passed: bool = True


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        return f"<<UNREADABLE: {exc}>>"


def _expect(
    result: CheckResult,
    condition: bool,
    failure_msg: str,
) -> None:
    if not condition:
        result.passed = False
        result.findings.append(failure_msg)


def _check_32(result: CheckResult) -> None:
    path = CHAPTERS / "02_stage_1_site_survey.md"
    text = _read(path)
    _expect(
        result,
        "2.7 Stage 1 Outputs and Limitations" in text,
        f"missing §2.7 heading in {path}",
    )
    _expect(
        result,
        "controlled handoff to Stage 2" in text,
        f"missing Stage 1 → Stage 2 handoff sentence in {path}",
    )


def _check_38(result: CheckResult) -> None:
    chap6 = _read(CHAPTERS / "06_recommendations_for_detailed_site_evaluation.md")
    _expect(
        result,
        "Stage 1 — Site Survey" in chap6,
        "Chapter 6 opener missing Stage 1 — Site Survey block",
    )
    _expect(
        result,
        "Stage 2 — Site Selection" in chap6,
        "Chapter 6 opener missing Stage 2 — Site Selection block",
    )
    _expect(
        result,
        "Stage 3 — Site Evaluation and Confirmation" in chap6,
        "Chapter 6 opener missing Stage 3 — Site Evaluation and Confirmation block",
    )
    _expect(
        result,
        "ulterior Stage 3" in chap6,
        "Chapter 6 opener missing scope-of-this-report sentence about ulterior Stage 3",
    )
    _expect(
        result,
        "Deviations from the SSG-35 stages" in chap6,
        "Chapter 6 opener missing 'Deviations from the SSG-35 stages' paragraph",
    )
    chap3 = _read(CHAPTERS / "03_stage_2_site_selection.md")
    _expect(
        result,
        "SSG-35 staging defined at the opening of Chapter 6" in chap3,
        "§3.3 missing cross-reference to Chapter 6 staging",
    )
    _expect(
        result,
        "Chapter 6" in chap3 and "ranking and selection stage" in chap3,
        "§3.10 missing 'ranking and selection stage' framing + Chapter 6 pointer",
    )


def _check_43(result: CheckResult) -> None:
    chap3 = _read(CHAPTERS / "03_stage_2_site_selection.md")
    total = 0.0
    seen_blocks = 0
    for key in ("weights-nh", "weights-hi", "weights-ri", "weights-ep", "weights-ns"):
        m = re.search(
            rf"<!-- begin: {key} -->(.*?)<!-- end: {key} -->",
            chap3,
            re.DOTALL,
        )
        if not m:
            result.passed = False
            result.findings.append(f"missing idempotent marker block {key}")
            continue
        seen_blocks += 1
        for line in m.group(1).splitlines():
            row = re.match(r"\|[^|]+\|[^|]+\|\s*([0-9]+\.?[0-9]*)", line)
            if row:
                total += float(row.group(1))
    _expect(
        result,
        seen_blocks == 5,
        f"expected 5 weight-family blocks, found {seen_blocks}",
    )
    _expect(
        result,
        abs(total - 100.0) < 0.05,
        f"baseline weight % across Tables 3.2-3.6 sums to {total:.4f}%, expected 100.00",
    )
    result.findings.append(f"weights sum = {total:.2f}%")


def _check_50(result: CheckResult) -> None:
    chap3 = _read(CHAPTERS / "03_stage_2_site_selection.md")
    chap4 = _read(CHAPTERS / "04_results_and_findings.md")
    _expect(
        result,
        "33 full-pass sites" in chap3,
        "§3.9 missing '33 full-pass sites' framing sentence",
    )
    for name in ("Turceni", "Rovinari", "Iernut"):
        _expect(
            result,
            f"{name} power station" in chap3,
            f"§3.9 Table 3.9 missing Romanian leader '{name} power station'",
        )
    _expect(
        result,
        "33 sites in total" in chap4 or "33 clear both" in chap4,
        "§4.1 / §4.3.1 prose missing 33-site full-pass framing",
    )


def _check_54_57(result: CheckResult) -> None:
    chap4 = _read(CHAPTERS / "04_results_and_findings.md")
    _expect(
        result,
        not re.search(r"\bCohort:", chap4),
        "Chapter 4 still uses 'Cohort:' in a caption (rule 5 + #54/#57 unresolved)",
    )
    _expect(
        result,
        "<!-- begin: table-4.1.1 -->" in chap4,
        "Chapter 4 missing Table 4.1.1 idempotent marker",
    )
    set_header = re.search(r"^\|\s*Set\s+\|\s*Countries\s*\|", chap4, re.MULTILINE)
    cohort_header = re.search(r"^\|\s*Cohort\s+\|\s*Countries\s*\|", chap4, re.MULTILINE)
    _expect(
        result,
        set_header is not None and cohort_header is None,
        "Chapter 4 Table 4.1.1 column header should read 'Set' (not 'Cohort')",
    )
    for marker in ("table-4.2.1", "table-4.3.1", "table-4.3.2", "table-4.4.1"):
        _expect(
            result,
            f"<!-- begin: {marker} -->" in chap4,
            f"Chapter 4 missing idempotent marker for {marker}",
        )


def _check_60(result: CheckResult) -> None:
    chap4 = _read(CHAPTERS / "04_results_and_findings.md")
    m = re.search(
        r"<!-- begin: table-4\.3\.1 -->(.*?)<!-- end: table-4\.3\.1 -->",
        chap4,
        re.DOTALL,
    )
    if not m:
        result.passed = False
        result.findings.append("Chapter 4 Table 4.3.1 idempotent block not found")
        return
    block = m.group(1)
    _expect(
        result,
        "Iernut" in block,
        "Table 4.3.1 missing Iernut row",
    )
    _expect(
        result,
        "7.114" in block,
        "Table 4.3.1 Iernut row missing composite 7.114",
    )


def _check_61(result: CheckResult) -> None:
    chap4 = _read(CHAPTERS / "04_results_and_findings.md")
    m = re.search(
        r"<!-- begin: table-4\.3\.2 -->(.*?)<!-- end: table-4\.3\.2 -->",
        chap4,
        re.DOTALL,
    )
    if not m:
        result.passed = False
        result.findings.append("Chapter 4 Table 4.3.2 idempotent block not found")
        return
    block = m.group(1)
    _expect(result, "Braila" in block, "Table 4.3.2 missing Braila row")
    _expect(result, "Romag Termo" in block, "Table 4.3.2 missing Romag Termo row")


def _check_63(result: CheckResult) -> None:
    """No 'cohort' token in reader-facing chapter or annex prose."""
    bad: list[str] = []
    for root in (CHAPTERS, ANNEXES):
        for md in sorted(root.rglob("*.md")):
            text = _read(md)
            for m in re.finditer(r"\bcohort\b", text, re.IGNORECASE):
                line_no = text.count("\n", 0, m.start()) + 1
                bad.append(f"{md.relative_to(REPO_ROOT)}:{line_no}")
                break
    if bad:
        result.passed = False
        result.findings.extend(["cohort hit in: " + p for p in bad])
    else:
        result.findings.append("0 cohort hits in chapters + annexes")


def _check_70(result: CheckResult) -> None:
    path = CHAPTERS / "05_country_and_site_profiles.md"
    text = _read(path)
    _expect(
        result,
        "5.2 Country Profiles and Top Sites" in text,
        f"§5.2 heading missing in {path}",
    )
    header_hits = re.findall(
        r"^\|\s*Country\s*\|\s*Current profile\s*\|", text, re.MULTILINE,
    )
    _expect(
        result,
        len(header_hits) == 1,
        f"§5.2 country-index table appears {len(header_hits)} times (expected 1)",
    )


CHECKS: dict[str, tuple[Callable[[CheckResult], None], str]] = {
    "32": (
        _check_32,
        "Stage 1 handoff paragraph in §2.7 (Chapter 2) — reviewer-approved ack-close.",
    ),
    "38": (
        _check_38,
        "Stage 3 framing propagated into Chapter 6 opener + §3.3 + §3.10 cross-references.",
    ),
    "43": (
        _check_43,
        "Baseline weights across Tables 3.2-3.6 sum to 100.00% (idempotent blocks).",
    ),
    "50": (
        _check_50,
        "§3.9 reflects 33-site full-pass set; three Romanian leaders present in Table 3.9.",
    ),
    "54": (
        _check_54_57,
        "Chapter 4 narrative cites canonical regenerated tables; no 'Cohort:' captions.",
    ),
    "57": (
        _check_54_57,
        "Chapter 4 cross-country surface is the canonical regional view (Tables 4.1.1 / 4.3.1 / 4.3.2).",
    ),
    "60": (
        _check_60,
        "Iernut row visible in Table 4.3.1 with composite 7.114.",
    ),
    "61": (
        _check_61,
        "Braila + Romag Termo rows visible in Table 4.3.2.",
    ),
    "63": (
        _check_63,
        "'cohort' replaced with 'set' across chapter + annex prose (rubric YAML + Table 4.1.1 generator updated).",
    ),
    "70": (
        _check_70,
        "§5.2 country-index table present exactly once (no duplicate sibling tables).",
    ),
}


def load_triage() -> list[dict]:
    data = yaml.safe_load(TRIAGE_YAML.read_text(encoding="utf-8"))
    items = data["items"] if isinstance(data, dict) and "items" in data else data
    return items


def main() -> int:
    items = load_triage()
    by_id = {it["id"]: it for it in items}
    results: list[CheckResult] = []
    for cid in sorted(OVIDIU_IDS, key=int):
        spec = by_id.get(cid)
        if spec is None:
            res = CheckResult(
                comment_id=cid,
                closure_status="<missing>",
                description="comment id not found in triage YAML",
                passed=False,
            )
            res.findings.append(f"#{cid} not in triage YAML")
            results.append(res)
            continue
        check_fn, description = CHECKS[cid]
        res = CheckResult(
            comment_id=cid,
            closure_status=spec.get("closure_status", "open"),
            description=description,
        )
        check_fn(res)
        results.append(res)

    print(f"{'ID':>5} {'STATUS':22} {'PASS':6} Anchor check")
    print("-" * 100)
    for res in results:
        pass_marker = "PASS" if res.passed else "FAIL"
        print(
            f"#{res.comment_id:>4} {res.closure_status:22} {pass_marker:6} {res.description}"
        )
        for note in res.findings:
            prefix = "      "
            print(f"{prefix}- {note}")

    JSON_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_REPORT_PATH.write_text(
        json.dumps(
            {
                "ovidiu_comment_ids": sorted(OVIDIU_IDS, key=int),
                "results": [asdict(r) for r in results],
                "all_passed": all(r.passed for r in results),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nReport written to {JSON_REPORT_PATH.relative_to(REPO_ROOT)}")

    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
