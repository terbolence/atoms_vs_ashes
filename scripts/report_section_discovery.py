# man_hours: 1.0
"""Discover report Markdown sections in publication order."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

COUNTRY_ISO_ORDER: list[str] = [
    "AT", "BA", "BG", "CZ", "HR", "HU", "LV", "MD", "ME",
    "MK", "PL", "RO", "RS", "SK", "TR", "UA",
]


@dataclass
class Section:
    path: Path
    heading_shift: int = 0


def discover_chapter5_sections(chapters: Path) -> list[Section]:
    sections: list[Section] = []
    chapter5_root = chapters / "05_country_and_site_profiles"

    chapter5_main = chapters / "05_country_and_site_profiles.md"
    if chapter5_main.exists():
        sections.append(Section(chapter5_main))

    for iso in COUNTRY_ISO_ORDER:
        country_file = chapter5_root / f"{iso}_country_prototype.md"
        if country_file.exists():
            sections.append(Section(country_file, heading_shift=1))
            for site_file in sorted((chapter5_root / "sites").glob(f"{iso}_*.md")):
                sections.append(Section(site_file, heading_shift=2))

    for name in (
        "recommended_top5_sites.md",
        "consolidated_failure_section.md",
    ):
        path = chapter5_root / name
        if path.exists():
            sections.append(Section(path, heading_shift=1))

    return sections


def discover_sections(
    chapters: Path,
    annexes: Path,
) -> list[Section]:
    sections: list[Section] = []
    for name in (
        "00_acronyms.md",
        "01_introduction.md",
        "02_stage_1_site_survey.md",
        "03_stage_2_site_selection.md",
        "04_results_and_findings.md",
    ):
        path = chapters / name
        if path.exists():
            sections.append(Section(path))

    sections.extend(discover_chapter5_sections(chapters))

    for name in (
        "06_recommendations_for_detailed_site_evaluation.md",
        "07_final_remarks.md",
        "08_references.md",
    ):
        path = chapters / name
        if path.exists():
            sections.append(Section(path))

    for annex in sorted(annexes.glob("annex_*.md")):
        sections.append(Section(annex))

    return sections
