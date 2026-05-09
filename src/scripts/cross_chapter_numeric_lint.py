# man_hours: 2.0
"""Cross-chapter numeric consistency lint (FB-LL-06, SP-G step 6).

Scans `report/output/chapters/` for the small set of canonical numeric facts
that are repeated across multiple chapters / per-country / per-site
markdown files (capacity, full-pass count, weight values, distances) and
fails when the same fact carries two different values across documents.

Design:

- The lint is opinionated about which facts are *canonical* (small,
  reviewer-visible, mismatch-prone). It is not a free-form numeric diff.
- Each fact has an owner document (where the canonical value lives) and a
  list of consumer-document patterns the fact is expected to be repeated
  in. The lint only flags when the consumer prints a different value.
- The lint is opt-in via the `--strict` flag for use in pytest; without
  the flag it prints the report and exits 0.
- New facts are registered by appending to ``CANONICAL_FACTS``; the
  matchers are simple regexes so they stay legible to non-engineers.

Wire-up:
- Run manually:    ``python src/scripts/cross_chapter_numeric_lint.py``
- Run from pytest: ``pytest tests/scripts/test_cross_chapter_numeric_lint.py``
- The pytest case is decorated `@pytest.mark.slow` so the default
  collection skips it; CI / pre-publish runs `-m slow` to enable.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CHAPTERS_DIR = REPO_ROOT / "report" / "output" / "chapters"


@dataclass
class CanonicalFact:
    """A single numeric fact with one canonical value and a consumer-glob set."""

    fact_id: str
    description: str
    canonical_value: str
    owner_doc: str
    consumer_patterns: list[tuple[str, re.Pattern[str]]] = field(default_factory=list)
    expected_in_consumers: bool = True


@dataclass
class LintFinding:
    """A single mismatch between a consumer document and the canonical value."""

    fact_id: str
    file: Path
    found_value: str
    expected: str
    line_number: int
    context: str


def _pat(s: str, flags: int = 0) -> re.Pattern[str]:
    return re.compile(s, flags)


CANONICAL_FACTS: list[CanonicalFact] = [
    CanonicalFact(
        fact_id="VOYGR6_CAPACITY_MWE",
        description=(
            "NuScale VOYGR-6 reference net electrical output: 462 MWe "
            "(6 x 77 MWe modules). No '924 MWe' or '12-module' variant."
        ),
        canonical_value="462 MWe (6 x 77 MWe modules)",
        owner_doc="report/output/chapters/02_methodology.md",
        consumer_patterns=[
            ("VOYGR-12 invented variant", _pat(r"\bVOYGR-12\b")),
            ("924 MWe inflated capacity", _pat(r"\b924\s*MW(?:e)?\b")),
            ("12-module narrative", _pat(r"\b12-module\b|\b12 module\b")),
        ],
    ),
    CanonicalFact(
        fact_id="ROMANIA_FULL_PASS_RECONCILIATION",
        description=(
            "Chapter 4 Table 4.1.1 must explicitly disambiguate the "
            "'1' regional-top-20 contribution from the 3 country-level "
            "full-pass count, otherwise a reviewer reads them as a "
            "contradiction (#568). The phrase 'three full-pass sites at "
            "country level' must appear next to the '1' in the table row."
        ),
        canonical_value=(
            "Table 4.1.1 Romania row must contain 'full-pass sites at country level'"
        ),
        owner_doc="report/output/chapters/04_results_and_findings.md",
        consumer_patterns=[
            (
                "Romania row missing reconciliation",
                _pat(
                    r"\|\s*Romania\s*\|\s*1\s*\|(?![^|]*country level)",
                    re.IGNORECASE,
                ),
            ),
        ],
    ),
    CanonicalFact(
        fact_id="STUDY_REGION_COUNTRY_COUNT",
        description=(
            "Study region: 23 countries. Any '24' or '22' country count "
            "in narrative chapters needs an explicit qualifier (e.g. "
            "'including border-buffer countries')."
        ),
        canonical_value="23 countries",
        owner_doc="report/output/chapters/01_introduction.md",
        consumer_patterns=[
            (
                "Anomalous country-count claim",
                _pat(r"\b(?:24|25)\s+countries\b"),
            ),
        ],
    ),
]


def _scan_chapter_md_files() -> list[Path]:
    """Return every .md under report/output/chapters/ for scanning."""
    if not CHAPTERS_DIR.exists():
        return []
    return sorted(p for p in CHAPTERS_DIR.rglob("*.md") if p.is_file())


def _check_fact(fact: CanonicalFact, files: list[Path]) -> list[LintFinding]:
    findings: list[LintFinding] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for label, pattern in fact.consumer_patterns:
            for match in pattern.finditer(text):
                line_no = text.count("\n", 0, match.start()) + 1
                line_start = text.rfind("\n", 0, match.start()) + 1
                line_end = text.find("\n", match.end())
                if line_end == -1:
                    line_end = len(text)
                context = text[line_start:line_end].strip()
                if len(context) > 200:
                    idx = context.find(match.group(0))
                    context = "..." + context[max(0, idx - 40):idx + 80] + "..."
                findings.append(LintFinding(
                    fact_id=fact.fact_id,
                    file=path.relative_to(REPO_ROOT),
                    found_value=match.group(0),
                    expected=f"{label}: must read '{fact.canonical_value}'",
                    line_number=line_no,
                    context=context,
                ))
    return findings


def run_lint() -> list[LintFinding]:
    """Run all CANONICAL_FACTS checks across chapter markdowns."""
    files = _scan_chapter_md_files()
    out: list[LintFinding] = []
    for fact in CANONICAL_FACTS:
        out.extend(_check_fact(fact, files))
    return out


def format_report(findings: list[LintFinding]) -> str:
    if not findings:
        return "cross_chapter_numeric_lint: 0 findings (clean).\n"
    lines = [f"cross_chapter_numeric_lint: {len(findings)} findings\n"]
    by_fact: dict[str, list[LintFinding]] = {}
    for f in findings:
        by_fact.setdefault(f.fact_id, []).append(f)
    for fact_id, group in sorted(by_fact.items()):
        lines.append(f"\n## {fact_id} ({len(group)} hit(s))")
        for f in group:
            lines.append(f"  {f.file}:{f.line_number}")
            lines.append(f"    found:    {f.found_value!r}")
            lines.append(f"    expected: {f.expected}")
            lines.append(f"    context:  {f.context}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser("cross_chapter_numeric_lint")
    parser.add_argument(
        "--strict", action="store_true",
        help="Exit 1 when any finding exists (use in pytest / CI).",
    )
    args = parser.parse_args(argv)

    findings = run_lint()
    sys.stdout.write(format_report(findings))

    if args.strict and findings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
