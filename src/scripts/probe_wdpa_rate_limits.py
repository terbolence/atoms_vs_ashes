"""Rate limit probe for WDPA Protected Planet API v4.

Usage: python scripts/probe_wdpa_rate_limits.py [--burst 20] [--delay 0.1]

Requires WDPA_TOKEN environment variable.
"""

from __future__ import annotations

import argparse
import os
import time

import httpx


def probe(burst: int = 20, delay: float = 0.1) -> None:
    token = os.environ.get("WDPA_TOKEN")
    if not token:
        print("ERROR: Set WDPA_TOKEN environment variable")
        return

    url = "https://api.protectedplanet.net/v4/protected_areas/search"
    params = {
        "token": token,
        "country": "ROU",
        "per_page": "5",
        "page": "1",
    }

    print(f"Probing WDPA API with {burst} requests, {delay}s delay…")
    print(f"URL: {url}")
    print()

    times: list[float] = []
    for i in range(burst):
        params["page"] = str(i + 1)
        t0 = time.monotonic()
        resp = httpx.get(url, params=params, timeout=15)
        elapsed = time.monotonic() - t0
        times.append(elapsed)

        rl = {
            k: v for k, v in resp.headers.items()
            if any(w in k.lower() for w in ("rate", "limit", "retry", "remaining"))
        }
        print(
            f"  [{i + 1}/{burst}] {resp.status_code} in {elapsed * 1000:.0f}ms"
            + (f"  RL: {rl}" if rl else "")
        )

        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After", "unknown")
            print(f"  *** RATE LIMITED at request {i + 1}. Retry-After: {retry_after}")
            break

        time.sleep(delay)

    if times:
        avg = sum(times) / len(times)
        print()
        print(f"Results: {len(times)} requests completed")
        print(f"  Avg response time: {avg * 1000:.0f}ms")
        print(f"  Min: {min(times) * 1000:.0f}ms, Max: {max(times) * 1000:.0f}ms")
        effective_rps = 1.0 / (avg + delay) if (avg + delay) > 0 else 0
        print(f"  Effective rate: {effective_rps:.1f} req/s")
        print(f"  Recommended inter_request_delay_s: {max(0.2, delay)}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Rate limit probe for WDPA API")
    p.add_argument("--burst", type=int, default=20)
    p.add_argument("--delay", type=float, default=0.1)
    a = p.parse_args()
    probe(a.burst, a.delay)
