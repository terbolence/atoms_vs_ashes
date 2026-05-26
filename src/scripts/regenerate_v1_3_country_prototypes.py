"""Refresh the 16 in-region country prototypes against the frozen Phase 2 runs.

Loops the in-scope ISO-2 codes and invokes
``build_country_profile_prototype`` in ``--country-only`` mode. The
country bundle JSON / ledger CSV / Pareto figures / status map / country
Markdown all get rewritten. Per-site profiles are out of scope here
(handled by ``regenerate_v1_3_site_profiles.py``).

Belarus (BY) is deactivated from the published roster; the source data
is preserved in the DB for potential reactivation, but no build artefact
is regenerated for it.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts.build_country_profile_prototype import main as run_one

_DEFAULT_OUTPUT = Path(
    "report/version 1.03/output/report/chapters/05_country_and_site_profiles"
)

_DEFAULT_COUNTRIES = (
    "AT", "BA", "BG", "CZ", "HR", "HU", "LV", "MD", "ME",
    "MK", "PL", "RO", "RS", "SK", "TR", "UA",
)


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("regenerate_v1_3_country_prototypes")
    p.add_argument("--scoring-run-id", required=True)
    p.add_argument("--sensitivity-run-id", required=True)
    p.add_argument("--sensitivity-stamp", required=True)
    p.add_argument("--smr-key", default="nuscale_voygr6")
    p.add_argument("--output-dir", type=Path, default=_DEFAULT_OUTPUT)
    p.add_argument("--countries", nargs="+", default=list(_DEFAULT_COUNTRIES))
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    failures: list[str] = []
    for cc in args.countries:
        print(f"[country-prototype] {cc}")
        try:
            run_one([
                "--country-code", cc,
                "--country-only",
                "--smr-key", args.smr_key,
                "--scoring-run-id", args.scoring_run_id,
                "--sensitivity-run-id", args.sensitivity_run_id,
                "--sensitivity-stamp", args.sensitivity_stamp,
                "--output-dir", str(args.output_dir),
            ])
        except SystemExit as exc:
            if exc.code not in (0, None):
                failures.append(f"{cc}: SystemExit({exc.code})")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{cc}: {type(exc).__name__}: {exc}")
    if failures:
        print("FAILURES:", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1
    print(f"Refreshed {len(args.countries)} country prototypes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
