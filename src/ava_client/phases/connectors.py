"""Phase 2 — CORINE, EGDI, and Seismic worker functions.

Each function is submitted to a thread pool so different APIs are
queried in parallel while respecting per-API rate limits.

The Overpass (OSM + Population) worker lives in ``fetch_overpass.py``
because it is the largest single API group.
"""

from __future__ import annotations

import time
import traceback
from typing import Any

from ava_client import display
from ava_client.cache import SiteDataCache
from ava_client.rate_limiter import ApiRateLimiter
from ava_client.resolver import ResolvedSite
from ava_client.snapshot import build_header, build_site_section, pretty_json


# Re-export so runner.py can import all workers from one place
from ava_client.phases.fetch_overpass import run_overpass_worker  # noqa: F401


def run_corine_worker(
    sites: list[ResolvedSite],
    settings: Any,
    cache: SiteDataCache,
    limiter: ApiRateLimiter,
    run_id: str,
) -> dict[str, int]:
    """Fetch CORINE features and classify per site."""
    from atoms_vs_ashes.connectors.corine import CorineConnector

    stats = {"ok": 0, "fail": 0}
    conn = CorineConnector(settings)

    try:
        md = build_header("CORINE Land Cover - classify()",
                          "Fetch CLC features + ring classification",
                          run_id, len(sites))
        for site in sites:
            limiter.wait()
            t0 = time.monotonic()
            try:
                features = conn.fetch(site.lat, site.lon, radius_m=5000)
                result = conn.classify(site.lat, site.lon) if features else None
                ms = int((time.monotonic() - t0) * 1000)
                cache.put(site, "corine_features", features)
                cache.put(site, "corine_classify", result)

                summary = f"{len(features)} features"
                if result:
                    summary += f", {len(result.rings)} rings, dev={result.total_developable_ha:.1f}ha"
                md += build_site_section(
                    site, "ok" if features else "error", ms, summary,
                    pretty_json(result.to_dict() if result else {"features_count": 0}),
                )
                stats["ok"] += 1
                display.print_status(
                    f"[dim]corine[/dim]   {site.country} {site.name} "
                    f"[green]OK[/green] ({ms}ms, {summary})")
            except Exception as exc:
                ms = int((time.monotonic() - t0) * 1000)
                md += build_site_section(site, "error", ms, str(exc),
                                         traceback.format_exc())
                stats["fail"] += 1
                display.print_status(
                    f"[dim]corine[/dim]   {site.country} {site.name} "
                    f"[red]FAIL[/red] ({ms}ms: {exc})")

        cache.put_snapshot("corine_classify.md", md)
    finally:
        conn.close()

    return stats


def run_egdi_worker(
    sites: list[ResolvedSite],
    settings: Any,
    cache: SiteDataCache,
    limiter: ApiRateLimiter,
    run_id: str,
) -> dict[str, int]:
    """Fetch EGDI geology data per site."""
    from atoms_vs_ashes.connectors.egdi_geology import EgdiGeologyConnector

    stats = {"ok": 0, "fail": 0}
    conn = EgdiGeologyConnector(settings)

    try:
        md = build_header("EGDI Geology - fetch_all()",
                          "Full geological assessment", run_id, len(sites))
        for site in sites:
            limiter.wait()
            t0 = time.monotonic()
            try:
                result = conn.fetch_all(site.lat, site.lon, country_code=site.country)
                ms = int((time.monotonic() - t0) * 1000)
                cache.put(site, "egdi", result)
                summary = (f"quality={result.quality}, "
                           f"layers_with_data={len(result.layers_with_data)}/{len(result.layers_queried)}")
                md += build_site_section(site, "ok", ms, summary,
                                         pretty_json(result.to_dict()))
                stats["ok"] += 1
                display.print_status(
                    f"[dim]egdi[/dim]     {site.country} {site.name} "
                    f"[green]OK[/green] ({ms}ms, {summary})")
            except Exception as exc:
                ms = int((time.monotonic() - t0) * 1000)
                md += build_site_section(site, "error", ms, str(exc),
                                         traceback.format_exc())
                stats["fail"] += 1
                display.print_status(
                    f"[dim]egdi[/dim]     {site.country} {site.name} "
                    f"[red]FAIL[/red] ({ms}ms: {exc})")

        cache.put_snapshot("egdi_geology.md", md)
    finally:
        conn.close()

    return stats


def run_seismic_worker(
    sites: list[ResolvedSite],
    settings: Any,
    cache: SiteDataCache,
    limiter: ApiRateLimiter,
    run_id: str,
) -> dict[str, int]:
    """Fetch seismic hazard data per site."""
    from atoms_vs_ashes.connectors.seismic_hazard import SeismicHazardConnector

    stats = {"ok": 0, "fail": 0}
    conn = SeismicHazardConnector(settings)

    try:
        md = build_header("Seismic Hazard - fetch_all()",
                          "PGA, hazard curve, and UHS via EFEHR/GEM fallback",
                          run_id, len(sites))
        for site in sites:
            limiter.wait()
            t0 = time.monotonic()
            try:
                result = conn.fetch_all(site.lat, site.lon)
                ms = int((time.monotonic() - t0) * 1000)
                cache.put(site, "seismic", result)
                summary = (f"PGA_475yr={result.pga_475yr}, "
                           f"PGA_2475yr={result.pga_2475yr}, "
                           f"source={result.source}, quality={result.quality}")
                status = "ok" if result.quality != "insufficient" else "error"
                md += build_site_section(site, status, ms, summary,
                                         pretty_json(result.to_dict()))
                stats["ok"] += 1
                display.print_status(
                    f"[dim]seismic[/dim]  {site.country} {site.name} "
                    f"[green]OK[/green] ({ms}ms, {summary})")
            except Exception as exc:
                ms = int((time.monotonic() - t0) * 1000)
                md += build_site_section(site, "error", ms, str(exc),
                                         traceback.format_exc())
                stats["fail"] += 1
                display.print_status(
                    f"[dim]seismic[/dim]  {site.country} {site.name} "
                    f"[red]FAIL[/red] ({ms}ms: {exc})")

        cache.put_snapshot("seismic_hazard.md", md)
    finally:
        conn.close()

    return stats
