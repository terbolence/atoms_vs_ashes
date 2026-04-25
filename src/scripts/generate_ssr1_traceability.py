# man_hours: 1.5
"""SSR-1 ↔ project-criterion traceability matrix generator.

Reads ``config/ssr1_clause_map.yaml`` (the curated mapping) and the
rubric bundle, validates that every cited ``criterion_id`` exists, and
emits two artefacts that the regulatory-style audit pack expects:

- ``audit/post_processing/06_scoring/{stamp}_ssr1_traceability.csv``
  (one row per (Requirement, criterion) cell, plus rows for orphan
  criteria not yet mapped).
- ``report/methodology/ssr1_traceability.md`` — Markdown traceability
  table consumable by external reviewers.

Validation (raised as a ``ValueError`` if violated):

1. Every ``criterion_id`` in the map exists in the rubric bundle.
2. Every rubric criterion appears either in a Requirement's
   ``criterion_ids`` list **or** in ``non_ssr1_criteria``. Orphans are
   reported, not silently dropped.
3. Every Requirement declares a ``coverage`` value drawn from the
   schema's allowed set.
"""

from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from atoms_vs_ashes.logging import get_logger
from atoms_vs_ashes.scoring.rubric import load_rubric_bundle

log = get_logger(__name__)

DEFAULT_RUBRIC_DIR = Path("config/scoring_rubrics")
DEFAULT_MAP_PATH = Path("config/ssr1_clause_map.yaml")
DEFAULT_AUDIT_DIR = Path("audit/post_processing/06_scoring")
DEFAULT_REPORT_PATH = Path("report/methodology/ssr1_traceability.md")

ALLOWED_COVERAGE = {"full", "partial", "screening_only", "out_of_scope"}


def _load_map(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"SSR-1 map not found at {path}")
    return yaml.safe_load(path.read_text())


def _validate_map(
    data: dict[str, Any],
    bundle_ids: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    """Return (requirements, non_ssr1_rows, orphan_criteria).

    Raises ``ValueError`` on schema violations (unknown criterion_id,
    illegal coverage value).
    """
    requirements = data.get("requirements") or []
    non_ssr1 = data.get("non_ssr1_criteria") or []

    cited: set[str] = set()
    issues: list[str] = []
    for req in requirements:
        coverage = req.get("coverage")
        if coverage not in ALLOWED_COVERAGE:
            issues.append(
                f"{req.get('id', '?')}: invalid coverage '{coverage}' "
                f"(allowed: {sorted(ALLOWED_COVERAGE)})"
            )
        for cid in req.get("criterion_ids") or []:
            if cid not in bundle_ids:
                issues.append(
                    f"{req.get('id', '?')}: cites unknown criterion_id '{cid}'"
                )
            cited.add(cid)

    for entry in non_ssr1:
        cid = entry.get("criterion_id")
        if cid not in bundle_ids:
            issues.append(
                f"non_ssr1_criteria: unknown criterion_id '{cid}'"
            )
        if cid:
            cited.add(cid)

    if issues:
        raise ValueError("ssr1_map invalid:\n  - " + "\n  - ".join(issues))

    orphans = sorted(bundle_ids - cited)
    return requirements, non_ssr1, orphans


def _write_csv(
    csv_path: Path,
    requirements: list[dict[str, Any]],
    non_ssr1: list[dict[str, Any]],
    orphans: list[str],
    bundle: dict[str, Any],
) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "ssr1_requirement_id",
                "ssr1_title",
                "ssr1_section",
                "criterion_id",
                "criterion_name",
                "coverage",
                "notes",
            ]
        )
        for req in requirements:
            cids = req.get("criterion_ids") or []
            if not cids:
                writer.writerow(
                    [
                        req.get("id", ""),
                        req.get("title", ""),
                        req.get("section", ""),
                        "",
                        "",
                        req.get("coverage", ""),
                        (req.get("notes") or "").strip(),
                    ]
                )
                continue
            for cid in cids:
                crit = bundle.get(cid)
                writer.writerow(
                    [
                        req.get("id", ""),
                        req.get("title", ""),
                        req.get("section", ""),
                        cid,
                        crit.name if crit else "",
                        req.get("coverage", ""),
                        (req.get("notes") or "").strip(),
                    ]
                )
        for entry in non_ssr1:
            cid = entry.get("criterion_id", "")
            crit = bundle.get(cid)
            writer.writerow(
                [
                    "non_ssr1",
                    entry.get("label", ""),
                    "—",
                    cid,
                    crit.name if crit else "",
                    "out_of_scope",
                    (entry.get("rationale") or "").strip(),
                ]
            )
        for cid in orphans:
            crit = bundle.get(cid)
            writer.writerow(
                [
                    "ORPHAN",
                    "(unmapped)",
                    "—",
                    cid,
                    crit.name if crit else "",
                    "unmapped",
                    "Criterion not yet linked to an SSR-1 Requirement; review needed.",
                ]
            )


def _write_markdown(
    out_path: Path,
    *,
    reference: str,
    requirements: list[dict[str, Any]],
    non_ssr1: list[dict[str, Any]],
    orphans: list[str],
    bundle: dict[str, Any],
    csv_path: Path,
    stamp: str,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# SSR-1 ↔ project-criterion traceability matrix",
        "",
        f"- Stamp: `{stamp}`",
        f"- Reference: {reference}",
        f"- Source map: `{DEFAULT_MAP_PATH.as_posix()}`",
        f"- Source CSV: `{csv_path.as_posix()}`",
        "",
        "## How to read this matrix",
        "",
        "Each Requirement of IAEA SSR-1 (2019) is mapped to one or more",
        "Atoms-vs-Ashes scoring criteria. ``coverage`` indicates how much",
        "of the Requirement is satisfied at screening resolution:",
        "",
        "- **full** — the criterion(s) cover the substantive Requirement",
        "  obligations at pre-screening resolution.",
        "- **partial** — the screening proxies a portion of the",
        "  Requirement; detailed siting is needed to close it out.",
        "- **screening_only** — the basic-filter family captures the",
        "  upstream eligibility gate, not the Requirement itself.",
        "- **out_of_scope** — the Requirement is operational, programmatic",
        "  or QA-related and not addressed by a scoring criterion.",
        "",
        "## SSR-1 Requirements",
        "",
        "| SSR-1 Req. | Title | Coverage | Mapped criteria | Notes |",
        "| --- | --- | --- | --- | --- |",
    ]
    for req in requirements:
        cids = req.get("criterion_ids") or []
        crit_cell = ", ".join(
            f"{cid} ({bundle[cid].name})" if cid in bundle else cid
            for cid in cids
        ) or "—"
        notes = (req.get("notes") or "").strip().replace("\n", " ")
        lines.append(
            f"| {req.get('id', '')} | {req.get('title', '')} | "
            f"`{req.get('coverage', '')}` | {crit_cell} | {notes} |"
        )

    lines.extend(
        [
            "",
            "## Project-only criteria (not mapped to SSR-1)",
            "",
            "These viability axes (cost, transport, regulatory environment, …)",
            "are scored for ranking purposes but sit outside the SSR-1 safety",
            "remit. Listed here for completeness so reviewers see the full",
            "rubric.",
            "",
            "| Criterion | Rationale |",
            "| --- | --- |",
        ]
    )
    for entry in non_ssr1:
        cid = entry.get("criterion_id", "")
        label = entry.get("label", "")
        rationale = (entry.get("rationale") or "").strip().replace("\n", " ")
        crit_label = (
            f"{cid} — {label}"
            if label
            else (
                f"{cid} ({bundle[cid].name})"
                if cid in bundle
                else cid
            )
        )
        lines.append(f"| {crit_label} | {rationale} |")

    if orphans:
        lines.extend(
            [
                "",
                "## Orphan criteria (REVIEW)",
                "",
                "These criteria appear in the rubric but are not yet mapped to",
                "an SSR-1 Requirement or recorded as non-SSR-1. Review",
                "`config/ssr1_clause_map.yaml` and either map or classify each.",
                "",
            ]
        )
        for cid in orphans:
            crit = bundle.get(cid)
            name = crit.name if crit else ""
            lines.append(f"- `{cid}` — {name}")
    else:
        lines.extend(
            [
                "",
                "_All rubric criteria are accounted for (no orphans)._",
            ]
        )

    out_path.write_text("\n".join(lines).rstrip() + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rubric-dir", type=Path, default=DEFAULT_RUBRIC_DIR)
    parser.add_argument("--map-path", type=Path, default=DEFAULT_MAP_PATH)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument(
        "--stamp", default=datetime.now(UTC).strftime("%Y%m%d")
    )
    args = parser.parse_args(argv)

    bundle = load_rubric_bundle(args.rubric_dir)
    bundle_ids = set(bundle.keys())
    data = _load_map(args.map_path)

    requirements, non_ssr1, orphans = _validate_map(data, bundle_ids)
    csv_path = args.audit_dir / f"{args.stamp}_ssr1_traceability.csv"
    _write_csv(csv_path, requirements, non_ssr1, orphans, bundle)
    _write_markdown(
        args.report_path,
        reference=str(data.get("reference") or ""),
        requirements=requirements,
        non_ssr1=non_ssr1,
        orphans=orphans,
        bundle=bundle,
        csv_path=csv_path,
        stamp=args.stamp,
    )

    log.info(
        "ssr1_traceability_written",
        requirements=len(requirements),
        non_ssr1=len(non_ssr1),
        orphans=len(orphans),
        csv=str(csv_path),
        md=str(args.report_path),
    )
    print(f"Wrote {csv_path}")
    print(f"Wrote {args.report_path}")
    if orphans:
        print(f"WARNING: {len(orphans)} orphan criteria — review the map.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
