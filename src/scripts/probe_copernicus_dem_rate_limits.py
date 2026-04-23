#!/usr/bin/env python3
# man_hours: 0.5
"""Rate limit probe for Copernicus DEM GLO-30 COG tiles on AWS Open Data.

The S3 bucket is public and served via CloudFront CDN. There are no
documented rate limits, but this script probes empirically to discover
any throttling behaviour.

Usage: python scripts/probe_copernicus_dem_rate_limits.py [--burst 20] [--delay 0.05]
"""

from __future__ import annotations

import argparse
import time

import httpx

TILE_URL = (
    "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/"
    "Copernicus_DSM_COG_10_N45_00_E027_00_DEM/"
    "Copernicus_DSM_COG_10_N45_00_E027_00_DEM.tif"
)


def probe(burst: int = 20, delay: float = 0.05) -> None:
    """Send burst HEAD requests to discover rate limiting."""
    print(f"Probing Copernicus DEM COG endpoint ({burst} requests, {delay}s delay)")
    print(f"URL: {TILE_URL}")
    print("-" * 70)

    times: list[float] = []
    statuses: list[int] = []

    for i in range(burst):
        t0 = time.monotonic()
        try:
            resp = httpx.head(TILE_URL, timeout=15, follow_redirects=True)
            elapsed = time.monotonic() - t0
            times.append(elapsed)
            statuses.append(resp.status_code)

            rl = {
                k: v for k, v in resp.headers.items()
                if any(w in k.lower() for w in ("rate", "limit", "retry", "remaining"))
            }
            print(
                f"  [{i + 1}/{burst}] {resp.status_code} in {elapsed * 1000:.0f}ms"
                + (f"  RL: {rl}" if rl else "")
            )

            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                print(f"  *** RATE LIMITED at request {i + 1}.")
                if retry_after:
                    print(f"  *** Retry-After: {retry_after}")
                break

        except httpx.TimeoutException:
            elapsed = time.monotonic() - t0
            print(f"  [{i + 1}/{burst}] TIMEOUT after {elapsed * 1000:.0f}ms")
            times.append(elapsed)
            statuses.append(0)

        except httpx.HTTPError as exc:
            elapsed = time.monotonic() - t0
            print(f"  [{i + 1}/{burst}] ERROR: {exc} ({elapsed * 1000:.0f}ms)")
            times.append(elapsed)
            statuses.append(0)

        time.sleep(delay)

    print("-" * 70)
    if times:
        avg_ms = sum(times) / len(times) * 1000
        ok_count = sum(1 for s in statuses if 200 <= s < 300)
        print(f"Results: {ok_count}/{len(statuses)} OK")
        print(f"Average response time: {avg_ms:.0f}ms")
        print(f"Min: {min(times) * 1000:.0f}ms, Max: {max(times) * 1000:.0f}ms")

        rate_limited = any(s == 429 for s in statuses)
        if rate_limited:
            idx = statuses.index(429)
            print(f"Rate limited at request {idx + 1}")
            print(f"Recommended: {max(1, idx // 2)} requests before pause")
        else:
            print("No rate limiting detected.")
            print("Recommendation: use courtesy delay of 0.1–0.5s between requests")
    else:
        print("No successful requests.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Probe Copernicus DEM rate limits")
    p.add_argument("--burst", type=int, default=20, help="Number of requests")
    p.add_argument("--delay", type=float, default=0.05, help="Delay between requests (s)")
    a = p.parse_args()
    probe(a.burst, a.delay)
