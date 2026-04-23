# man_hours: 0.5
"""Excel-safety + clear-naming helpers shared by the export sheets.

Split out of ``export_databases.py`` to keep the orchestrator under the
repo's 300-line file-size rule. Covers:

- ``sanitize_for_excel`` — strip tz, flatten JSONB, truncate long text.
- ``apply_clear_naming`` — swap raw DB column names for the descriptive
  labels from :mod:`_column_mappings`.

Used by both the basic DB sheets and the merged-DB-specific sheets.
"""

from __future__ import annotations

import json as _json

import pandas as pd

from export._column_mappings import COLUMN_MAPPINGS, phase_for_column

_EXCEL_MAX_CELL_LEN = 32_767


def sanitize_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    """Make a DataFrame Excel-safe.

    * Strip timezone from datetime columns (openpyxl rejects tz-aware).
    * Render dict / list cells (JSONB columns) as compact JSON strings.
    * Truncate any string cell that would exceed Excel's 32 767-char
      limit, marking the truncation so the user can spot it.
    """
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            try:
                out[col] = out[col].dt.tz_localize(None)
            except (TypeError, AttributeError):
                pass
            continue

        if out[col].dtype == object:
            def _scrub(v):
                if v is None:
                    return None
                if isinstance(v, (dict, list)):
                    s = _json.dumps(v, default=str, ensure_ascii=False)
                else:
                    s = v if isinstance(v, str) else str(v)
                if len(s) > _EXCEL_MAX_CELL_LEN:
                    return s[: _EXCEL_MAX_CELL_LEN - 20] + "…[TRUNCATED]"
                return s if isinstance(v, (dict, list)) else v

            out[col] = out[col].map(_scrub)
    return out


def apply_clear_naming(
    df: pd.DataFrame, sheet_name: str, use_clear_names: bool
) -> pd.DataFrame:
    """Apply the descriptive column-naming convention to ``df``.

    Only rewrites headers for the ``Sites`` sheet (the historical target
    of the clear-naming pass). Unmapped criterion columns get a
    ``<PHASE>_UNMAPPED_<orig>_<MEASURE>_text`` stub so downstream
    consumers can spot them without breaking the pipeline.
    """
    if not use_clear_names or sheet_name != "Sites":
        return df

    rename: dict[str, str] = {}
    for old_col in df.columns:
        if old_col in COLUMN_MAPPINGS:
            rename[old_col] = COLUMN_MAPPINGS[old_col][0]
        elif old_col.startswith(
            ("nh", "hi", "ri", "ep", "ns", "n2k", "wdpa")
        ) and old_col.endswith(("_quality", "_comment", "_source")):
            phase = phase_for_column(old_col)
            parts = old_col.rsplit("_", 1)
            measure = parts[-1].upper() if len(parts) == 2 else "VALUE"
            rename[old_col] = f"{phase}_UNMAPPED_{old_col}_{measure}_text"
    return df.rename(columns=rename)
