"""Resolve a reviewer comment's heading path to a v1.03 report Markdown file.

Used by `extract_docx_comments.py`. Builds a tiny in-memory index of H1 titles
found in chapter, country-prototype, and site Markdown files; resolves
``heading_path`` (e.g. ``[Chapter 5..., Country, Site, Section]``) against that
index from most specific to least specific.

Kept as a private helper so the orchestrator stays under the 300-line budget.
"""

from __future__ import annotations

import re
from pathlib import Path

CHAPTER_PREFIX_RE = re.compile(r"^\s*(\d+)\.\s+")
H1_RE = re.compile(r"^#\s+(.+?)\s*$")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _read_h1(path: Path) -> str | None:
    try:
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                m = H1_RE.match(line)
                if m:
                    return m.group(1).strip()
        return None
    except OSError:
        return None


class ReportPathIndex:
    """Map heading text to a relative v1.03 report Markdown path."""

    def __init__(self, report_root: Path | None) -> None:
        self.report_root = report_root.resolve() if report_root else None
        self.chapters_by_number: dict[int, str] = {}
        self.chapter5_files: list[tuple[str, str]] = []
        self.chapter5_site_files: list[tuple[str, str]] = []
        if self.report_root is not None and self.report_root.is_dir():
            self._build()

    def _build(self) -> None:
        chapters_dir = self.report_root / "chapters"
        if not chapters_dir.is_dir():
            return
        for entry in sorted(chapters_dir.iterdir()):
            if entry.is_file() and entry.suffix == ".md":
                m = re.match(r"^(\d+)_", entry.name)
                if not m:
                    continue
                self.chapters_by_number[int(m.group(1))] = str(
                    entry.relative_to(self.report_root)
                )
        ch5_dir = chapters_dir / "05_country_and_site_profiles"
        if ch5_dir.is_dir():
            for entry in sorted(ch5_dir.glob("*.md")):
                title = _read_h1(entry)
                if title:
                    self.chapter5_files.append(
                        (_slug(title), str(entry.relative_to(self.report_root)))
                    )
            sites_dir = ch5_dir / "sites"
            if sites_dir.is_dir():
                for entry in sorted(sites_dir.glob("*.md")):
                    title = _read_h1(entry)
                    if title:
                        self.chapter5_site_files.append(
                            (_slug(title), str(entry.relative_to(self.report_root)))
                        )

    def _chapter_number(self, heading_path: list[str]) -> int | None:
        if not heading_path:
            return None
        m = CHAPTER_PREFIX_RE.match(heading_path[0])
        return int(m.group(1)) if m else None

    def _match(self, target: str, candidates: list[tuple[str, str]]) -> str | None:
        target_slug = _slug(target)
        if not target_slug:
            return None
        for slug, rel in candidates:
            if slug == target_slug:
                return rel
        for slug, rel in candidates:
            if target_slug in slug or slug in target_slug:
                return rel
        return None

    def resolve(self, heading_path: list[str]) -> str | None:
        """Return the most specific v1.03 report file the heading path lands in."""
        chapter_num = self._chapter_number(heading_path)
        if chapter_num is None:
            return None
        if chapter_num == 5 and len(heading_path) >= 3:
            site_hit = self._match(heading_path[2], self.chapter5_site_files)
            if site_hit:
                return site_hit
        if chapter_num == 5 and len(heading_path) >= 2:
            country_hit = self._match(heading_path[1], self.chapter5_files)
            if country_hit:
                return country_hit
        return self.chapters_by_number.get(chapter_num)


def detect_language(text: str) -> str:
    """Very small heuristic: tag a reviewer note as ``ro``, ``en``, or ``mixed``.

    Looks for Romanian-specific tokens (``este``, ``sa``, ``incercat``, etc.) and
    English determiners (``the``, ``is``, ``with``). Diacritics are normalised by
    matching the unaccented form because reviewer notes are usually typed without
    them. Returns ``""`` when the text is empty.
    """
    if not text:
        return ""
    normalized = text.lower()
    for src, dst in (("ă", "a"), ("â", "a"), ("î", "i"), ("ş", "s"), ("ș", "s"), ("ţ", "t"), ("ț", "t")):
        normalized = normalized.replace(src, dst)
    tokens = re.findall(r"[a-z]+", normalized)
    if not tokens:
        return ""
    ro_markers = {
        "este", "sa", "se", "sunt", "din", "trebuie", "obtinut", "incercat",
        "incheia", "recompletat", "pierdut", "verifica", "scor", "pondere",
        "categorie", "exclus", "sursa", "tabel", "titlu", "sugest", "migratory",
        "utilizeaza", "definitia", "filtrul", "nu", "ca", "si", "cu", "de",
        "la", "in", "pentru", "intr", "mai", "decat", "asa", "fara",
    }
    en_markers = {
        "the", "is", "are", "was", "were", "with", "and", "of", "for",
        "should", "would", "between", "this", "that", "these", "those",
        "make", "sure", "apply", "criteria", "however", "small", "large",
        "country", "site", "table", "text", "chapter", "limits", "do", "we",
    }
    ro_hits = sum(1 for t in tokens if t in ro_markers)
    en_hits = sum(1 for t in tokens if t in en_markers)
    if ro_hits == 0 and en_hits == 0:
        return ""
    if ro_hits >= 1 and en_hits >= 1 and min(ro_hits, en_hits) / max(ro_hits, en_hits) >= 0.34:
        return "mixed"
    return "ro" if ro_hits > en_hits else "en"
