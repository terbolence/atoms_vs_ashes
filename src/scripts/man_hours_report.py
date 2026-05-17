# man_hours: 7.0
"""Generate audit/man_hours_summary.md — plain-language project scale report.

Usage:
    python src/scripts/man_hours_report.py
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _man_hours_metrics import (  # noqa: E402
    INPUT_TO_OUTPUT_RATIO,
    LINES_PER_PAGE_ESTIMATE,
    THINKING_FRACTION,
    ClocBundle,
    ClocReport,
    FileStats,
    ExtensionStats,
    ProjectAreaRow,
    ProjectInventory,
    build_chars_by_kind,
    collect_cloc_reports,
    collect_project_inventory,
    count_connector_packages,
    count_criteria_specs,
    count_expert_prompts,
    estimate_tokens_from_chars,
    scan_llm_logs,
    total_tracked_by_suffix,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = PROJECT_ROOT / "audit" / "man_hours_registry.yml"
DEFAULT_OUTPUT = PROJECT_ROOT / "audit" / "man_hours_summary.md"

# Registry categories → plain English (for non-software readers).
CATEGORY_PLAIN: dict[str, str] = {
    "Requirements & Analysis": "Requirements & regulatory research",
    "Architecture & Design": "System design",
    "Implementation": "Building the screening software",
    "Testing": "Testing & verification",
    "Database & Migrations": "Database structure",
    "Configuration & DevOps": "Configuration & tooling",
    "Research & Data Sources": "External data source research",
    "AI Prompts & Tooling": "AI expert prompts & automation",
    "Project Management & QA": "Project management & quality records",
    "Connectors & Data Acquisition": "Map & API data integrations",
    "Report Authoring & Documentation": "Report writing",
    "Documentation": "Documentation",
    "Expert Systems": "Expert review systems",
    "Reporting & Visualization": "Charts & visual outputs",
    "Testing & Quality Assurance": "Extra QA",
    "Other": "Other",
}

CATEGORY_ORDER = list(CATEGORY_PLAIN.keys()) + ["Other"]


def load_registry(path: Path) -> dict[str, dict]:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("files", {})


def _fmt(n: int) -> str:
    return f"{n:,}"


def _pages(lines: int) -> str:
    p = max(1, round(lines / LINES_PER_PAGE_ESTIMATE)) if lines else 0
    return f"~{p:,} pages" if p else "—"


def build_how_to_read() -> str:
    return (
        "## How to read this report\n\n"
        "This document describes the **size and composition** of the Atoms vs Ashes "
        "siting screening project — the software, written specifications, client report "
        "material, and quality records kept under version control.\n\n"
        "- **Lines of text** — every line in a file (like counting lines in Word).\n"
        "- **Estimated pages** — rough print equivalent (~"
        f"{LINES_PER_PAGE_ESTIMATE} lines per page of dense text).\n"
        "- **Person-hours** — estimated senior professional time to produce each part "
        "(from our internal registry, not a timesheet).\n"
        "- Counts include **only files tracked in git** (the official project archive). "
        "Large downloaded map files on disk are excluded.\n\n"
        "---\n\n"
    )


def build_at_a_glance(
    inv: ProjectInventory,
    hours: float,
    criteria: int,
    connectors: int,
    cloc: ClocReport | None,
) -> str:
    sw = inv.programs
    lines = [
        "## At a glance\n\n",
        "| | |\n",
        "| --- | --- |\n",
        f"| **Estimated professional effort** | **{hours:,.0f} person-hours** "
        f"(~{hours / 8:,.0f} person-days at 8 h/day) |\n",
        f"| **Written documentation** | **{_fmt(inv.prose.lines)}** lines "
        f"({_pages(inv.prose.lines)}) in **{_fmt(inv.prose.files)}** files |\n",
        f"| **Computer programs (Python)** | **{_fmt(sw.lines)}** lines in "
        f"**{_fmt(sw.files)}** files |\n",
        f"| **Siting criteria defined** | **{criteria}** specification documents |\n",
        f"| **External map & data connectors** | **{connectors}** integrated sources |\n",
    ]
    if cloc is not None:
        lines.append(
            f"| **All tracked project files** | **{_fmt(cloc.n_files)}** files, "
            f"**{_fmt(cloc.total_lines)}** total lines (programs + prose + tables) |\n"
        )
    lines.append("\n---\n\n")
    return "".join(lines)


def build_platform_section(criteria: int, connectors: int, experts: int) -> str:
    return (
        "## What the platform includes\n\n"
        "Atoms vs Ashes is a **screening and ranking system** for coal-to-nuclear "
        "and brownfield SMR sites against international siting criteria.\n\n"
        "| Component | Count | What it is |\n"
        "| --- | ---: | --- |\n"
        f"| Siting criteria | **{criteria}** | Formal rubric documents (natural hazards, "
        "grid, land, emergency planning, etc.) |\n"
        f"| Data connectors | **{connectors}** | Automated links to public geospatial "
        "and infrastructure datasets (seismic, flood, population, grid, …) |\n"
        f"| Expert prompts | **{experts}** | Structured instructions for AI-assisted "
        "quality review |\n"
        "| Screening engine | 1 | Scores and ranks hundreds of candidate sites |\n"
        "| Operator interface | 1 | Dashboard to run analyses and inspect results |\n\n"
        "---\n\n"
    )


def _area_table_rows(areas: list[ProjectAreaRow]) -> str:
    lines = [
        "| Part of the project | Files | Lines of text | Est. pages |\n",
        "| --- | ---: | ---: | ---: |\n",
    ]
    for row in areas:
        if row.prose.files == 0:
            continue
        lines.append(
            f"| {row.label} | {_fmt(row.prose.files)} | {_fmt(row.prose.lines)} | "
            f"{_pages(row.prose.lines)} |\n"
        )
    return "".join(lines)


def build_written_docs(inv: ProjectInventory) -> str:
    large = ""
    if inv.large_prose:
        large = "\n### Largest individual documents\n\n| Lines | Document |\n| ---: | --- |\n"
        for n, rel in inv.large_prose[:12]:
            name = Path(rel).name
            large += f"| {_fmt(n)} | {name} (`{rel}`) |\n"
        large += "\n"

    return (
        "## Written documentation\n\n"
        f"The project contains **{_fmt(inv.prose.lines)} lines** of Markdown documentation "
        f"(**{_pages(inv.prose.lines)}**, **{_fmt(inv.prose.files)}** files). "
        "This is the main body of prose: criteria, the client report, audits, "
        "architecture notes, and technical references.\n\n"
        "### Where the writing lives\n\n"
        + _area_table_rows(inv.areas)
        + f"\n| **Total** | **{_fmt(inv.prose.files)}** | **{_fmt(inv.prose.lines)}** | "
        f"**{_pages(inv.prose.lines)}** |\n"
        + large
        + "---\n\n"
    )


def build_software_section(inv: ProjectInventory, cloc: ClocReport | None) -> str:
    py_lines = inv.programs.lines
    test_row = next((a for a in inv.areas if a.folder == "tests"), None)
    src_row = next((a for a in inv.areas if a.folder == "src"), None)
    src_only = src_row.programs.lines if src_row else py_lines

    body = (
        "## Computer programs\n\n"
        f"The screening **software** is **{_fmt(py_lines)} lines** of Python "
        f"(**{_fmt(inv.programs.files)}** files), plus configuration in YAML.\n\n"
        "| Component | Lines | Role |\n"
        "| --- | ---: | --- |\n"
        f"| Main application (`src/`) | **{_fmt(src_only)}** | Scoring, maps, database, "
        "connectors, user interface |\n"
    )
    if test_row and test_row.programs.lines:
        body += (
            f"| Automated tests (`tests/`) | **{_fmt(test_row.programs.lines)}** | "
            "Checks that scoring behaves correctly |\n"
        )
    body += (
        f"| Configuration (YAML) | **{_fmt(inv.settings.lines)}** | "
        "Scoring weights, thresholds, rubrics |\n\n"
    )
    if cloc is not None:
        py = cloc.language("Python")
        if py:
            body += (
                f"*Analyst note: automated counters classify **{_fmt(py.code)}** lines as "
                f"\"active program text\", **{_fmt(py.comment)}** as inline documentation "
                f"in code, and **{_fmt(py.blank)}** as blank lines — total "
                f"**{_fmt(py.total_lines)}** for Python across the whole repository.*\n\n"
            )
    body += "---\n\n"
    return body


def build_data_outputs_section(inv: ProjectInventory) -> str:
    dt = inv.data_tables
    if dt.files == 0:
        return ""
    audit_row = next((a for a in inv.areas if a.folder == "audit"), None)
    audit_dt = audit_row.data_tables if audit_row else ExtensionStats()
    return (
        "## Spreadsheet & data exports (audit trail)\n\n"
        f"Separate from prose and programs, the repository holds **{_fmt(dt.files)}** "
        f"machine-readable **JSON/CSV** files (**{_fmt(dt.lines)}** lines). "
        "These are scoring outputs, verification tables, and sensitivity analyses — "
        "not meant to be read cover-to-cover.\n\n"
        f"- **In `audit/` alone:** {_fmt(audit_dt.files)} files, "
        f"**{_fmt(audit_dt.lines)}** lines (bulk of the data exports).\n"
        "- Typical use: evidence for a criterion, national ranking charts, "
        "before/after comparisons.\n\n"
        "---\n\n"
    )


def _registry_plain_name(cat: str) -> str:
    return CATEGORY_PLAIN.get(cat, cat)


def build_effort_section(by_category: dict[str, list[tuple[str, float]]]) -> str:
    rows: list[tuple[str, float, int]] = []
    for cat, entries in by_category.items():
        rows.append((_registry_plain_name(cat), sum(h for _, h in entries), len(entries)))
    rows.sort(key=lambda r: -r[1])

    lines = [
        "## Professional effort (person-hours)\n\n",
        "Estimated **senior professional time** to reach the current state of the project "
        "(research, design, implementation, review). "
        "Rounded totals from `audit/man_hours_registry.yml`.\n\n",
        "| Work area | Hours | ~Days (8 h) | Files counted |\n",
        "| --- | ---: | ---: | ---: |\n",
    ]
    total_h = 0.0
    total_f = 0
    for label, hrs, nfiles in rows:
        if hrs <= 0:
            continue
        lines.append(
            f"| {label} | {hrs:,.1f} | {hrs / 8:,.0f} | {nfiles} |\n"
        )
        total_h += hrs
        total_f += nfiles
    lines.append(
        f"| **Total** | **{total_h:,.1f}** | **{total_h / 8:,.0f}** | **{total_f}** |\n\n"
        "---\n\n"
    )
    return "".join(lines)


def build_ai_section(token_est, llm_logs) -> str:
    lines = [
        "## AI assistance (indicative)\n\n",
        "Much of the repository was produced with AI coding tools. "
        "The figures below are **rough models**, not invoices.\n\n",
        "| | Estimated tokens |\n",
        "| --- | ---: |\n",
        f"| Text stored in the repository (output) | **{_fmt(token_est.output_tokens)}** |\n",
        f"| Reading & revising during development (input) | **{_fmt(token_est.input_tokens)}** |\n",
        f"| Extended reasoning steps (thinking) | **{_fmt(token_est.thinking_tokens)}** |\n",
        f"| **Combined model** | **{_fmt(token_est.total_tokens)}** |\n\n",
        f"*Method: character counts in tracked Python, Markdown, and YAML; "
        f"≈×{INPUT_TO_OUTPUT_RATIO:.0f} input multiplier; "
        f"{THINKING_FRACTION:.0%} thinking allowance.*\n\n",
    ]
    if llm_logs is not None:
        lines.append(
            f"Where API logging is enabled, **{_fmt(llm_logs.total_tokens)}** tokens were "
            f"recorded locally across **{llm_logs.response_files}** saved responses "
            f"(input {_fmt(llm_logs.input_tokens)}, output "
            f"{_fmt(llm_logs.output_tokens)}).\n\n"
        )
    lines.append("---\n\n")
    return "".join(lines)


def build_full_inventory_table(inv: ProjectInventory) -> str:
    lines = [
        "## Complete project inventory (all file types)\n\n",
        "Every **top-level folder** in the git archive:\n\n",
        "| Folder | Plain name | Prose (.md) | Programs (.py) | "
        "Settings (.yml) | Data (.json/.csv) | Other files |\n",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |\n",
    ]
    for row in inv.areas:
        lines.append(
            f"| `{row.folder}` | {row.label} | "
            f"{_fmt(row.prose.lines)} / {row.prose.files}f | "
            f"{_fmt(row.programs.lines)} / {row.programs.files}f | "
            f"{_fmt(row.settings.lines)} / {row.settings.files}f | "
            f"{_fmt(row.data_tables.lines)} / {row.data_tables.files}f | "
            f"{row.other_files} |\n"
        )
    lines.append(
        f"| **Total** | | **{_fmt(inv.prose.lines)}** | **{_fmt(inv.programs.lines)}** | "
        f"**{_fmt(inv.settings.lines)}** | **{_fmt(inv.data_tables.lines)}** | |\n\n"
        "---\n\n"
    )
    return "".join(lines)


def build_technical_appendix(bundle: ClocBundle) -> str:
    cloc = bundle.full
    if cloc is None:
        return (
            "<details><summary>Technical appendix (line-type analysis)</summary>\n\n"
            "*Install `cloc` and re-run the report generator to include this section.*\n\n"
            "</details>\n\n"
        )
    lines = [
        "<details><summary>Technical appendix (line-type analysis for specialists)</summary>\n\n",
        f"Produced with **cloc {cloc.version}** on git-tracked files. "
        f"**Code** = logical source lines; **comment** = documentation embedded in code; "
        f"**blank** = empty lines.\n\n",
        "### Whole repository\n\n",
        "| | Lines |\n",
        "| --- | ---: |\n",
        f"| Code | {_fmt(cloc.code)} |\n",
        f"| Comment | {_fmt(cloc.comment)} |\n",
        f"| Blank | {_fmt(cloc.blank)} |\n",
        f"| **Physical total** | **{_fmt(cloc.total_lines)}** |\n\n",
        "### By folder (physical lines)\n\n",
        "| Area | Folder | Files | Code | Comment | Blank | Total |\n",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |\n",
    ]
    for area in cloc.areas:
        lines.append(
            f"| {area.label} | `{area.path}` | {_fmt(area.n_files)} | "
            f"{_fmt(area.code)} | {_fmt(area.comment)} | {_fmt(area.blank)} | "
            f"{_fmt(area.total_lines)} |\n"
        )
    lines.append("\n</details>\n\n")
    return "".join(lines)


def build_registry_appendix(by_category: dict[str, list[tuple[str, float]]]) -> str:
    lines = [
        "<details><summary>Detailed person-hour registry (all files)</summary>\n\n",
    ]
    all_cats = sorted(by_category.keys(), key=lambda c: -sum(h for _, h in by_category[c]))
    for cat in all_cats:
        entries = by_category[cat]
        if not entries:
            continue
        entries.sort(key=lambda e: (-e[1], e[0]))
        hrs = sum(h for _, h in entries)
        lines.append(f"### {_registry_plain_name(cat)}\n\n")
        lines.append(f"**{len(entries)}** files, **{hrs:.1f}** hours\n\n")
        lines.append("| File | Hours |\n| --- | ---: |\n")
        for fpath, h in entries:
            lines.append(f"| `{fpath}` | {h:.1f} |\n")
        lines.append("\n")
    lines.append("</details>\n\n")
    return "".join(lines)


def build_report(files: dict[str, dict], root: Path) -> str:
    by_category: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for fpath, info in sorted(files.items()):
        by_category[info.get("category", "Other")].append(
            (fpath, float(info.get("hours", 0)))
        )

    inv = collect_project_inventory(root)
    py_total = total_tracked_by_suffix(root, (".py",))
    md_total = total_tracked_by_suffix(root, (".md",))
    yaml_total = total_tracked_by_suffix(root, (".yaml", ".yml"))
    token_est = estimate_tokens_from_chars(
        build_chars_by_kind(py_total, md_total, yaml_total)
    )
    llm_logs = scan_llm_logs(root)
    cloc_bundle = collect_cloc_reports(root)
    registry_hours = sum(float(i.get("hours", 0)) for i in files.values())
    criteria = count_criteria_specs(root)
    connectors = count_connector_packages(root)
    experts = count_expert_prompts(root)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    parts = [
        "<!-- man_hours: 3.0 -->\n",
        "# Atoms vs Ashes — Project Scale Report\n\n",
        f"**Generated:** {now}  \n",
        "**Purpose:** Summarise how large the siting screening project is — in words, "
        "software, data, and professional effort.  \n",
        f"**Scope:** All files tracked in the project git archive "
        f"({root.name}/).\n\n",
        "---\n\n",
        build_how_to_read(),
        build_at_a_glance(inv, registry_hours, criteria, connectors, cloc_bundle.full),
        build_platform_section(criteria, connectors, experts),
        build_written_docs(inv),
        build_software_section(inv, cloc_bundle.full),
        build_data_outputs_section(inv),
        build_effort_section(by_category),
        build_ai_section(token_est, llm_logs),
        build_full_inventory_table(inv),
        build_technical_appendix(cloc_bundle),
        build_registry_appendix(by_category),
        "---\n\n",
        f"*Generated by `python src/scripts/man_hours_report.py` · "
        f"{len(files)} registry entries · cloc "
        f"{cloc_bundle.full.version if cloc_bundle.full else 'n/a'}*\n",
    ]
    return "".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate project scale report")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    files = load_registry(args.registry)
    if not files:
        print(f"No files in {args.registry}")
        return

    args.output.write_text(build_report(files, PROJECT_ROOT), encoding="utf-8")
    total = sum(float(i.get("hours", 0)) for i in files.values())
    print(f"Wrote {args.output} — {len(files)} registry files, {total:.1f} h")


if __name__ == "__main__":
    main()
