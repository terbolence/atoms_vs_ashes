# man_hours: 3.5
"""Reproducible engineering-effort metrics: man-hours headers, LOC, REST log counts, LLM tokens.

Usage:
    python scripts/report_effort_metrics.py
    python scripts/report_effort_metrics.py --write-report
    python scripts/report_effort_metrics.py --write-report --scan-logs --loc
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_ROOT = PROJECT_ROOT / "logs"

MAN_HOURS_LINE = re.compile(r"^#\s*man_hours:\s*([0-9]+(?:\.[0-9]+)?)\s*$", re.I)
SKIP_DIR_NAMES = frozenset({".venv", "venv", "__pycache__", ".git", "node_modules"})


def sum_man_hours(paths: list[Path]) -> tuple[float, int]:
    """Walk each tree once; only read allowed suffixes."""
    total = 0.0
    files_with_tag = 0
    for root in paths:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root, topdown=True):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
            for fn in filenames:
                low = fn.lower()
                if not (
                    low.endswith(".py")
                    or low.endswith(".md")
                    or low.endswith(".yml")
                    or low.endswith(".yaml")
                ):
                    continue
                p = Path(dirpath) / fn
                try:
                    text = p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                for line in text.splitlines():
                    m = MAN_HOURS_LINE.match(line.strip())
                    if m:
                        total += float(m.group(1))
                        files_with_tag += 1
                        break
    return total, files_with_tag


def line_counts_tracked_python(dirs: list[Path]) -> dict[str, int]:
    """Line counts for tracked ``*.py`` under ``src/``, ``tests/``, ``alembic/`` via ``wc -l`` (chunked)."""
    prefixes = [str(d.relative_to(PROJECT_ROOT)) for d in dirs if d.is_dir()]
    out: dict[str, int] = {p: 0 for p in prefixes}
    proc = subprocess.run(
        ["git", "ls-files", "--"] + prefixes,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        return {p: -1 for p in prefixes}
    rels = [
        ln.strip()
        for ln in proc.stdout.splitlines()
        if ln.strip().endswith(".py")
        and "/.venv/" not in ln
        and "/venv/" not in ln
        and "/__pycache__/" not in ln
    ]
    if not rels:
        return out
    # Chunked ``wc`` — a single huge ``wc -l`` on cloud-backed trees can block for minutes.
    chunk_size = 20
    per_chunk_timeout = 12
    for i in range(0, len(rels), chunk_size):
        batch = rels[i : i + chunk_size]
        paths = [str(PROJECT_ROOT / r) for r in batch]
        try:
            wproc = subprocess.run(
                ["wc", "-l", *paths],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                check=False,
                timeout=per_chunk_timeout,
            )
        except subprocess.TimeoutExpired:
            for p in prefixes:
                out[p] = -1
            return out
        if wproc.returncode != 0 or not wproc.stdout:
            for p in prefixes:
                out[p] = -1
            return out
        for line in wproc.stdout.strip().splitlines():
            parts = line.strip().split()
            if len(parts) < 2 or parts[-1].lower() == "total":
                continue
            try:
                n = int(parts[0])
            except ValueError:
                continue
            path_part = parts[-1].replace("\\", "/")
            for pref in prefixes:
                needle = f"/{pref}/"
                if path_part.endswith(".py") and (
                    needle in path_part or path_part.startswith(pref + "/")
                ):
                    out[pref] += n
                    break
    return out


def try_cloc() -> str | None:
    dirs = ["src", "tests", "alembic"]
    try:
        proc = subprocess.run(
            ["cloc", "--quiet", "--sum-one"] + dirs,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def count_rest_request_logs(*, max_runs_per_subsystem: int = 100) -> dict[str, int]:
    """Count request JSONs under ``logs/<subsystem>/<run>/requests/`` (bounded per subsystem)."""
    counts: dict[str, int] = defaultdict(int)
    if not LOGS_ROOT.is_dir():
        return dict(counts)
    try:
        with os.scandir(LOGS_ROOT) as top:
            subsystems_seen = 0
            for sub_entry in top:
                if subsystems_seen >= 40:
                    break
                if not sub_entry.is_dir() or sub_entry.name.startswith("."):
                    continue
                subsystems_seen += 1
                subsystem = Path(sub_entry.path)
                n = 0
                runs_used = 0
                try:
                    with os.scandir(subsystem) as run_it:
                        for entry in run_it:
                            if runs_used >= max_runs_per_subsystem:
                                break
                            if not entry.is_dir() or entry.name.startswith("."):
                                continue
                            runs_used += 1
                            req = Path(entry.path) / "requests"
                            if not req.is_dir():
                                continue
                            try:
                                with os.scandir(req) as rq:
                                    for fe in rq:
                                        if fe.name.endswith(".json"):
                                            n += 1
                            except OSError:
                                continue
                except OSError:
                    continue
                if n:
                    counts[subsystem.name] = n
    except OSError:
        return dict(counts)
    return dict(sorted(counts.items()))


def aggregate_llm_usage(*, max_response_files: int = 400) -> tuple[int, int, int]:
    """Sum input/output tokens from ``logs/llm/<run_id>/responses/*.json`` (capped file reads)."""
    inp = out = 0
    n_files = 0
    base = LOGS_ROOT / "llm"
    if not base.is_dir():
        return 0, 0, 0
    try:
        runs_seen = 0
        for run_e in os.scandir(base):
            if n_files >= max_response_files or runs_seen >= 80:
                break
            if not run_e.is_dir() or run_e.name.startswith("."):
                continue
            runs_seen += 1
            resp = Path(run_e.path) / "responses"
            if not resp.is_dir():
                continue
            try:
                with os.scandir(resp) as resp_it:
                    for fe in resp_it:
                        if n_files >= max_response_files:
                            break
                        if not fe.name.endswith(".json"):
                            continue
                        jf = Path(fe.path)
                        try:
                            data = json.loads(jf.read_text(encoding="utf-8"))
                        except (json.JSONDecodeError, OSError):
                            continue
                        usage = data.get("usage") if isinstance(data, dict) else None
                        if not isinstance(usage, dict):
                            continue
                        in_tok = usage.get("input_tokens")
                        out_tok = usage.get("output_tokens")
                        if isinstance(in_tok, int):
                            inp += in_tok
                        if isinstance(out_tok, int):
                            out += out_tok
                        n_files += 1
            except OSError:
                continue
    except OSError:
        pass
    return inp, out, n_files


def build_report(
    *,
    with_cloc: bool = False,
    with_loc: bool = False,
    scan_logs: bool = False,
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    src_h, src_n = sum_man_hours([PROJECT_ROOT / "src"])
    test_h, test_n = sum_man_hours([PROJECT_ROOT / "tests"])
    alembic_h, alembic_n = sum_man_hours([PROJECT_ROOT / "alembic"])
    scripts_h, scripts_n = sum_man_hours([PROJECT_ROOT / "scripts"])
    total_h = src_h + test_h + alembic_h + scripts_h
    total_files = src_n + test_n + alembic_n + scripts_n

    loc = (
        line_counts_tracked_python(
            [PROJECT_ROOT / "src", PROJECT_ROOT / "tests", PROJECT_ROOT / "alembic"]
        )
        if with_loc
        else {}
    )
    cloc_out = try_cloc() if with_cloc else None
    if scan_logs:
        rest = count_rest_request_logs()
        llm_in, llm_out, llm_resp_files = aggregate_llm_usage()
    else:
        rest = {}
        llm_in = llm_out = llm_resp_files = 0

    lines: list[str] = [
        "<!-- Generated by scripts/report_effort_metrics.py -->\n",
        "# Effort metrics report\n\n",
        f"**Generated (UTC):** {now}\n\n",
        "## `# man_hours:` line headers\n\n",
        "Convention: first-line `# man_hours: N.N` in source files (engineering-time estimate).\n\n",
        "| Scope | Files tagged | Sum (hours) |\n",
        "| --- | ---: | ---: |\n",
        f"| `src/` | {src_n} | {src_h:.1f} |\n",
        f"| `tests/` | {test_n} | {test_h:.1f} |\n",
        f"| `alembic/` | {alembic_n} | {alembic_h:.1f} |\n",
        f"| `scripts/` | {scripts_n} | {scripts_h:.1f} |\n",
        f"| **Total** | **{total_files}** | **{total_h:.1f}** |\n\n",
        "> For registry-based totals see `audit/man_hours_registry.yml` and `scripts/man_hours_report.py`.\n\n",
        "## Lines of code (Python, `wc` on `*.py`)\n\n",
    ]
    if with_loc:
        lines.extend(
            [
                "| Directory | Lines |\n",
                "| --- | ---: |\n",
            ]
        )
        for k, v in sorted(loc.items()):
            lines.append(f"| `{k}` | {v if v >= 0 else 'n/a'} |\n")
        loc_pos = [v for v in loc.values() if v > 0]
        lines.append(f"| **Sum** | **{sum(loc_pos) if loc_pos else 'n/a'}** |\n")
        if any(v < 0 for v in loc.values()):
            lines.append(
                "\n*Line counts use chunked `wc -l` on `git ls-files` paths; a chunk timed out "
                "(common on cloud-backed working copies). Re-run on a fast disk or smaller checkout.*\n"
            )
        lines.append("\n")
    else:
        lines.append(
            "*Omitted by default (chunked `wc` on cloud-backed trees can stall). "
            "Re-run with `--loc` for tracked `*.py` line counts, or use `cloc --with-cloc`.*\n\n"
        )

    if cloc_out:
        lines.append("## `cloc` (optional — if installed)\n\n")
        lines.append("```text\n")
        lines.append(cloc_out.rstrip() + "\n")
        lines.append("```\n\n")

    lines.append("## REST request JSON logs\n\n")
    if not scan_logs:
        lines.append(
            "*Omitted by default (large or cloud-synced `logs/`). Re-run with `--scan-logs`.*\n\n"
        )
    else:
        lines.append(
            "Count of `*.json` under `logs/<subsystem>/<run_id>/requests/`, "
            "at most **100 run folders** per subsystem and **40** top-level subsystem folders.\n\n"
        )
        if rest:
            lines.append("| Subsystem (under `logs/`) | Request JSON files |\n| --- | ---: |\n")
            for k, v in rest.items():
                lines.append(f"| `{k}` | {v if v >= 0 else 'n/a'} |\n")
            pos = [v for v in rest.values() if v >= 0]
            lines.append(f"| **Total** | **{sum(pos) if pos else 'n/a'}** |\n")
            if any(v < 0 for v in rest.values()):
                lines.append(
                    "\n*Log scan returned a sentinel row (internal error or cap).*\n"
                )
            lines.append("\n")
        else:
            lines.append("*No matching request logs found.*\n\n")

    lines.append("## LLM usage from local logs\n\n")
    if not scan_logs:
        lines.append("*Omitted unless `--scan-logs` is set.*\n\n")
    elif llm_resp_files:
        lines.append(
            f"Parsed `{llm_resp_files}` response JSON files (cap 400 reads) "
            f"(`usage.input_tokens` / `usage.output_tokens`).\n\n"
        )
        lines.append("| Metric | Tokens |\n| --- | ---: |\n")
        lines.append(f"| Input | {llm_in:,} |\n")
        lines.append(f"| Output | {llm_out:,} |\n")
        lines.append(f"| **Total** | **{llm_in + llm_out:,}** |\n\n")
    else:
        lines.append(
            "*No `logs/llm/.../responses/*.json` with `usage` objects — run LLM assessments locally to populate.*\n\n"
        )

    lines.append(
        "---\n\n*Regenerate: `python scripts/report_effort_metrics.py --write-report` "
        "(`--loc`, `--with-cloc`, `--scan-logs` as needed)*\n"
    )
    return "".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Effort metrics (man-hours, LOC, log counts).")
    parser.add_argument(
        "--write-report",
        action="store_true",
        help=f"Write {REPORTS_DIR / 'effort_latest.md'} and a dated copy (no full report on stdout).",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Also print the full markdown to stdout (use alone or with --write-report).",
    )
    parser.add_argument(
        "--with-cloc",
        action="store_true",
        help="Run optional `cloc` (can be slow; skipped by default).",
    )
    parser.add_argument(
        "--loc",
        action="store_true",
        help="Include tracked-Python line counts via chunked `wc -l` (can be slow on cloud drives).",
    )
    parser.add_argument(
        "--scan-logs",
        action="store_true",
        help="Scan `logs/` for REST request JSON counts and LLM token totals (can be slow).",
    )
    args = parser.parse_args()
    report = build_report(
        with_cloc=args.with_cloc,
        with_loc=args.loc,
        scan_logs=args.scan_logs,
    )
    if args.write_report:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        latest = REPORTS_DIR / "effort_latest.md"
        dated = REPORTS_DIR / f"effort_{date.today().isoformat().replace('-', '')}.md"
        latest.write_text(report, encoding="utf-8")
        dated.write_text(report, encoding="utf-8")
        print(f"Wrote {latest} and {dated}", file=sys.stderr)
    if not args.write_report or args.print_report:
        sys.stdout.write(report)


if __name__ == "__main__":
    main()
