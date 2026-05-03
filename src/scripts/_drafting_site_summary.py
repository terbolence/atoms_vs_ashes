"""Compact site-bundle summariser used by the agent during the
specialist drafting pass for batches 2-5. Reads a site bundle JSON
and prints the values needed to draft the six site-scope
interpretations (4 family + stability + residual_risk).

Usage:
    PYTHONPATH=src python src/scripts/_drafting_site_summary.py \
        report/output/chapters/05_country_and_site_profiles/data/AT_timelkam_power_station_site_bundle.json
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path


def _fmt_value(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, float):
        if abs(value) >= 1000:
            return f"{value:,.0f}"
        if abs(value) >= 10:
            return f"{value:.2f}"
        return f"{value:.3f}".rstrip("0").rstrip(".")
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def main(path: str) -> None:
    bundle = json.loads(Path(path).read_text(encoding="utf-8"))
    site = bundle.get("site") or {}
    families = bundle.get("criterion_families") or {}
    scoring = bundle.get("scoring") or {}
    sensitivity = bundle.get("sensitivity") or {}
    screening = bundle.get("screening") or {}

    print("=" * 70)
    print(f"SITE: {site.get('name')} ({site.get('country_code')})")
    print(
        f"Coords: {site.get('latitude')}, {site.get('longitude')} | "
        f"capacity: {site.get('installed_capacity_mw')} MW | "
        f"subnational: {site.get('subnational_unit')}"
    )

    crs = scoring.get("composite_rankings") or []
    if crs:
        cr = crs[0]
        print(
            f"Composite: {cr.get('composite_score')} "
            f"(MC {cr.get('composite_score_low')} - {cr.get('composite_score_high')})"
        )

    cc = site.get("country_code")
    bands = sensitivity.get("bands") or []
    nat_band = next(
        (
            b
            for b in bands
            if b.get("scope_country_code") == cc
            and b.get("smr_key") in ("_all_", "nuscale_voygr6")
        ),
        None,
    )
    reg_band = next(
        (b for b in bands if b.get("scope_country_code") == "XX"),
        None,
    )
    if nat_band:
        print(
            f"National band {nat_band.get('band')} "
            f"(top10pct {nat_band.get('top10pct_hit_rate'):.0%}, "
            f"top5pct {nat_band.get('top5pct_hit_rate'):.0%}, "
            f"scenarios {nat_band.get('scenarios_scored')}/{nat_band.get('scenarios_total')})"
        )
    if reg_band:
        print(
            f"Regional band {reg_band.get('band')} "
            f"(top10pct {reg_band.get('top10pct_hit_rate'):.0%}, "
            f"scenarios {reg_band.get('scenarios_scored')}/{reg_band.get('scenarios_total')})"
        )

    rs = scoring.get("ranking_scores") or []
    by_id = {r.get("criterion_id"): r for r in rs}
    family_of = {
        "NH": "natural_hazards",
        "HI": "human_hazards",
        "EP": "radiological",
        "RI": "radiological",
        "NS": "infrastructure",
        "BF": "infrastructure",
    }

    family_buckets: dict[str, list[tuple[str, float, float]]] = defaultdict(list)
    for cid, r in by_id.items():
        fam = family_of.get(cid.split("-")[0])
        if fam is None:
            continue
        family_buckets[fam].append(
            (cid, r.get("score_0_10") or 0.0, r.get("weight_normalised") or 0.0)
        )

    weakest: list[tuple[str, float, float]] = []
    for r in rs:
        score = r.get("score_0_10")
        if score is not None and score < 4:
            weakest.append((r.get("criterion_id"), score, r.get("weight_normalised") or 0.0))
    weakest.sort(key=lambda t: t[1])

    print()
    print("Lowest-scoring criteria (score < 4):")
    for cid, sc, wt in weakest[:8]:
        print(f"  {cid}: {sc}/10  weight={wt}")

    contributors: list[tuple[str, float]] = []
    for r in rs:
        score = r.get("score_0_10")
        wt = r.get("weight_normalised")
        if score is None or wt is None:
            continue
        contributors.append((r.get("criterion_id"), score * wt))
    contributors.sort(key=lambda t: t[1], reverse=True)
    print()
    print("Top contributors to composite (score x weight):")
    for cid, contrib in contributors[:6]:
        sc = by_id[cid].get("score_0_10")
        wt = by_id[cid].get("weight_normalised")
        print(f"  {cid}: contrib={contrib:.4f} (score {sc}, weight {wt})")

    print()
    print("Family normalised scores (avg of normalised score x weight):")
    for fam, items in family_buckets.items():
        scored = [s for _, s, _ in items if s is not None]
        if scored:
            avg = sum(scored) / len(scored)
            print(f"  {fam}: avg score {avg:.2f} across {len(scored)} criteria")

    print()
    print("Avoidance flag (caution) and exclusionary-fail verdicts:")
    seen: set[str] = set()
    for v in screening.get("verdicts") or []:
        verdict = v.get("verdict")
        if verdict in ("caution", "avoidance_flag", "avoidance", "exclusionary_fail"):
            cid = v.get("criterion_id")
            key = f"{cid}|{verdict}"
            if key in seen:
                continue
            seen.add(key)
            mv = v.get("measured_value")
            mv_str = _fmt_value(mv) if mv is not None else "null"
            thr = v.get("threshold") or v.get("threshold_label") or ""
            print(f"  {cid}: {verdict}  measured={mv_str}  threshold={thr[:90]}")

    print()
    print("Inconclusive verdicts (rolled up):")
    inconclusive: dict[str, str] = {}
    for v in screening.get("verdicts") or []:
        if v.get("verdict") == "inconclusive":
            cid = v.get("criterion_id")
            mv = v.get("measured_value")
            inconclusive.setdefault(cid, _fmt_value(mv) if mv is not None else "null")
    for cid, mv in inconclusive.items():
        print(f"  {cid}: measured={mv}")

    print()
    print("Family bullet bullets (auto-extracted from markdown via separate file)")


if __name__ == "__main__":
    main(sys.argv[1])
