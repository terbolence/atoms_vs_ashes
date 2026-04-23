#!/usr/bin/env python3
"""FIX-03: Re-enrich CORINE/WorldCover sites to populate patch_count.

Usage:
    # Dry-run: show what would be enriched
    python scripts/run_fix03_patch_count.py --dry-run

    # Run 20-site validation batch (5 anchor + 15 random)
    python scripts/run_fix03_patch_count.py --batch-size 20

    # Run all sites
    python scripts/run_fix03_patch_count.py --all

    # WorldCover only (local, no API)
    python scripts/run_fix03_patch_count.py --worldcover-only --all

    # CORINE only (requires EEA REST API calls)
    python scripts/run_fix03_patch_count.py --corine-only --all
"""
from __future__ import annotations

import argparse
import random
import sys
import uuid
from datetime import datetime, timezone

sys.path.insert(0, "src")

from sqlalchemy import func

from atoms_vs_ashes.connectors.corine.models import CORINE_COVERED_COUNTRIES
from atoms_vs_ashes.db.engine import session_scope
from atoms_vs_ashes.db.models import Site, SiteInfrastructureV2


ANCHOR_SITE_NAMES = [
    "Kozienice",
    "Maritsa Iztok",
    "Turceni",
    "Tuzla",
    "Bitola",
]


def _sites_needing_patch_count(
    session,
    *,
    corine: bool = True,
    worldcover: bool = True,
) -> list[tuple[uuid.UUID, str, str]]:
    """Return (site_id, name, country_code) for sites missing patch_count."""
    rows = (
        session.query(Site.site_id, Site.name, Site.country_code)
        .join(SiteInfrastructureV2, Site.site_id == SiteInfrastructureV2.site_id)
        .filter(SiteInfrastructureV2.dominant_land_class.isnot(None))
        .filter(SiteInfrastructureV2.patch_count.is_(None))
        .order_by(Site.country_code, Site.name)
        .all()
    )
    result = []
    for sid, name, cc in rows:
        is_eu = (cc or "").upper() in CORINE_COVERED_COUNTRIES
        if is_eu and corine:
            result.append((sid, name, cc))
        elif not is_eu and worldcover:
            result.append((sid, name, cc))
    return result


def _pick_batch(
    sites: list[tuple[uuid.UUID, str, str]],
    batch_size: int,
) -> list[tuple[uuid.UUID, str, str]]:
    """Pick anchor sites first, then random fill."""
    anchors = [s for s in sites if s[1] in ANCHOR_SITE_NAMES]
    remaining = [s for s in sites if s[1] not in ANCHOR_SITE_NAMES]
    random.shuffle(remaining)
    fill = batch_size - len(anchors)
    return anchors + remaining[:max(0, fill)]


def _run_corine_batch(site_ids: list[uuid.UUID], run_id: str) -> int:
    """Re-enrich CORINE sites. Returns number of succeeded sites."""
    from atoms_vs_ashes.connectors.corine.batch import enrich_batch
    from atoms_vs_ashes.connectors.corine.client import CorineConnector

    connector = CorineConnector()
    with session_scope() as session:
        result = enrich_batch(
            connector,
            session,
            run_id,
            site_ids=site_ids,
            skip_if_enriched=False,
        )
    print(f"  CORINE: {result.succeeded} ok, {result.failed} failed, "
          f"{result.skipped_non_eu} non-EU skipped")
    return result.succeeded


def _run_worldcover_batch(site_ids: list[uuid.UUID], run_id: str) -> int:
    """Re-enrich WorldCover sites. Returns number of succeeded sites."""
    from atoms_vs_ashes.connectors.worldcover.batch import enrich_batch
    from atoms_vs_ashes.connectors.worldcover.client import WorldCoverConnector

    connector = WorldCoverConnector()
    with session_scope() as session:
        result = enrich_batch(
            connector,
            session,
            run_id,
            site_ids=site_ids,
            skip_if_enriched=False,
        )
    connector.close()
    print(f"  WorldCover: {result.succeeded} ok, {result.failed} failed, "
          f"{result.skipped_eu} EU skipped")
    return result.succeeded


def _validate(site_ids: list[uuid.UUID]) -> bool:
    """Check that patch_count is within plausible range (1-50)."""
    with session_scope() as session:
        rows = (
            session.query(
                Site.name,
                Site.country_code,
                SiteInfrastructureV2.patch_count,
                SiteInfrastructureV2.largest_contiguous_ha,
                SiteInfrastructureV2.buildable_area_ha,
            )
            .join(SiteInfrastructureV2, Site.site_id == SiteInfrastructureV2.site_id)
            .filter(Site.site_id.in_(site_ids))
            .all()
        )

    print(f"\n{'Site':<30} {'CC':<4} {'Patches':<8} {'Largest ha':<12} {'Buildable ha':<12}")
    print("-" * 70)

    issues = 0
    for name, cc, pc, lch, bah in rows:
        flag = ""
        if pc is None:
            flag = " *** NULL"
            issues += 1
        elif pc > 50:
            flag = " ** HIGH (review)"
        print(f"{name[:29]:<30} {cc:<4} {pc!s:<8} {lch!s:<12} {bah!s:<12}{flag}")

    print(f"\nValidation: {len(rows)} sites, {issues} issues")
    return issues == 0


def main() -> None:
    parser = argparse.ArgumentParser(description="FIX-03: populate patch_count")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--all", dest="run_all", action="store_true")
    parser.add_argument("--corine-only", action="store_true")
    parser.add_argument("--worldcover-only", action="store_true")
    args = parser.parse_args()

    corine = not args.worldcover_only
    worldcover = not args.corine_only

    with session_scope() as session:
        sites = _sites_needing_patch_count(
            session, corine=corine, worldcover=worldcover,
        )

    eu_count = sum(1 for _, _, cc in sites if (cc or "").upper() in CORINE_COVERED_COUNTRIES)
    non_eu_count = len(sites) - eu_count

    print(f"Sites needing patch_count: {len(sites)} "
          f"({eu_count} CORINE / {non_eu_count} WorldCover)")

    if args.dry_run:
        for sid, name, cc in sites[:20]:
            is_eu = (cc or "").upper() in CORINE_COVERED_COUNTRIES
            src = "CORINE" if is_eu else "WorldCover"
            print(f"  {name:<35} {cc:<4} → {src}")
        if len(sites) > 20:
            print(f"  ... and {len(sites) - 20} more")
        return

    if not sites:
        print("Nothing to do — all sites have patch_count.")
        return

    if args.run_all:
        batch = sites
    else:
        batch = _pick_batch(sites, args.batch_size)

    print(f"\nProcessing batch of {len(batch)} sites...")

    run_id = f"fix03_patch_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    corine_ids = [s[0] for s in batch if (s[2] or "").upper() in CORINE_COVERED_COUNTRIES]
    wc_ids = [s[0] for s in batch if (s[2] or "").upper() not in CORINE_COVERED_COUNTRIES]

    if corine_ids:
        print(f"\nRunning CORINE re-enrichment for {len(corine_ids)} EU sites...")
        _run_corine_batch(corine_ids, run_id)

    if wc_ids:
        print(f"\nRunning WorldCover re-enrichment for {len(wc_ids)} sites...")
        _run_worldcover_batch(wc_ids, run_id)

    all_ids = [s[0] for s in batch]
    ok = _validate(all_ids)

    if ok:
        print("\nAll sites passed validation.")
    else:
        print("\nSome sites have issues — review above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
