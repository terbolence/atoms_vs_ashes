#!/usr/bin/env python
# man_hours: 3.0
"""Parallel orchestrator: web-search site area enrichment across all countries.

Loads ALL remaining sites (cap 15 per country), then processes them with
a concurrent.futures thread pool (default 30 workers). Each worker runs one
Anthropic API call. DB writes are serialised via a threading lock.

Countries excluded: RO (already done), TR (user request).

Usage:
    # Dry run — show what would be processed:
    python scripts/run_site_area_all_countries.py --dry-run

    # Run with 30 parallel workers (default):
    python scripts/run_site_area_all_countries.py

    # Adjust concurrency:
    python scripts/run_site_area_all_countries.py --workers 10

    # Single country:
    python scripts/run_site_area_all_countries.py --country PL

Consent: User gave explicit go-ahead for all-region enrichment 2026-04-18.
"""

from __future__ import annotations

import argparse
import os
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

import anthropic
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from atoms_vs_ashes.config import Settings
from atoms_vs_ashes.logging import get_logger

log = get_logger(__name__)

# Re-use all the logic from the single-country script
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from enrich_site_area_web import (
    MODEL,
    MAX_TOKENS,
    PROMPT_VERSION,
    CRITERION_ID,
    COUNTRY_HINTS,
    search_site_area,
    persist_result,
    _llm_db_url,
    _ensure_data_source,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_PER_COUNTRY = 15
# Rate limit: 800k input tokens/min. Each call uses ~170k tokens.
# 4 concurrent = ~680k/min — stays under 800k with margin.
DEFAULT_WORKERS = 4

EXCLUDED_COUNTRIES = {"RO", "TR"}

MAX_RETRIES = 3
RETRY_BASE_DELAY_S = 65  # Wait >60s to reset the per-minute window

# ---------------------------------------------------------------------------
# Site loading (all countries, respecting cap)
# ---------------------------------------------------------------------------

def load_all_sites(
    session: Session,
    *,
    country_filter: str | None = None,
    countries_filter: list[str] | None = None,
    max_per_country: int = MAX_PER_COUNTRY,
) -> list[dict[str, Any]]:
    """Load unpopulated sites across all countries, capped at max_per_country each."""
    where = ["s.country_code IS NOT NULL"]
    params: dict[str, Any] = {}

    if countries_filter:
        where.append("s.country_code = ANY(:ccs)")
        params["ccs"] = countries_filter
    elif country_filter:
        where.append("s.country_code = :cc")
        params["cc"] = country_filter
    else:
        where.append("s.country_code NOT IN :excluded")
        params["excluded"] = tuple(EXCLUDED_COUNTRIES)

    where.append("s.site_area_ha IS NULL")  # skip already populated

    rows = session.execute(
        text(
            f"SELECT DISTINCT ON (s.name, s.country_code) "
            f"       s.site_id::text, s.name, s.country_name, s.country_code, "
            f"       s.latitude::float, s.longitude::float, "
            f"       s.installed_capacity_mw::float, s.plant_type, "
            f"       s.owner_operator, s.local_area, s.site_area_ha::float "
            f"FROM sites s "
            f"WHERE {' AND '.join(where)} "
            f"ORDER BY s.name, s.country_code, s.site_id"
        ),
        params,
    ).fetchall()

    sites = [dict(r._mapping) for r in rows]

    # Group by country, sort each group by capacity desc, take top N
    from collections import defaultdict
    by_country: dict[str, list[dict]] = defaultdict(list)
    for s in sites:
        by_country[s["country_code"]].append(s)

    result: list[dict[str, Any]] = []
    for cc in sorted(by_country):
        group = by_country[cc]
        group.sort(key=lambda s: (s.get("installed_capacity_mw") or 0), reverse=True)
        result.extend(group[:max_per_country])

    return result


# ---------------------------------------------------------------------------
# Worker function
# ---------------------------------------------------------------------------

db_lock = threading.Lock()
progress_lock = threading.Lock()
completed_count = 0
error_count = 0


def process_site(
    site: dict[str, Any],
    client: anthropic.Anthropic,
    session_factory: sessionmaker,
    run_id: str,
    total: int,
) -> dict[str, Any]:
    """Process one site with retry on rate-limit. Thread-safe. Returns summary dict."""
    global completed_count, error_count

    name = site["name"]
    cc = site["country_code"]

    for attempt in range(1, MAX_RETRIES + 1):
        t0 = time.monotonic()
        try:
            result = search_site_area(client, site)
            elapsed = time.monotonic() - t0

            area = result.get("site_area_ha")
            buildable = result.get("buildable_area_ha") or area
            expansion = result.get("expansion_potential_ha", 0) or 0
            confidence = result.get("confidence", "?")
            plant_status = result.get("plant_status", "?")

            with db_lock:
                with session_factory() as session:
                    persist_result(
                        session,
                        site_id=site["site_id"],
                        site_name=name,
                        result=result,
                        run_id=run_id,
                    )
                    session.commit()

            with progress_lock:
                completed_count += 1
                n = completed_count + error_count
                print(
                    f"  [{n}/{total}] OK  {cc}  {name:<40}  "
                    f"area={area:.0f}ha  build={buildable:.0f}ha  "
                    f"conf={confidence}  status={plant_status}  "
                    f"({elapsed:.0f}s)"
                )

            return {
                "name": name, "country": cc,
                "site_area_ha": area, "buildable_area_ha": buildable,
                "expansion_potential_ha": expansion, "confidence": confidence,
                "plant_status": plant_status, "status": "ok",
            }

        except anthropic.RateLimitError:
            delay = RETRY_BASE_DELAY_S * attempt
            with progress_lock:
                print(f"  [RATE-LIMIT] {cc}  {name:<40}  retry {attempt}/{MAX_RETRIES} in {delay}s")
            time.sleep(delay)
            continue

        except Exception as exc:
            elapsed = time.monotonic() - t0
            with progress_lock:
                error_count += 1
                n = completed_count + error_count
                print(f"  [{n}/{total}] ERR {cc}  {name:<40}  {str(exc)[:60]}  ({elapsed:.0f}s)")
            log.error("site_failed", site_name=name, error=str(exc))
            return {"name": name, "country": cc, "status": "error", "error": str(exc)}

    # Exhausted retries
    with progress_lock:
        error_count += 1
        n = completed_count + error_count
        print(f"  [{n}/{total}] ERR {cc}  {name:<40}  rate-limited after {MAX_RETRIES} retries")
    return {"name": name, "country": cc, "status": "error", "error": "rate_limit_exhausted"}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    global completed_count, error_count

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Show plan only")
    parser.add_argument("--country", default=None, help="Restrict to one country (2-letter code)")
    parser.add_argument(
        "--countries", default=None,
        help="Comma-separated list of country codes (e.g. RS,SK,XK,SI)",
    )
    parser.add_argument(
        "--workers", type=int, default=DEFAULT_WORKERS,
        help=f"Max concurrent API calls (default: {DEFAULT_WORKERS})",
    )
    parser.add_argument(
        "--max-per-country", type=int, default=MAX_PER_COUNTRY,
        help=f"Max sites per country (default: {MAX_PER_COUNTRY})",
    )
    args = parser.parse_args()

    countries_list = [c.strip().upper() for c in args.countries.split(",")] if args.countries else None

    settings = Settings()
    llm_url = _llm_db_url(settings)
    engine = create_engine(llm_url, echo=False, pool_pre_ping=True, pool_size=5)
    SessionFactory = sessionmaker(bind=engine)

    with SessionFactory() as session:
        sites = load_all_sites(
            session,
            country_filter=args.country,
            countries_filter=countries_list,
            max_per_country=args.max_per_country,
        )

    if not sites:
        print("No unpopulated sites found. All done or filters too narrow.")
        return

    # Group summary
    from collections import Counter
    cc_counts = Counter(s["country_code"] for s in sites)

    print(f"\n{'='*80}")
    print(f"  Site Area Web Enrichment — PARALLEL ({args.workers} workers)")
    print(f"  Model: {MODEL} + web_search  |  Prompt: {PROMPT_VERSION}")
    print(f"  Cap: {args.max_per_country} per country  |  Total: {len(sites)} sites")
    print(f"  DB: {llm_url.split('@')[-1]}")
    print(f"{'='*80}")

    print(f"\n  Sites per country:")
    for cc in sorted(cc_counts):
        print(f"    {cc}: {cc_counts[cc]}")

    print(f"\n  Full site list:")
    print(f"  {'#':>4}  {'CC':>2}  {'Site':<45}  {'MW':>7}")
    print(f"  {'-'*65}")
    for i, s in enumerate(sites, 1):
        mw = f"{s['installed_capacity_mw']:.0f}" if s.get("installed_capacity_mw") else "?"
        print(f"  {i:>4}  {s['country_code']:>2}  {s['name']:<45}  {mw:>7}")

    avg_input = 173_235
    avg_output = 1_420
    cost_est = len(sites) * (avg_input / 1e6 * 3.0 + avg_output / 1e6 * 15.0 + 4 * 10 / 1000)
    print(f"\n  Estimated cost: ~${cost_est:.2f} USD")
    print(f"  Dry run: {'YES' if args.dry_run else 'NO — live API calls'}")

    if args.dry_run:
        print("\nDRY RUN complete.")
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    run_id = f"site_area_web_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    print(f"\n  Run ID: {run_id}")
    print(f"  Starting at {datetime.now(timezone.utc).isoformat()}Z")
    print(f"  Workers: {args.workers}\n")

    with SessionFactory() as session:
        _ensure_data_source(session)
        session.commit()

    client = anthropic.Anthropic(api_key=api_key)

    completed_count = 0
    error_count = 0
    results: list[dict[str, Any]] = []
    t_start = time.monotonic()

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(process_site, site, client, SessionFactory, run_id, len(sites)): site
            for site in sites
        }
        for future in as_completed(futures):
            results.append(future.result())

    elapsed_total = time.monotonic() - t_start

    # Sort results by country + name for display
    results.sort(key=lambda r: (r["country"], r["name"]))

    ok = [r for r in results if r["status"] == "ok"]
    errors = [r for r in results if r["status"] != "ok"]

    print(f"\n{'='*90}")
    print(f"  Run complete: {run_id}")
    print(f"  {len(ok)} OK, {len(errors)} errors  |  {elapsed_total:.0f}s total")
    print(f"{'='*90}")
    print(f"  {'#':>3}  {'CC':>2}  {'Site':<40}  {'Area':>6}  {'Build':>6}  {'Exp':>6}  {'Conf':>6}  {'Status':<12}")
    print(f"  {'-'*88}")
    for i, r in enumerate(results, 1):
        if r["status"] == "ok":
            print(
                f"  {i:>3}  {r['country']:>2}  {r['name']:<40}  "
                f"{r['site_area_ha']:>6.0f}  {r['buildable_area_ha']:>6.0f}  "
                f"{r['expansion_potential_ha']:>6.0f}  {r['confidence']:>6}  "
                f"{r.get('plant_status','?'):<12}"
            )
        else:
            print(f"  {i:>3}  {r['country']:>2}  {r['name']:<40}  {'ERR':>6}  {'':>6}  {'':>6}  {'':>6}  {r.get('error','')[:30]}")

    if errors:
        print(f"\n  Failed sites ({len(errors)}):")
        for r in errors:
            print(f"    {r['country']}  {r['name']}: {r.get('error','unknown')}")

    print(f"\n{'='*90}\n")


if __name__ == "__main__":
    main()
