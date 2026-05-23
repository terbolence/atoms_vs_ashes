# man_hours: 2.9
"""Build the v1.2 stakeholder work-audit synthesis deliverable."""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from report_docx_postprocess import postprocess_docx
from report_format_config import (
    DEFAULT_FORMAT_PATH,
    ReportFormatConfig,
    ensure_reference_docx,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = (
    REPO_ROOT
    / "report/version 1.02/output/report/chapters/05_country_and_site_profiles/data"
)
MAN_HOURS_SUMMARY = REPO_ROOT / "audit/man_hours_summary.md"
EXECUTIVE_BRIEF = REPO_ROOT / "report/version 1.02/output/report/executive_technical_brief.md"
EXPERT_PROMPTS = (
    REPO_ROOT / "experts/report/stakeholder_nuclear_engineering_expert.md",
    REPO_ROOT / "experts/report/stakeholder_energy_transition_expert.md",
    REPO_ROOT / "experts/report/stakeholder_management_consultant.md",
)

PUBLISHED_COUNTRIES: tuple[str, ...] = (
    "AT", "BA", "BG", "CZ", "HR", "HU", "LV", "MD", "ME",
    "MK", "PL", "RO", "RS", "SK", "TR", "UA",
)
OUTPUT_STEM = "atoms_vs_ashes_work_audit_synthesis"


@dataclass(frozen=True)
class ProjectMetrics:
    effort_hours: str
    effort_days: str
    documentation_lines: str
    documentation_pages: str
    documentation_files: str
    python_lines: str
    python_files: str
    criteria_count: str
    connector_count: str
    total_files: str
    total_lines: str


@dataclass(frozen=True)
class ScopeMetrics:
    countries: int
    published_site_records: int
    scored_records: int
    full_pass_records: int
    avoidance_records: int
    hard_fail_records: int


def _summary_text() -> str:
    return MAN_HOURS_SUMMARY.read_text(encoding="utf-8") if MAN_HOURS_SUMMARY.exists() else ""


def _match(text: str, pattern: str, default: str = "not available") -> str:
    found = re.search(pattern, text, re.MULTILINE)
    return found.group(1) if found else default


def _project_metrics(summary: str) -> ProjectMetrics:
    effort = _match(summary, r"Estimated professional effort\*\* \| \*\*([0-9,]+) person-hours")
    days = _match(summary, r"person-hours\*\* \(~([0-9,]+) person-days")
    docs = re.search(
        r"Written documentation\*\* \| \*\*([0-9,]+)\*\* lines \(\~([0-9,]+) pages\) in \*\*([0-9,]+)\*\* files",
        summary,
    )
    python = re.search(
        r"Computer programs \(Python\)\*\* \| \*\*([0-9,]+)\*\* lines in \*\*([0-9,]+)\*\* files",
        summary,
    )
    total = re.search(
        r"All tracked project files\*\* \| \*\*([0-9,]+)\*\* files, \*\*([0-9,]+)\*\* total lines",
        summary,
    )
    return ProjectMetrics(
        effort_hours=effort,
        effort_days=days,
        documentation_lines=docs.group(1) if docs else "not available",
        documentation_pages=docs.group(2) if docs else "not available",
        documentation_files=docs.group(3) if docs else "not available",
        python_lines=python.group(1) if python else "not available",
        python_files=python.group(2) if python else "not available",
        criteria_count=_match(summary, r"Siting criteria defined\*\* \| \*\*([0-9,]+)\*\*"),
        connector_count=_match(summary, r"External map & data connectors\*\* \| \*\*([0-9,]+)\*\*"),
        total_files=total.group(1) if total else "not available",
        total_lines=total.group(2) if total else "not available",
    )


def _truthy(value: str) -> bool:
    return value.strip().lower() == "true"


def _scope_metrics() -> ScopeMetrics:
    published_site_records = 0
    scored_records = 0
    full_pass_records = 0
    avoidance_records = 0
    hard_fail_records = 0
    for country_code in PUBLISHED_COUNTRIES:
        path = DATA_DIR / f"{country_code}_site_ledger.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                published_site_records += 1
                if row.get("composite_score", "").strip():
                    scored_records += 1
                passed_exclusionary = _truthy(row.get("passed_exclusionary", ""))
                passed_avoidance = _truthy(row.get("passed_avoidance", ""))
                if passed_exclusionary and passed_avoidance:
                    full_pass_records += 1
                elif passed_exclusionary:
                    avoidance_records += 1
                else:
                    hard_fail_records += 1
    return ScopeMetrics(
        countries=len(PUBLISHED_COUNTRIES),
        published_site_records=published_site_records,
        scored_records=scored_records,
        full_pass_records=full_pass_records,
        avoidance_records=avoidance_records,
        hard_fail_records=hard_fail_records,
    )


def _check_expert_prompts() -> list[str]:
    missing = [str(path) for path in EXPERT_PROMPTS if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing expert prompt(s): " + ", ".join(missing))
    return [path.read_text(encoding="utf-8").splitlines()[1].lstrip("# ").strip() for path in EXPERT_PROMPTS]


def _source_boundary_sentence() -> str:
    if not EXECUTIVE_BRIEF.exists():
        return (
            "The source report is a Stage 1-2 screening and ranking product; it does not "
            "replace licensing, design-basis site characterisation, or investment approval."
        )
    text = EXECUTIVE_BRIEF.read_text(encoding="utf-8")
    match = re.search(r"The scope is deliberately bounded\.(.+?investment decision.+?public-acceptance finding\.)", text, re.DOTALL)
    if not match:
        return (
            "The source report is a Stage 1-2 screening and ranking product; it does not "
            "replace licensing, design-basis site characterisation, or investment approval."
        )
    return " ".join(("The scope is deliberately bounded." + match.group(1)).split())


def _build_markdown(markdown_path: Path) -> dict[str, str | int]:
    summary = _summary_text()
    project = _project_metrics(summary)
    scope = _scope_metrics()
    expert_titles = _check_expert_prompts()
    boundary = _source_boundary_sentence()

    text = f"""# Atoms vs Ashes Work Audit Synthesis

## Purpose and Boundaries

This stakeholder synthesis explains what the v1.2 report is, what it is not, what the platform can become, and what level of professional effort is represented by the current project archive. {boundary}

The report is a screening-grade decision-support product. It is strongest as a portfolio triage tool: it identifies which brownfield thermal sites justify detailed Stage 3 characterisation, which sites need an issue-specific unlock review, and which existing thermal portfolios do not contain an exclusionary-pass NuScale VOYGR-6 brownfield candidate. It is not a licence application, construction approval, vendor selection, final investment decision, environmental impact assessment, land-title opinion, grid-connection study, emergency-plan approval, or public-acceptance finding.

## Scale of Work Performed

| Evidence of effort | Current value | Stakeholder meaning |
| :--- | ---: | :--- |
| Estimated professional effort | {project.effort_hours} person-hours, about {project.effort_days} person-days | Indicates a substantial built capability, not only a writing exercise. |
| Written documentation | {project.documentation_lines} lines, about {project.documentation_pages} pages in {project.documentation_files} files | Shows the depth of criteria, audit, report, and evidence-control material. |
| Python software | {project.python_lines} lines in {project.python_files} files | Shows that the work includes repeatable screening, scoring, connector, GUI, and reporting machinery. |
| Siting criteria | {project.criteria_count} specification documents | Provides the structured safety and implementation rubric behind the report. |
| External map and data connectors | {project.connector_count} integrated sources | Supports repeatable evidence gathering from public geospatial and infrastructure datasets. |
| Tracked project archive | {project.total_files} files and {project.total_lines} total lines | Captures the software, report, data exports, and audit trail as a controlled body of work. |
| Actual man-days | 25 | Recorded execution effort for the current delivery period. |
| Supplementary days | 10 | Additional support capacity associated with the delivery. |
| Cash spent | EUR 4,200 | Direct cash expenditure recorded for stakeholder reporting. |

The v1.2 published country ledgers cover {scope.countries} countries and {scope.published_site_records} site records. Of these, {scope.scored_records} records have composite scores, {scope.full_pass_records} clear both the exclusionary and avoidance screens, {scope.avoidance_records} pass the exclusionary screen but retain an avoidance flag, and {scope.hard_fail_records} are removed at the exclusionary screen. This mix is important for governance: the platform does not simply rank sites; it separates first-wave candidates, conditional unlock candidates, and hard constraints.

The original stakeholder need can be stated simply: identify Central, Eastern and Southern European coal and thermal sites that could become SMR candidates, and show power-export scale and site surface area. A reliable answer required the process above because those two infrastructure indicators are only useful after the site has been passed through exclusionary gates, avoidance checks, national scoring, sensitivity testing and map review. A programmatic workflow was needed because the evidence volume is too large for a dependable manual table: hundreds of sites, repeated country rules, changing ledgers, site bundles, map assets and revision cycles. The programmatic approach makes the list reproducible, allows rapid iteration when evidence changes, and keeps the same screening logic across all countries.

## Integrated Strategic Synthesis

The answer for a senior stakeholder is that Atoms vs Ashes is not only a report; it is an evidence platform for capital allocation in early nuclear and industrial-site redevelopment. The platform converts a large regional population of coal and thermal assets into a ranked set of decision pathways: progress to detailed characterisation, resolve a defined unlock issue, or stop because a hard screening constraint has been triggered.

This matters because brownfield SMR screening is a multi-variable investment question. Legacy power capacity and site surface area are necessary indicators, but they do not answer the siting question by themselves. The commercially useful answer comes from combining those indicators with safety gates, grid and cooling context, emergency-planning feasibility, industrial-hazard screening, national rank stability and evidence-quality controls.

The resulting value proposition is practical. For Nuclearelectrica and similar owners or governments, the platform can shorten the long list, prioritise scarce technical studies, make partner discussions more evidence-based, and show why each site is a first-wave candidate, a conditional unlock case, or an unsuitable brownfield option. For investors and institutions, it creates a transparent basis for sequencing diligence rather than treating all coal-site conversion opportunities as equal.

## Development Potential

The immediate product direction is to harden the current nuclear-siting workflow. Useful next modules include national evidence reconciliation, design-envelope comparison across SMR and large-nuclear technologies, Stage 3 work-package generation, ownership and land-control due diligence, grid and cooling confirmation, regulator-facing evidence packs, and scenario dashboards for national programmes.

A second product direction is multi-technology redevelopment screening. The platform can be extended to compare industrial redevelopment pathways, provided each pathway has its own criteria and acceptance logic. For example, a brownfield thermal site could be assessed for SMR, large nuclear, battery storage, hydrogen, heat offtake, grid-support assets, CCUS interfaces, or hybrid industrial platforms. The product value is not a single answer; it is a structured view of which option deserves the next study budget.

The third direction is institutional decision support. A utility or ministry could use the platform as a live portfolio register, an evidence-gap tracker, and a transparent basis for sequencing feasibility spending. Investors and development banks could use it to understand which sites have resolvable constraints and which constraints are structural.

## Stakeholder Takeaway

The v1.2 report should be read as a controlled Stage 1-2 screening product backed by a substantial software, data, criteria, and audit system. Its core contribution is clarity: it distinguishes candidates ready for detailed characterisation, candidates that need targeted unlock work, and sites that should not proceed under the current brownfield NuScale VOYGR-6 envelope.

The platform's future value is broader than the report. It can become a repeatable decision engine for nuclear siting, industrial-site reuse, and energy-infrastructure portfolio strategy, provided each extension preserves the same discipline: explicit criteria, traceable evidence, uncertainty labelling, conservative claim boundaries, and validation before stakeholder use.
"""
    markdown_path.write_text(text, encoding="utf-8")
    return {
        "markdown": str(markdown_path),
        "countries": scope.countries,
        "published_site_records": scope.published_site_records,
        "expert_viewpoints": len(expert_titles),
    }


def _run_pandoc(markdown_path: Path, output_docx: Path, reference_docx: Path) -> None:
    if shutil.which("pandoc") is None:
        raise RuntimeError("pandoc not found on PATH; install pandoc first.")
    markdown_path = markdown_path.resolve()
    output_docx = output_docx.resolve()
    reference_docx = reference_docx.resolve()
    command = [
        "pandoc",
        markdown_path.name,
        "-o",
        str(output_docx),
        "--from=markdown+pipe_tables+header_attributes+fenced_code_blocks",
        "--to=docx",
        "--standalone",
        f"--reference-doc={reference_docx}",
        "--metadata",
        "title=Atoms vs Ashes Work Audit Synthesis",
    ]
    subprocess.run(command, check=True, cwd=markdown_path.parent)


def build_work_audit_synthesis(
    *,
    format_path: Path = DEFAULT_FORMAT_PATH,
    output_dir: Path | None = None,
) -> dict[str, str | int]:
    fmt = ReportFormatConfig.load(format_path)
    build_dir = output_dir or fmt.report_root / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = build_dir / f"{OUTPUT_STEM}.md"
    output_docx = build_dir / f"{OUTPUT_STEM}.docx"
    stats = _build_markdown(markdown_path)
    reference_docx = ensure_reference_docx(fmt)
    _run_pandoc(markdown_path, output_docx, reference_docx)
    postprocess_docx(output_docx, fmt)
    stats["docx"] = str(output_docx)
    return stats


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", type=Path, default=DEFAULT_FORMAT_PATH)
    parser.add_argument("--output-dir", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    stats = build_work_audit_synthesis(
        format_path=args.format,
        output_dir=args.output_dir,
    )
    print(
        "Built work-audit synthesis deliverable: "
        f"{stats['docx']} ({stats['expert_viewpoints']} expert viewpoints)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
