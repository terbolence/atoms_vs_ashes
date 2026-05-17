# man_hours: 5.5
"""Generate audit/man_hours_summary.md from audit/man_hours_registry.yml.

Usage:
    python src/scripts/man_hours_report.py
    python src/scripts/man_hours_report.py --registry path/to/registry.yml
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml

# Allow running as script without package install.
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _man_hours_metrics import (  # noqa: E402
    CHARS_PER_TOKEN,
    CLOC_PRIMARY_LANGS,
    INPUT_TO_OUTPUT_RATIO,
    THINKING_FRACTION,
    ClocLanguageRow,
    ClocBundle,
    ClocReport,
    FileStats,
    build_chars_by_kind,
    collect_cloc_reports,
    collect_markdown_metrics,
    collect_python_metrics,
    collect_yaml_metrics,
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

CATEGORY_ORDER = [
    "Requirements & Analysis",
    "Architecture & Design",
    "Implementation",
    "Testing",
    "Database & Migrations",
    "Configuration & DevOps",
    "Research & Data Sources",
    "AI Prompts & Tooling",
    "Project Management & QA",
    "Other",
]


def load_registry(path: Path) -> dict[str, dict]:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("files", {})


def _fmt_int(n: int) -> str:
    return f"{n:,}"


def _stats_table(rows: list[tuple[str, FileStats]], total_label: str) -> str:
    lines = ["| Area | Files | Lines | Characters |\n", "| --- | ---: | ---: | ---: |\n"]
    tot = FileStats()
    for label, st in rows:
        if st.files == 0 and st.lines == 0:
            continue
        lines.append(
            f"| {label} | {_fmt_int(st.files)} | {_fmt_int(st.lines)} | {_fmt_int(st.chars)} |\n"
        )
        tot.files += st.files
        tot.lines += st.lines
        tot.chars += st.chars
    lines.append(
        f"| **{total_label}** | **{_fmt_int(tot.files)}** | "
        f"**{_fmt_int(tot.lines)}** | **{_fmt_int(tot.chars)}** |\n"
    )
    return "".join(lines)


def build_executive_section(
    *,
    registry_hours: float,
    registry_files: int,
    py_total: FileStats,
    md_total: FileStats,
    yaml_total: FileStats,
    criteria_count: int,
    connector_count: int,
    expert_prompts: int,
    token_est,
    llm_logs,
    cloc_product: ClocReport | None,
) -> str:
    authored_chars = py_total.chars + md_total.chars + yaml_total.chars
    lines = [
        "## Executive summary (customer metrics)\n\n",
        "Indicative scale of the Atoms vs Ashes siting platform. "
        "Physical **source lines** (below) come from [`cloc`](https://github.com/AlDanial/cloc) "
        "with `--vcs=git` (tracked files only). Character totals use the same git scope.\n\n",
        "| Metric | Value | Notes |\n",
        "| --- | ---: | --- |\n",
        f"| Registry engineering effort | **{registry_hours:,.1f} h** | "
        f"{registry_files:,} files in `audit/man_hours_registry.yml` |\n",
    ]
    if cloc_product is not None:
        py = cloc_product.language("Python")
        md = cloc_product.language("Markdown")
        yml = cloc_product.language("YAML")
        lines.extend([
            f"| **Product source lines (`cloc` code)** | **{_fmt_int(cloc_product.code)}** | "
            f"{_fmt_int(cloc_product.n_files)} files; software + specs (excludes audit JSON/CSV) |\n",
            f"| Documentation & comments (`cloc`) | **{_fmt_int(cloc_product.comment)}** | "
            f"{cloc_product.comment_ratio_pct:.1f}% of code+comment |\n",
            f"| Python source lines (`cloc` code) | **{_fmt_int(py.code if py else 0)}** | "
            f"{_fmt_int(py.n_files if py else 0)} files |\n",
            f"| Markdown prose (`cloc` code) | **{_fmt_int(md.code if md else 0)}** | "
            "Criteria, specs, expert prompts |\n",
            f"| YAML configuration (`cloc` code) | **{_fmt_int(yml.code if yml else 0)}** | "
            "Rubrics and config |\n",
        ])
    lines.extend([
        f"| Python (git physical lines) | **{_fmt_int(py_total.lines)}** lines | "
        f"{_fmt_int(py_total.files)} files; {_fmt_int(py_total.chars)} characters |\n",
        f"| Markdown (git physical lines) | **{_fmt_int(md_total.lines)}** lines | "
        f"{_fmt_int(md_total.files)} files |\n",
        f"| YAML (git physical lines) | **{_fmt_int(yaml_total.lines)}** lines | "
        f"{_fmt_int(yaml_total.files)} files |\n",
        f"| **Total authored text** | **{_fmt_int(authored_chars)}** chars | "
        "Python + Markdown + YAML |\n",
        f"| Siting criteria specifications | **{criteria_count}** | Under `criteria/` |\n",
        f"| Geodata connector packages | **{connector_count}** | Under `src/atoms_vs_ashes/connectors/` |\n",
        f"| Expert / LLM prompt files | **{expert_prompts}** | Under `experts/` |\n",
        f"| Estimated LLM tokens (modelled) | **{_fmt_int(token_est.total_tokens)}** | "
        "See [Estimated LLM usage](#estimated-llm-usage-indicative); not invoiced usage |\n",
        f"| — output (artifact corpus) | {_fmt_int(token_est.output_tokens)} | "
        "Tokens to store current repo text |\n",
        f"| — input (context reads) | {_fmt_int(token_est.input_tokens)} | "
        f"×{INPUT_TO_OUTPUT_RATIO:.0f} vs output (agentic iteration heuristic) |\n",
        f"| — thinking / reasoning | {_fmt_int(token_est.thinking_tokens)} | "
        f"{THINKING_FRACTION:.0%} of (input + output); extended-thinking models |\n",
    ])
    if cloc_product is not None:
        lines.append(
            f"| `cloc` version / scan time | {cloc_product.version} / "
            f"{cloc_product.elapsed_seconds:.1f}s | "
            "See [Physical source analysis](#physical-source-analysis-cloc) |\n"
        )
    if llm_logs is not None:
        lines.append(
            f"| Measured LLM usage (local logs) | **{_fmt_int(llm_logs.total_tokens)}** | "
            f"`logs/llm/` — {llm_logs.response_files} response files parsed |\n"
        )
        lines.append(
            f"| — logged input / output | {_fmt_int(llm_logs.input_tokens)} / "
            f"{_fmt_int(llm_logs.output_tokens)} | When API logging is enabled |\n"
        )
    lines.append("\n---\n\n")
    return "".join(lines)


def build_python_section(py: dict[str, FileStats]) -> str:
    ordered = [(label, st) for label, st in py.items()]
    return (
        "## Python (tracked)\n\n"
        + _stats_table(ordered, "Total Python")
        + "\n---\n\n"
    )


def _sum_file_stats(stats: dict[str, FileStats]) -> FileStats:
    total = FileStats()
    for st in stats.values():
        total.files += st.files
        total.lines += st.lines
        total.chars += st.chars
    return total


def build_prose_section(
    title: str,
    metrics: dict[str, FileStats],
    *,
    footnote: str = "",
) -> str:
    ordered = list(metrics.items())
    note = (
        f"\n*{footnote}*\n\n" if footnote else "\n"
    )
    return f"## {title}\n\n{_stats_table(ordered, 'Subtotal (areas)')}{note}---\n\n"


def build_token_section(token_est, llm_logs) -> str:
    lines = [
        "## Estimated LLM usage (indicative)\n\n",
        "Rough order-of-magnitude for **AI-assisted delivery** of the current repository. "
        "This is **not** billing data; it models how many tokens would be required to "
        "**reproduce the authored corpus** plus typical agentic read/reason cycles.\n\n",
        "### Method\n\n",
        "1. Sum UTF-8 characters in tracked `.py`, `.md`, `.yaml`/`.yml` (see tables above).\n",
        "2. Convert to **output tokens** using chars/token heuristics: "
        f"Python ≈{CHARS_PER_TOKEN['python']}, Markdown ≈{CHARS_PER_TOKEN['markdown']}, "
        f"YAML ≈{CHARS_PER_TOKEN['yaml']} "
        "(aligned with public GPT/Claude guidance of ~4 characters per token for English; "
        "code is denser).\n",
        f"3. **Input tokens** ≈ output × {INPUT_TO_OUTPUT_RATIO:.0f} "
        "(files read, retries, diffs, tool results per iteration).\n",
        f"4. **Thinking tokens** ≈ {THINKING_FRACTION:.0%} × (input + output) "
        "(extended reasoning on frontier models).\n\n",
        "| Component | Characters | Chars/token | Est. tokens |\n",
        "| --- | ---: | ---: | ---: |\n",
    ]
    for kind, chars in sorted(token_est.chars_by_kind.items()):
        if chars <= 0:
            continue
        cpt = CHARS_PER_TOKEN.get(kind, CHARS_PER_TOKEN["default"])
        tok = int(round(chars / cpt))
        lines.append(f"| {kind.capitalize()} | {_fmt_int(chars)} | {cpt} | {_fmt_int(tok)} |\n")
    lines.append(
        f"| **Output (artifacts)** | | | **{_fmt_int(token_est.output_tokens)}** |\n"
    )
    lines.append(
        f"| **Input (context)** | | | **{_fmt_int(token_est.input_tokens)}** |\n"
    )
    lines.append(
        f"| **Thinking / reasoning** | | | **{_fmt_int(token_est.thinking_tokens)}** |\n"
    )
    lines.append(
        f"| **Total (modelled)** | | | **{_fmt_int(token_est.total_tokens)}** |\n\n"
    )
    if llm_logs is not None:
        lines.append(
            "### Measured usage (local `logs/llm/`)\n\n"
            f"Parsed **{llm_logs.response_files}** response JSON files: "
            f"input **{_fmt_int(llm_logs.input_tokens)}**, "
            f"output **{_fmt_int(llm_logs.output_tokens)}**, "
            f"total **{_fmt_int(llm_logs.total_tokens)}**. "
            "This is a subset of all development-time calls (caps apply; logs may be gitignored).\n\n"
        )
    else:
        lines.append(
            "*No parseable `logs/llm/*/responses/*.json` found on this machine "
            "(logs are often gitignored).*\n\n"
        )
    lines.append("---\n\n")
    return "".join(lines)


def _cloc_lang_table(rows: list[ClocLanguageRow], *, primary_only: bool) -> str:
    lines = [
        "| Language | Files | Code | Comment | Blank | Code share |\n",
        "| --- | ---: | ---: | ---: | ---: | ---: |\n",
    ]
    total_code = sum(r.code for r in rows) or 1
    for row in rows:
        if primary_only and row.language not in CLOC_PRIMARY_LANGS:
            continue
        share = 100.0 * row.code / total_code
        lines.append(
            f"| {row.language} | {_fmt_int(row.n_files)} | {_fmt_int(row.code)} | "
            f"{_fmt_int(row.comment)} | {_fmt_int(row.blank)} | {share:.1f}% |\n"
        )
    if primary_only:
        other_code = sum(r.code for r in rows if r.language not in CLOC_PRIMARY_LANGS)
        if other_code:
            other_files = sum(r.n_files for r in rows if r.language not in CLOC_PRIMARY_LANGS)
            share = 100.0 * other_code / total_code
            lines.append(
                f"| *Other languages* | {_fmt_int(other_files)} | {_fmt_int(other_code)} | "
                f"— | — | {share:.1f}% |\n"
            )
    return "".join(lines)


def _cloc_report_subsection(cloc: ClocReport, *, heading: str) -> str:
    code_pct = 100.0 * cloc.code / cloc.total_lines if cloc.total_lines else 0
    lines = [
        f"### {heading}\n\n",
        f"**{_fmt_int(cloc.n_files)}** files, **{_fmt_int(cloc.code)}** code lines "
        f"({code_pct:.1f}% of physical lines in this scope), "
        f"**{_fmt_int(cloc.comment)}** comment, **{_fmt_int(cloc.blank)}** blank. "
        f"Comment-to-code: **{cloc.comment_ratio_pct:.1f}%**.\n\n",
        "#### By language\n\n",
        _cloc_lang_table(cloc.languages, primary_only=True),
        "\n",
        "#### By area\n\n",
        "| Area | Path | Files | Code | Comment | Blank | Dominant language |\n",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |\n",
    ]
    for area in cloc.areas:
        lines.append(
            f"| {area.label} | `{area.path}` | {_fmt_int(area.n_files)} | "
            f"{_fmt_int(area.code)} | {_fmt_int(area.comment)} | {_fmt_int(area.blank)} | "
            f"{area.top_language} |\n"
        )
    lines.append("\n")
    return "".join(lines)


def build_cloc_section(bundle: ClocBundle) -> str:
    product = bundle.product
    if product is None:
        return (
            "## Physical source analysis (`cloc`)\n\n"
            "*`cloc` is not installed or the scan failed. Install with "
            "`brew install cloc` (macOS) and re-run "
            "`python src/scripts/man_hours_report.py`.*\n\n---\n\n"
        )

    lines = [
        "## Physical source analysis (`cloc`)\n\n",
        f"Generated with **cloc {product.version}** using `--vcs=git` (git-tracked files only) "
        f"and excluding virtualenvs / caches. Product scope covers application code, tests, "
        "criteria, config, and documentation — **not** bulk audit JSON/CSV exports.\n\n",
        _cloc_report_subsection(product, heading="Product engineering scope"),
    ]
    if bundle.audit is not None and bundle.audit.code > 0:
        lines.append(
            _cloc_report_subsection(
                bundle.audit,
                heading="Audit trail & post-processing artefacts",
            )
        )
        lines.extend([
            "<details><summary>All languages in audit scope</summary>\n\n",
            _cloc_lang_table(bundle.audit.languages, primary_only=False),
            "\n</details>\n\n",
        ])
    lines.extend([
        "<details><summary>All languages in product scope</summary>\n\n",
        _cloc_lang_table(product.languages, primary_only=False),
        "\n</details>\n\n",
        "### How to read this\n\n",
        "- **Code**: logical source lines (standard SLOC).\n",
        "- **Comment**: comments and docstrings.\n",
        "- **Blank**: empty lines.\n",
        "- Executive **product** totals exclude `audit/` JSON/CSV machine outputs "
        "(often 10× larger than Python). Use product figures for engineering scale.\n\n"
        "---\n\n",
    ])
    return "".join(lines)


def build_report(files: dict[str, dict], project_root: Path) -> str:
    by_category: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for fpath, info in sorted(files.items()):
        hours = float(info.get("hours", 0))
        category = info.get("category", "Other")
        by_category[category].append((fpath, hours))

    py_metrics = collect_python_metrics(project_root)
    md_metrics = collect_markdown_metrics(project_root)
    yaml_metrics = collect_yaml_metrics(project_root)

    py_total = _sum_file_stats(py_metrics)
    md_total = total_tracked_by_suffix(project_root, (".md",))
    yaml_total = total_tracked_by_suffix(project_root, (".yaml", ".yml"))

    chars_by_kind = build_chars_by_kind(py_total, md_total, yaml_total)
    token_est = estimate_tokens_from_chars(chars_by_kind)
    llm_logs = scan_llm_logs(project_root)
    cloc_bundle = collect_cloc_reports(project_root)

    registry_hours = sum(float(info.get("hours", 0)) for info in files.values())
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines: list[str] = [
        "<!-- man_hours: 3.0 -->\n",
        "# Man-Hours & Project Metrics Summary\n\n",
        f"**Generated:** {now}\n",
        f"**Sources:** `audit/man_hours_registry.yml`, git-tracked file metrics, "
        "`src/scripts/man_hours_report.py`\n\n",
        "---\n\n",
        build_executive_section(
            registry_hours=registry_hours,
            registry_files=len(files),
            py_total=py_total,
            md_total=md_total,
            yaml_total=yaml_total,
            criteria_count=count_criteria_specs(project_root),
            connector_count=count_connector_packages(project_root),
            expert_prompts=count_expert_prompts(project_root),
            token_est=token_est,
            llm_logs=llm_logs,
            cloc_product=cloc_bundle.product,
        ),
        build_python_section(py_metrics),
        build_prose_section(
            "Markdown (tracked, by area)",
            md_metrics,
            footnote=(
                f"Repo-wide deduped total: **{_fmt_int(md_total.lines)}** lines, "
                f"**{_fmt_int(md_total.files)}** files (table rows may overlap)."
            ),
        ),
        build_prose_section(
            "YAML (tracked, by area)",
            yaml_metrics,
            footnote=(
                f"Repo-wide deduped total: **{_fmt_int(yaml_total.lines)}** lines, "
                f"**{_fmt_int(yaml_total.files)}** files."
            ),
        ),
        build_cloc_section(cloc_bundle),
        build_token_section(token_est, llm_logs),
        "## Totals by category (registry)\n\n",
        "| Category | Files | Hours |\n",
        "| --- | ---: | ---: |\n",
    ]

    grand_files = 0
    grand_hours = 0.0
    seen_cats: set[str] = set()

    for cat in CATEGORY_ORDER:
        entries = by_category.get(cat, [])
        if not entries:
            continue
        seen_cats.add(cat)
        cat_hours = sum(h for _, h in entries)
        lines.append(f"| {cat} | {len(entries)} | {cat_hours:.1f} |\n")
        grand_files += len(entries)
        grand_hours += cat_hours

    for cat in sorted(by_category.keys()):
        if cat in seen_cats:
            continue
        entries = by_category[cat]
        cat_hours = sum(h for _, h in entries)
        lines.append(f"| {cat} | {len(entries)} | {cat_hours:.1f} |\n")
        grand_files += len(entries)
        grand_hours += cat_hours

    lines.append(f"| **Project total** | **{grand_files}** | **{grand_hours:.1f}** |\n")
    lines.append("\n---\n\n## Detailed breakdown (registry)\n\n")

    all_cats = [c for c in CATEGORY_ORDER if c in by_category]
    all_cats += [c for c in sorted(by_category.keys()) if c not in CATEGORY_ORDER]

    for cat in all_cats:
        entries = by_category[cat]
        entries.sort(key=lambda e: (-e[1], e[0]))
        cat_hours = sum(h for _, h in entries)
        lines.append(f"### {cat}\n\n")
        lines.append(f"**Subtotal:** {len(entries)} files, {cat_hours:.1f} hours\n\n")
        lines.append("| File | Hours |\n")
        lines.append("| --- | ---: |\n")
        for fpath, hours in entries:
            lines.append(f"| `{fpath}` | {hours:.1f} |\n")
        lines.append("\n")

    lines.append("---\n\n")
    lines.append(
        f"*Report generated by `src/scripts/man_hours_report.py` at {now}. "
        "Re-run: `python src/scripts/man_hours_report.py`*\n"
    )
    return "".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate man-hours summary report")
    parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY,
        help="Path to man_hours_registry.yml",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to write the summary Markdown",
    )
    args = parser.parse_args()

    files = load_registry(args.registry)
    if not files:
        print(f"No files found in {args.registry}")
        return

    report = build_report(files, PROJECT_ROOT)
    args.output.write_text(report, encoding="utf-8")

    total = sum(float(info.get("hours", 0)) for info in files.values())
    print(f"Wrote {args.output} — {len(files)} files, {total:.1f} total hours")


if __name__ == "__main__":
    main()
