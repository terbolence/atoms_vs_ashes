# man_hours: 0.5
"""Dump catalogue, enrichment, and scoring state for one site (inspection)."""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.db.engine import init_engine, session_scope
from atoms_vs_ashes.db.models import CompositeRanking, RankingScore, ScreeningVerdict, Site
from atoms_vs_ashes.ingest.catalogue import (
    assess_site_scoring_readiness,
    enrichment_row_counts,
)


def _site_dict(site: Site) -> dict[str, Any]:
    return {
        "site_id": str(site.site_id),
        "name": site.name,
        "country_code": site.country_code,
        "plant_type": site.plant_type,
        "status": site.status,
        "latitude": float(site.latitude) if site.latitude is not None else None,
        "longitude": float(site.longitude) if site.longitude is not None else None,
        "installed_capacity_mw": (
            float(site.installed_capacity_mw)
            if site.installed_capacity_mw is not None
            else None
        ),
        "owner_operator": site.owner_operator,
        "site_area_ha": (
            float(site.site_area_ha) if site.site_area_ha is not None else None
        ),
        "wiki_url": site.wiki_url,
        "extended_data": site.extended_data,
    }


def build_inspection_report(site_id: uuid.UUID) -> dict[str, Any]:
    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "site_id": str(site_id),
    }
    audit_bundle = Path(
        "audit/post_processing/06_scoring/20260517_iernut_site_bundle.json"
    )
    if audit_bundle.exists():
        report["archived_enriched_bundle"] = str(audit_bundle.resolve())

    with session_scope() as session:
        site = session.get(Site, site_id)
        if site is None:
            report["error"] = "site not found in active database"
            return report
        report["site"] = _site_dict(site)
        report["enrichment_readiness"] = assess_site_scoring_readiness(
            session, site_id
        )
        report["enrichment_row_counts"] = enrichment_row_counts(session, site_id)

        composites = session.execute(
            select(CompositeRanking)
            .where(CompositeRanking.site_id == site_id)
            .order_by(CompositeRanking.ranked_at.desc().nulls_last())
        ).scalars().all()
        report["composite_rankings"] = [
            {
                "run_id": c.run_id,
                "smr_key": c.smr_key,
                "weight_profile": c.weight_profile,
                "composite_score": (
                    float(c.composite_score) if c.composite_score is not None else None
                ),
                "composite_score_low": (
                    float(c.composite_score_low)
                    if c.composite_score_low is not None
                    else None
                ),
                "composite_score_high": (
                    float(c.composite_score_high)
                    if c.composite_score_high is not None
                    else None
                ),
                "criteria_coverage": (
                    float(c.criteria_coverage)
                    if c.criteria_coverage is not None
                    else None
                ),
                "passed_exclusionary": c.passed_exclusionary,
                "passed_avoidance": c.passed_avoidance,
                "ranked_at": c.ranked_at.isoformat() if c.ranked_at else None,
            }
            for c in composites
        ]

        if composites:
            latest = composites[0]
            scores = session.execute(
                select(RankingScore)
                .where(
                    RankingScore.run_id == latest.run_id,
                    RankingScore.site_id == site_id,
                    RankingScore.smr_key == latest.smr_key,
                )
                .order_by(RankingScore.criterion_id)
            ).scalars().all()
            report["latest_scoring"] = {
                "run_id": latest.run_id,
                "smr_key": latest.smr_key,
                "ranking_scores": [
                    {
                        "criterion_id": s.criterion_id,
                        "score_0_10": float(s.score_0_10),
                        "quality_flag": s.quality_flag,
                        "confidence": s.confidence,
                        "justification": s.justification,
                    }
                    for s in scores
                ],
            }
            verdicts = session.execute(
                select(ScreeningVerdict)
                .where(
                    ScreeningVerdict.run_id == latest.run_id,
                    ScreeningVerdict.site_id == site_id,
                    ScreeningVerdict.smr_key == latest.smr_key,
                )
                .order_by(ScreeningVerdict.criterion_id)
            ).scalars().all()
            report["latest_scoring"]["screening_verdicts"] = [
                {
                    "criterion_id": v.criterion_id,
                    "phase": v.phase,
                    "verdict": v.verdict,
                    "justification": v.justification,
                }
                for v in verdicts
            ]

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-id", type=uuid.UUID, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        help="Write JSON report (default: stdout)",
    )
    args = parser.parse_args()
    init_engine(Settings())
    payload = build_inspection_report(args.site_id)
    text = json.dumps(payload, indent=2, default=str)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
