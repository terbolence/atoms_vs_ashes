# man_hours: 6.0
"""Filesystem and git-backed metrics for ``man_hours_report.py``."""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

# Directories never counted (virtualenvs, caches, vendored trees).
SKIP_DIR_NAMES = frozenset({
    ".git",
    ".venv",
    "venv",
    "venv_test",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    ".ipynb_checkpoints",
})

# Chars per token heuristics (English/code; see OpenAI/Anthropic public guidance ~4 chars/token
# for prose; code tokenizes denser — ~3.5–3.8 chars/token).
CHARS_PER_TOKEN = {
    "python": 3.6,
    "markdown": 4.0,
    "yaml": 3.8,
    "default": 4.0,
}

# Indicative agentic-dev multipliers (documented in summary; not measured).
INPUT_TO_OUTPUT_RATIO = 6.0
THINKING_FRACTION = 0.28

PYTHON_BUCKETS: list[tuple[str, str]] = [
    ("src/atoms_vs_ashes", "Application package"),
    ("src/scripts", "Operational scripts"),
    ("src/ava_client", "AVA integration client"),
    ("src/alembic", "Database migrations"),
    ("tests", "Automated tests"),
    ("export", "Export tooling"),
]

MARKDOWN_BUCKETS: list[tuple[str, str]] = [
    ("criteria", "Siting criteria specs"),
    ("report/requirements", "Report requirements"),
    ("architecture", "Architecture specs"),
    ("experts", "Expert / LLM prompts"),
    ("docs", "Technical documentation"),
    ("audit", "Audit trail and QA"),
    ("report", "Client report (full tree)"),
    ("sources", "Data-source research notes"),
]

YAML_BUCKETS: list[tuple[str, str]] = [
    ("config", "Runtime configuration"),
    ("audit", "Audit registry and metadata"),
]

# Product software + specs (customer-facing engineering scope).
CLOC_PRODUCT_AREAS: list[tuple[str, str]] = [
    ("src/atoms_vs_ashes", "Application package"),
    ("src/scripts", "Operational scripts"),
    ("src/ava_client", "AVA integration client"),
    ("src/alembic", "Database migrations"),
    ("tests", "Automated tests"),
    ("criteria", "Siting criteria"),
    ("config", "Configuration"),
    ("experts", "Expert prompts"),
    ("docs", "Documentation"),
    ("export", "Export tooling"),
    ("architecture", "Architecture specs"),
]

# Audit trail (often large JSON/CSV post-processing artefacts — reported separately).
CLOC_AUDIT_AREAS: list[tuple[str, str]] = [
    ("audit", "Audit trail & post-processing"),
]

# Full repository scan paths (git-tracked via ``cloc --vcs=git``).
CLOC_FULL_PATHS: list[str] = [
    "src",
    "tests",
    "criteria",
    "config",
    "experts",
    "docs",
    "architecture",
    "export",
    "report",
    "audit",
    "sources",
    "data",
]

# Plain-English labels for top-level folders (project inventory).
PROJECT_FOLDER_LABELS: dict[str, str] = {
    "_root": "Project guides (README, AGENTS, etc.)",
    "report": "Client report & deliverables",
    "audit": "Quality audits & verification records",
    "src": "Software source (programs & specifications)",
    "tests": "Automated quality checks",
    "criteria": "Siting criteria (official rubric text)",
    "docs": "Technical reference documentation",
    "experts": "Expert review prompts (AI-assisted QA)",
    "architecture": "System design documents",
    "config": "Scoring rules & configuration",
    "export": "Data export tools",
    "sources": "External data source notes",
    "data": "Bundled reference data descriptors",
    ".cursor": "Editor automation (internal)",
}

LINES_PER_PAGE_ESTIMATE = 45

# Primary languages shown first in customer tables.
CLOC_PRIMARY_LANGS = frozenset({"Python", "Markdown", "YAML", "JSON", "Bourne Shell"})


@dataclass
class FileStats:
    files: int = 0
    lines: int = 0
    chars: int = 0


@dataclass
class TokenEstimate:
    output_tokens: int
    input_tokens: int
    thinking_tokens: int
    chars_by_kind: dict[str, int] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.output_tokens + self.input_tokens + self.thinking_tokens


@dataclass
class LlmLogUsage:
    response_files: int
    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class ClocLanguageRow:
    language: str
    n_files: int
    blank: int
    comment: int
    code: int

    @property
    def total_lines(self) -> int:
        return self.blank + self.comment + self.code

    @property
    def prose_lines(self) -> int:
        return self.total_lines

    @property
    def comment_ratio_pct(self) -> float:
        denom = self.code + self.comment
        return (100.0 * self.comment / denom) if denom else 0.0


@dataclass
class ClocAreaRow:
    label: str
    path: str
    n_files: int
    blank: int
    comment: int
    code: int
    top_language: str

    @property
    def total_lines(self) -> int:
        return self.blank + self.comment + self.code

    @property
    def prose_lines(self) -> int:
        """All physical lines in this area (code + comment + blank)."""
        return self.total_lines


@dataclass
class ClocReport:
    version: str
    elapsed_seconds: float
    languages: list[ClocLanguageRow]
    areas: list[ClocAreaRow]
    n_files: int
    code: int
    comment: int
    blank: int
    scope: str = "product"

    @property
    def total_lines(self) -> int:
        return self.code + self.comment + self.blank

    @property
    def comment_ratio_pct(self) -> float:
        denom = self.code + self.comment
        return (100.0 * self.comment / denom) if denom else 0.0

    def language(self, name: str) -> ClocLanguageRow | None:
        for row in self.languages:
            if row.language == name:
                return row
        return None


def _path_skipped(path: Path) -> bool:
    return any(part in SKIP_DIR_NAMES for part in path.parts)


def git_ls_files(root: Path, *pathspecs: str) -> list[Path]:
    """Return tracked paths under *root* (empty if not a git repo)."""
    if not (root / ".git").exists():
        return []
    cmd = ["git", "-C", str(root), "ls-files", "-z", "--", *pathspecs]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if proc.returncode != 0:
        return []
    out: list[Path] = []
    for chunk in proc.stdout.split(b"\0"):
        if not chunk:
            continue
        rel = chunk.decode("utf-8", errors="replace")
        out.append(root / rel)
    return out


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def stats_for_paths(paths: Iterable[Path]) -> FileStats:
    stats = FileStats()
    for path in paths:
        if not path.is_file() or _path_skipped(path):
            continue
        text = _read_text(path)
        if text is None:
            continue
        stats.files += 1
        stats.lines += len(text.splitlines())
        stats.chars += len(text)
    return stats


def stats_git_glob(root: Path, prefix: str, suffix: str) -> FileStats:
    """Tracked files under *prefix* matching *suffix* (e.g. ``.py``)."""
    spec = f"{prefix}/**/*{suffix}" if prefix else f"**/*{suffix}"
    paths = [
        p
        for p in git_ls_files(root, spec)
        if p.suffix.lower() == suffix and not _path_skipped(p)
    ]
    return stats_for_paths(paths)


def stats_git_tree(
    root: Path,
    prefix: str,
    suffix: str,
    *,
    exclude_prefixes: tuple[str, ...] = (),
) -> FileStats:
    """Tracked files with *suffix* under *prefix*, minus *exclude_prefixes* subtrees."""
    base = root / prefix
    if not base.is_dir():
        return FileStats()
    paths = git_ls_files(root, f"{prefix}/" if prefix else ".")
    exclude_bases = [root / ex for ex in exclude_prefixes]
    filtered: list[Path] = []
    for p in paths:
        if p.suffix.lower() != suffix or not p.is_relative_to(base) or _path_skipped(p):
            continue
        if any(p.is_relative_to(ex) and p != ex for ex in exclude_bases):
            continue
        filtered.append(p)
    return stats_for_paths(filtered)


def walk_tree_stats(
    root: Path,
    prefix: str,
    suffix: str,
    *,
    exclude_prefixes: tuple[str, ...] = (),
) -> FileStats:
    """Fallback when git is unavailable: walk *root/prefix* skipping SKIP_DIR_NAMES."""
    base = root / prefix
    if not base.is_dir():
        return FileStats()
    exclude_bases = [root / ex for ex in exclude_prefixes]
    stats = FileStats()
    for dirpath, dirnames, filenames in os.walk(base, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
        for fn in filenames:
            if not fn.lower().endswith(suffix):
                continue
            p = Path(dirpath) / fn
            if _path_skipped(p):
                continue
            if any(p.is_relative_to(ex) and p != ex for ex in exclude_bases):
                continue
            text = _read_text(p)
            if text is None:
                continue
            stats.files += 1
            stats.lines += len(text.splitlines())
            stats.chars += len(text)
    return stats


def measure_bucket(
    root: Path,
    prefix: str,
    suffix: str,
    *,
    exclude_prefixes: tuple[str, ...] = (),
) -> FileStats:
    stats = stats_git_tree(root, prefix, suffix, exclude_prefixes=exclude_prefixes)
    if stats.files == 0 and (root / ".git").exists():
        stats = walk_tree_stats(
            root, prefix, suffix, exclude_prefixes=exclude_prefixes,
        )
    return stats


# Markdown bucket → optional subtrees counted elsewhere.
MARKDOWN_EXCLUDES: dict[str, tuple[str, ...]] = {
    "Client report (full tree)": ("report/requirements",),
}


def collect_python_metrics(root: Path) -> dict[str, FileStats]:
    return {label: measure_bucket(root, prefix, ".py") for prefix, label in PYTHON_BUCKETS}


def collect_markdown_metrics(root: Path) -> dict[str, FileStats]:
    out: dict[str, FileStats] = {}
    for prefix, label in MARKDOWN_BUCKETS:
        ex = MARKDOWN_EXCLUDES.get(label, ())
        out[label] = measure_bucket(root, prefix, ".md", exclude_prefixes=ex)
    return out


def collect_yaml_metrics(root: Path) -> dict[str, FileStats]:
    out: dict[str, FileStats] = {}
    for prefix, label in YAML_BUCKETS:
        st = measure_bucket(root, prefix, ".yaml")
        st = _merge_stats(st, measure_bucket(root, prefix, ".yml"))
        out[label] = st
    return out


def total_tracked_by_suffix(root: Path, suffixes: tuple[str, ...]) -> FileStats:
    """Deduped repo-wide totals for file suffixes (git-tracked)."""
    seen: set[str] = set()
    paths: list[Path] = []
    for suf in suffixes:
        for p in git_ls_files(root, f"**/*{suf}"):
            if p.suffix.lower() != suf or _path_skipped(p):
                continue
            key = str(p.resolve())
            if key in seen:
                continue
            seen.add(key)
            paths.append(p)
    if paths:
        return stats_for_paths(paths)
    total = FileStats()
    for area in (
        "criteria", "src", "tests", "audit", "config", "docs", "experts",
        "report", "sources", "architecture", "export",
    ):
        for suf in suffixes:
            total = _merge_stats(total, walk_tree_stats(root, area, suf))
    return total


def _merge_stats(a: FileStats, b: FileStats) -> FileStats:
    return FileStats(
        files=a.files + b.files,
        lines=a.lines + b.lines,
        chars=a.chars + b.chars,
    )


def _sum_stats(stats: dict[str, FileStats]) -> FileStats:
    total = FileStats()
    for s in stats.values():
        total = _merge_stats(total, s)
    return total


def count_criteria_specs(root: Path) -> int:
    crit = root / "criteria"
    if not crit.is_dir():
        return 0
    return sum(1 for p in crit.rglob("*.md") if p.is_file() and not _path_skipped(p))


def count_connector_packages(root: Path) -> int:
    conn = root / "src" / "atoms_vs_ashes" / "connectors"
    if not conn.is_dir():
        return 0
    return sum(
        1
        for p in conn.iterdir()
        if p.is_dir()
        and not p.name.startswith("_")
        and (p / "__init__.py").is_file()
    )


def count_expert_prompts(root: Path) -> int:
    exp = root / "experts"
    if not exp.is_dir():
        return 0
    return sum(1 for p in exp.rglob("*.md") if p.is_file() and not _path_skipped(p))


def estimate_tokens_from_chars(chars_by_kind: dict[str, int]) -> TokenEstimate:
    output = 0.0
    for kind, chars in chars_by_kind.items():
        if chars <= 0:
            continue
        cpt = CHARS_PER_TOKEN.get(kind, CHARS_PER_TOKEN["default"])
        output += chars / cpt
    output_tokens = int(round(output))
    input_tokens = int(round(output_tokens * INPUT_TO_OUTPUT_RATIO))
    thinking_tokens = int(
        round((output_tokens + input_tokens) * THINKING_FRACTION)
    )
    return TokenEstimate(
        output_tokens=output_tokens,
        input_tokens=input_tokens,
        thinking_tokens=thinking_tokens,
        chars_by_kind=dict(chars_by_kind),
    )


def build_chars_by_kind(
    py_total: FileStats,
    md_total: FileStats,
    yaml_total: FileStats,
) -> dict[str, int]:
    return {
        "python": py_total.chars,
        "markdown": md_total.chars,
        "yaml": yaml_total.chars,
    }


def scan_llm_logs(
    root: Path,
    *,
    max_response_files: int = 400,
) -> LlmLogUsage | None:
    """Sum tokens from ``logs/llm/*/responses/*.json`` when present."""
    base = root / "logs" / "llm"
    if not base.is_dir():
        return None
    inp = out = 0
    n_files = 0
    try:
        for run_e in os.scandir(base):
            if n_files >= max_response_files:
                break
            if not run_e.is_dir() or run_e.name.startswith("."):
                continue
            resp = Path(run_e.path) / "responses"
            if not resp.is_dir():
                continue
            with os.scandir(resp) as resp_it:
                for fe in resp_it:
                    if n_files >= max_response_files:
                        break
                    if not fe.name.endswith(".json"):
                        continue
                    try:
                        data = json.loads(Path(fe.path).read_text(encoding="utf-8"))
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
        return None
    if n_files == 0:
        return None
    return LlmLogUsage(response_files=n_files, input_tokens=inp, output_tokens=out)


def _cloc_exclude_arg() -> str:
    return f"--exclude-dir={','.join(sorted(SKIP_DIR_NAMES))}"


def _cloc_available() -> bool:
    try:
        proc = subprocess.run(
            ["cloc", "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        return proc.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def run_cloc_json(
    root: Path,
    paths: list[str],
    *,
    timeout: int = 90,
) -> dict | None:
    """Run ``cloc --json --vcs=git`` on *paths* relative to *root*."""
    existing = [p for p in paths if (root / p).exists()]
    if not existing or not _cloc_available():
        return None
    cmd = [
        "cloc",
        "--quiet",
        "--json",
        "--vcs=git",
        _cloc_exclude_arg(),
        *existing,
    ]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def parse_cloc_languages(data: dict) -> list[ClocLanguageRow]:
    rows: list[ClocLanguageRow] = []
    for key, val in data.items():
        if key in ("header", "SUM") or not isinstance(val, dict):
            continue
        rows.append(
            ClocLanguageRow(
                language=key,
                n_files=int(val.get("nFiles", 0)),
                blank=int(val.get("blank", 0)),
                comment=int(val.get("comment", 0)),
                code=int(val.get("code", 0)),
            )
        )
    rows.sort(key=lambda r: (-r.code, r.language))
    return rows


def parse_cloc_sum(data: dict) -> tuple[int, int, int, int]:
    s = data.get("SUM") or {}
    return (
        int(s.get("nFiles", data.get("header", {}).get("n_files", 0))),
        int(s.get("code", 0)),
        int(s.get("comment", 0)),
        int(s.get("blank", 0)),
    )


def _top_language_from_json(data: dict) -> str:
    best_lang, best_code = "—", 0
    for key, val in data.items():
        if key in ("header", "SUM") or not isinstance(val, dict):
            continue
        code = int(val.get("code", 0))
        if code > best_code:
            best_code = code
            best_lang = key
    return best_lang


def _build_cloc_report(
    root: Path,
    area_defs: list[tuple[str, str]],
    *,
    scope: str,
) -> ClocReport | None:
    area_paths = [p for p, _ in area_defs if (root / p).is_dir()]
    if not area_paths:
        return None
    aggregate = run_cloc_json(root, area_paths)
    if not aggregate:
        return None
    header = aggregate.get("header") or {}
    n_files, code, comment, blank = parse_cloc_sum(aggregate)
    languages = parse_cloc_languages(aggregate)
    areas: list[ClocAreaRow] = []
    for path, label in area_defs:
        if not (root / path).is_dir():
            continue
        area_data = run_cloc_json(root, [path], timeout=45)
        if not area_data:
            continue
        af, ac, acm, ab = parse_cloc_sum(area_data)
        areas.append(
            ClocAreaRow(
                label=label,
                path=path,
                n_files=af,
                blank=ab,
                comment=acm,
                code=ac,
                top_language=_top_language_from_json(area_data),
            )
        )
    areas.sort(key=lambda a: -a.code)
    return ClocReport(
        version=str(header.get("cloc_version", "?")),
        elapsed_seconds=float(header.get("elapsed_seconds", 0)),
        languages=languages,
        areas=areas,
        n_files=n_files,
        code=code,
        comment=comment,
        blank=blank,
        scope=scope,
    )


@dataclass
class ExtensionStats:
    files: int = 0
    lines: int = 0


@dataclass
class ProjectAreaRow:
    """One top-level folder (or project root files)."""

    folder: str
    label: str
    prose: ExtensionStats
    programs: ExtensionStats
    settings: ExtensionStats
    data_tables: ExtensionStats
    other_files: int = 0

    @property
    def prose_pages_est(self) -> int:
        return max(0, round(self.prose.lines / LINES_PER_PAGE_ESTIMATE))

    @property
    def total_files(self) -> int:
        return (
            self.prose.files
            + self.programs.files
            + self.settings.files
            + self.data_tables.files
            + self.other_files
        )


@dataclass
class ProjectInventory:
    areas: list[ProjectAreaRow]
    prose: FileStats
    programs: FileStats
    settings: FileStats
    data_tables: FileStats
    large_prose: list[tuple[int, str]]

    @property
    def prose_pages_est(self) -> int:
        return max(0, round(self.prose.lines / LINES_PER_PAGE_ESTIMATE))


def _top_level_folder(rel: str) -> str:
    parts = Path(rel).parts
    return "_root" if len(parts) == 1 else parts[0]


def _line_count_file(path: Path) -> int:
    text = _read_text(path)
    if text is None:
        return 0
    return len(text.splitlines())


def collect_project_inventory(root: Path) -> ProjectInventory:
    """Git-tracked files grouped by top-level folder with line counts."""
    buckets: dict[str, ProjectAreaRow] = {}
    large: list[tuple[int, str]] = []

    for path in git_ls_files(root):
        if not path.is_file() or _path_skipped(path):
            continue
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            continue
        folder = _top_level_folder(rel)
        if folder not in buckets:
            label = PROJECT_FOLDER_LABELS.get(folder, folder.replace("_", " ").title())
            buckets[folder] = ProjectAreaRow(folder=folder, label=label, prose=ExtensionStats(), programs=ExtensionStats(), settings=ExtensionStats(), data_tables=ExtensionStats())
        row = buckets[folder]
        lines = _line_count_file(path)
        suffix = path.suffix.lower()
        if suffix == ".md":
            row.prose.files += 1
            row.prose.lines += lines
            if lines >= 400:
                large.append((lines, str(rel)))
        elif suffix == ".py":
            row.programs.files += 1
            row.programs.lines += lines
        elif suffix in (".yaml", ".yml"):
            row.settings.files += 1
            row.settings.lines += lines
        elif suffix in (".json", ".csv"):
            row.data_tables.files += 1
            row.data_tables.lines += lines
        else:
            row.other_files += 1

    areas = sorted(buckets.values(), key=lambda r: -(r.prose.lines + r.programs.lines + r.data_tables.lines))
    large.sort(reverse=True)

    prose = FileStats()
    programs = FileStats()
    settings = FileStats()
    data_tables = FileStats()
    for row in areas:
        prose.files += row.prose.files
        prose.lines += row.prose.lines
        programs.files += row.programs.files
        programs.lines += row.programs.lines
        settings.files += row.settings.files
        settings.lines += row.settings.lines
        data_tables.files += row.data_tables.files
        data_tables.lines += row.data_tables.lines

    return ProjectInventory(
        areas=areas,
        prose=prose,
        programs=programs,
        settings=settings,
        data_tables=data_tables,
        large_prose=large[:15],
    )


@dataclass
class ClocBundle:
    product: ClocReport | None
    audit: ClocReport | None
    full: ClocReport | None


def collect_cloc_reports(root: Path) -> ClocBundle:
    """Product, audit, and full-repository ``cloc`` scans."""
    full_paths = [p for p in CLOC_FULL_PATHS if (root / p).is_dir()]
    full_report: ClocReport | None = None
    if full_paths:
        aggregate = run_cloc_json(root, full_paths, timeout=120)
        if aggregate:
            header = aggregate.get("header") or {}
            n_files, code, comment, blank = parse_cloc_sum(aggregate)
            areas: list[ClocAreaRow] = []
            for path in full_paths:
                label = PROJECT_FOLDER_LABELS.get(path, path)
                area_data = run_cloc_json(root, [path], timeout=60)
                if not area_data:
                    continue
                af, ac, acm, ab = parse_cloc_sum(area_data)
                md = area_data.get("Markdown")
                py = area_data.get("Python")
                dom = "—"
                if isinstance(py, dict) and isinstance(md, dict):
                    dom = "Python" if int(py.get("code", 0)) >= int(md.get("code", 0)) else "Markdown"
                elif isinstance(py, dict):
                    dom = "Python"
                elif isinstance(md, dict):
                    dom = "Markdown"
                areas.append(
                    ClocAreaRow(
                        label=label,
                        path=path,
                        n_files=af,
                        blank=ab,
                        comment=acm,
                        code=ac,
                        top_language=dom,
                    )
                )
            areas.sort(key=lambda a: -a.total_lines)
            full_report = ClocReport(
                version=str(header.get("cloc_version", "?")),
                elapsed_seconds=float(header.get("elapsed_seconds", 0)),
                languages=parse_cloc_languages(aggregate),
                areas=areas,
                n_files=n_files,
                code=code,
                comment=comment,
                blank=blank,
                scope="full",
            )
    return ClocBundle(
        product=_build_cloc_report(root, CLOC_PRODUCT_AREAS, scope="product"),
        audit=_build_cloc_report(root, CLOC_AUDIT_AREAS, scope="audit"),
        full=full_report,
    )
