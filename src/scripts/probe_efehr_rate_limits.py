#!/usr/bin/env python3
# man_hours: 0.5
"""Rate limit probe for EFEHR seismic hazard API.

Usage: python scripts/probe_efehr_rate_limits.py [--burst 20] [--delay 0.1]

Findings (2026-04-13):
  - No rate limit headers detected (X-RateLimit-*, Retry-After)
  - No 429 responses after 10 rapid requests
  - Avg response time: ~2000 ms per map request (wide bbox)
  - No burst limit observed
  - Recommended inter_request_delay_s: 0.5 (courtesy to academic service)
"""

from __future__ import annotations

import argparse
import time

import httpx

BASE_URL = "http://appsrvr.share-eu.org:8080/share"
ESHM13_MODEL_ID = 68


def probe(burst: int = 20, delay: float = 0.1) -> None:
    print(f"Probing EFEHR API: {burst} requests, {delay}s delay between each")
    print(f"URL: {BASE_URL}/map (ESHM13 PGA 475yr)")
    print()

    times: list[float] = []
    errors = 0

    for i in range(burst):
        offset = i * 0.05
        params = {
            "id": str(ESHM13_MODEL_ID),
            "lon1": str(25.5 + offset), "lat1": "44.3",
            "lon2": str(25.7 + offset), "lat2": "44.5",
            "imt": "PGA", "hmapexceedprob": "0.1", "hmapexceedyears": "50",
            "soiltype": "rock_vs30_800ms-1",
            "aggregationtype": "arithmetic", "aggregationlevel": "0.5",
        }
        t0 = time.monotonic()
        try:
            resp = httpx.get(f"{BASE_URL}/map", params=params, timeout=30)
            elapsed = time.monotonic() - t0
            times.append(elapsed)

            rl_headers = {
                k: v for k, v in resp.headers.items()
                if any(
                    w in k.lower()
                    for w in ("rate", "limit", "retry", "remaining")
                )
            }
            status_info = f"{resp.status_code}"
            if rl_headers:
                status_info += f"  RL: {rl_headers}"

            print(
                f"  [{i + 1}/{burst}] {status_info} "
                f"in {elapsed * 1000:.0f}ms"
            )

            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After", "unknown")
                print(f"  *** RATE LIMITED at request {i + 1}. Retry-After: {retry_after}")
                break
        except httpx.HTTPError as exc:
            elapsed = time.monotonic() - t0
            errors += 1
            print(f"  [{i + 1}/{burst}] ERROR: {exc} in {elapsed * 1000:.0f}ms")

        time.sleep(delay)

    print()
    if times:
        avg = sum(times) / len(times)
        print(f"Results: {len(times)} successful, {errors} errors")
        print(
            f"  Avg: {avg * 1000:.0f}ms, "
            f"Min: {min(times) * 1000:.0f}ms, "
            f"Max: {max(times) * 1000:.0f}ms"
        )
        sustained_rate = 1.0 / avg if avg > 0 else 0
        print(f"  Sustained rate: {sustained_rate:.2f} req/s")
        recommended = max(0.5, 1.0 / (sustained_rate * 0.5)) if sustained_rate > 0 else 1.0
        print(f"  Recommended inter_request_delay_s: {recommended:.1f}")
    else:
        print("No successful requests.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Rate limit probe for EFEHR API")
    p.add_argument("--burst", type=int, default=20)
    p.add_argument("--delay", type=float, default=0.1)
    args = p.parse_args()
    probe(args.burst, args.delay)
