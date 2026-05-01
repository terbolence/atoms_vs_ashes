#!/usr/bin/env python
# man_hours: 1.0
"""Resolve site area in ``atoms_vs_ashes_merged`` from LLM, API, and favourable area."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from atoms_vs_ashes.analysis.site_area_merge_db import run


def main() -> int:
    default_run_id = f"site_area_resolve_{datetime.now(timezone.utc):%Y%m%dT%H%M%S}"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--run-id", default=default_run_id)
    args = parser.parse_args()
    run(run_id=args.run_id, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
