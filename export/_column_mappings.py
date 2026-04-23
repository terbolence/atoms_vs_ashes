# man_hours: 0.5
"""Clear-naming catalog for the comprehensive Excel export.

The mapping was previously an inline ~345-line dict in
``export_databases.py``. That crossed the repo's 300-line per-file rule
(see ``.cursor/rules/file-size-python.mdc``) and made the builder code
hard to navigate. The data now lives in ``column_mappings.csv`` and is
loaded once on import.

Canonical column-naming rules:

    <PHASE>_<CATEGORY>_<NUMBER>_<Description>_<MEASURE_TYPE>_<UNIT>
    PHASE        = EXCL | AVOID | RANK
    MEASURE_TYPE = VALUE | QUALITY | COMMENT | SOURCE

See ``audit/post_processing/02_data_verification/20260418_column_readability.md``
for the audit trail driving the mapping.
"""

from __future__ import annotations

import csv
from pathlib import Path

_CSV_PATH = Path(__file__).with_name("column_mappings.csv")


def _load_column_mappings() -> dict[str, tuple[str, str]]:
    """Read the CSV ledger into the legacy ``COLUMN_MAPPINGS`` shape."""
    mappings: dict[str, tuple[str, str]] = {}
    with _CSV_PATH.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            original = (row.get("original_column") or "").strip()
            if not original:
                continue
            mappings[original] = (
                (row.get("clear_name") or "").strip(),
                (row.get("description") or "").strip(),
            )
    return mappings


COLUMN_MAPPINGS: dict[str, tuple[str, str]] = _load_column_mappings()


_CRITERION_PHASE: dict[str, str] = {
    "nh01": "EXCL", "nh02": "EXCL", "nh03": "EXCL", "nh04": "EXCL",
    "nh05": "EXCL", "nh05b": "EXCL", "nh06": "RANK", "nh07": "EXCL",
    "nh08": "AVOID", "nh09": "AVOID",
    "nh10": "RANK", "nh11": "RANK", "nh12": "RANK", "nh13": "RANK",
    "nh14": "RANK",
    "hi01": "AVOID", "hi02": "AVOID", "hi03": "AVOID", "hi04": "AVOID",
    "hi05": "RANK", "hi06": "AVOID", "hi07": "RANK", "hi08": "RANK",
    "ri01": "RANK", "ri02": "RANK", "ri03": "RANK",
    "ri04": "AVOID", "ri05": "RANK", "ri06": "RANK",
    "ep01": "AVOID", "ep02": "RANK", "ep03": "RANK", "ep04": "RANK",
    "ep05": "RANK",
    "ns01": "RANK", "ns02": "AVOID", "ns03": "AVOID", "ns04": "RANK",
    "ns05": "AVOID", "ns06": "RANK", "ns07": "RANK", "ns08": "AVOID",
    "ns09": "RANK", "ns10": "RANK", "ns11": "RANK", "ns12": "RANK",
    "ns13": "RANK",
}


def phase_for_column(col_name: str) -> str:
    """Resolve the correct ``PHASE`` prefix for a criterion column name."""
    import re

    m = re.match(r"^(nh\d+b?|hi\d+|ri\d+|ep\d+|ns\d+)", col_name)
    if m:
        return _CRITERION_PHASE.get(m.group(1), "RANK")
    if col_name.startswith("wdpa"):
        return "AVOID"
    if col_name.startswith("n2k"):
        return "AVOID"
    return "RANK"
