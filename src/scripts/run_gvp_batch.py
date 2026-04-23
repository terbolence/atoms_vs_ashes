"""Ad-hoc runner for S-07 Smithsonian GVP batch enrichment.

Usage:
    PYTHONPATH=src python -u scripts/run_gvp_batch.py --run-id <id> --country TR
    PYTHONPATH=src python -u scripts/run_gvp_batch.py --run-id <id> --all
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--country", action="append", default=[])
    parser.add_argument("--all", dest="all_sites", action="store_true")
    args = parser.parse_args()

    print(f"[boot] importing modules...", flush=True)
    from atoms_vs_ashes.config import Settings
    from atoms_vs_ashes.db.engine import init_engine, session_scope
    from atoms_vs_ashes.connectors.smithsonian_gvp import SmithsonianGvpConnector
    from atoms_vs_ashes.connectors.smithsonian_gvp.batch import enrich_batch

    print(f"[boot] building settings...", flush=True)
    settings = Settings()
    init_engine(settings)

    label = "ALL" if args.all_sites else ",".join(args.country)
    print(f"[boot] run_id={args.run_id} scope={label}", flush=True)

    with SmithsonianGvpConnector(settings) as connector:
        with session_scope() as session:
            if args.all_sites:
                batch = enrich_batch(connector, session, args.run_id)
            else:
                batch = enrich_batch(
                    connector, session, args.run_id, country_codes=args.country
                )

    print()
    print(batch.summary_line(), flush=True)
    print()

    hazard_counts = Counter(s.hazard_class for s in batch.per_site)
    print("Hazard class distribution:", flush=True)
    for hc, n in sorted(hazard_counts.items(), key=lambda x: -x[1]):
        print(f"  {hc:12}: {n}", flush=True)

    print()
    print("Exclusionary sites (within exclusion distance):", flush=True)
    any_excl = False
    for s in batch.per_site:
        if s.hazard_class == "exclusionary":
            any_excl = True
            print(
                f"  {s.site_name[:40]:40} | {s.nearest_volcano_km:.1f}km | {s.nearest_volcano_name}",
                flush=True,
            )
    if not any_excl:
        print("  (none)", flush=True)

    print()
    print("Avoidance-class sites:", flush=True)
    any_avoid = False
    for s in batch.per_site:
        if s.hazard_class == "avoidance":
            any_avoid = True
            print(
                f"  {s.site_name[:40]:40} | {s.nearest_volcano_km:.1f}km | {s.nearest_volcano_name}",
                flush=True,
            )
    if not any_avoid:
        print("  (none)", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
