# man_hours: 1.5
"""One-shot patcher for SP-B EPRI weight wiring.

Reads ``config/epri/weights.yaml`` and rewrites every
``config/scoring_rubrics/*.yaml`` file to add a ``weight_factors:`` block and a
``weight_basis_source:`` block to each criterion. Idempotent: re-running on a
patched file rewrites the inserted lines in-place rather than appending dups.

The patcher operates as a text-level rewrite (regex anchored on
``criterion_id:`` and ``normalised_weight_pct:``) so the existing inline
flow-style YAML style is preserved end-to-end. The Pydantic loader in
``src/atoms_vs_ashes/scoring/rubric.py`` validates the resulting bundle on
import.

Run from the repo root::

    PYTHONPATH=src python src/scripts/_sp_b_epri_weight_patch.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
EPRI_SRC = REPO / "config" / "epri" / "weights.yaml"
RUBRIC_DIRS = (
    REPO / "config" / "scoring_rubrics",
    REPO / "config" / "scoring_specs",
)

BASELINE_CITATION = (
    "report/sites_evaluation/02_master_weights.md §3 master weight table "
    "(project engineering team intent)"
)

CRITERION_RE = re.compile(
    r"(\n  - criterion_id: (?P<cid>[A-Z]{2}-\d{2})\n)"
    r"(?P<body>(?:    .*\n)*?)"
    r"(    normalised_weight_pct: [^\n]*\n)",
)

WEIGHT_FACTOR_RE = re.compile(r"^    weight_factor: (\d+)$", re.MULTILINE)

EXISTING_BASIS_RE = re.compile(
    r"^    (weight_factors|weight_basis_source): \{[^\n]*\}\n",
    re.MULTILINE,
)


def load_epri_source() -> dict[str, dict]:
    with EPRI_SRC.open() as f:
        data = yaml.safe_load(f)
    weights = data.get("weights") or {}
    if not weights:
        raise SystemExit(f"No 'weights' map in {EPRI_SRC}")
    return weights


def patch_file(path: Path, epri: dict[str, dict]) -> int:
    text = path.read_text()
    patched_ids: list[str] = []

    def _strip_existing(body: str) -> str:
        return EXISTING_BASIS_RE.sub("", body)

    def _replace(match: re.Match) -> str:
        cid = match.group("cid")
        head = match.group(1)
        body = _strip_existing(match.group("body"))
        norm = match.group(4)
        wf_match = WEIGHT_FACTOR_RE.search(body)
        if not wf_match:
            raise SystemExit(
                f"Criterion {cid} in {path.name} has no weight_factor line; "
                "cannot derive baseline value for weight_factors block."
            )
        baseline_w = int(wf_match.group(1))
        record = epri.get(cid)
        if record is None:
            print(
                f"  - {cid}: NOT in {EPRI_SRC.name}; leaving criterion unchanged",
                file=sys.stderr,
            )
            return match.group(0)
        epri_w = int(record["weight_factor"])
        epri_basis = str(record.get("normative_basis", "")).strip()
        epri_citation = (
            f"docs/expert_siting_criteria_evaluation_matrix.md § {cid} "
            f"({epri_basis})"
        )
        insertion = (
            f"    weight_factors: {{baseline: {baseline_w}, epri: {epri_w}}}\n"
            f"    weight_basis_source: "
            f'{{baseline: "{BASELINE_CITATION}", '
            f'epri: "{epri_citation}"}}\n'
        )
        patched_ids.append(cid)
        return f"{head}{body}{norm}{insertion}"

    new_text = CRITERION_RE.sub(_replace, text)
    if new_text != text:
        path.write_text(new_text)
    print(f"{path.name}: patched {len(patched_ids)} criteria")
    return len(patched_ids)


def main() -> None:
    epri = load_epri_source()
    total = 0
    for rubric_dir in RUBRIC_DIRS:
        if not rubric_dir.is_dir():
            continue
        print(f"\n# {rubric_dir.relative_to(REPO)}")
        for path in sorted(rubric_dir.glob("*.yaml")):
            if path.name == "threshold_metadata.yaml":
                continue
            total += patch_file(path, epri)
    print(f"\nTotal criteria patched: {total} (EPRI source covers {len(epri)})")


if __name__ == "__main__":
    main()
