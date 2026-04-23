# man_hours: 0.5
"""Rate limit probe for S-18 EFSM20 seismogenic faults (WFS endpoint).

The primary data access is via bulk download (no rate limiting needed).
This script probes the WFS fallback endpoint used for per-site queries
and small bulk downloads.

Usage: python scripts/probe_efsm20_rate_limits.py [--burst 20] [--delay 0.1]
"""

from __future__ import annotations

import argparse
import time

import httpx


def probe(burst: int = 20, delay: float = 0.1) -> None:
    wfs_url = "https://seismofaults.eu/geoserver/wfs"

    # Small bbox around Vrancea, Romania — known seismic area
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeName": "EFSM20:crustal_fault_sources_top",
        "outputFormat": "application/json",
        "srsName": "EPSG:4326",
        "bbox": "26.0,45.0,27.0,46.0,EPSG:4326",
        "maxFeatures": "10",
    }

    print(f"Probing {wfs_url} with {burst} requests, {delay}s delay")
    print("-" * 60)

    times: list[float] = []
    for i in range(burst):
        t0 = time.monotonic()
        try:
            resp = httpx.get(wfs_url, params=params, timeout=15)
            elapsed = time.monotonic() - t0
            times.append(elapsed)

            rl = {
                k: v for k, v in resp.headers.items()
                if any(w in k.lower() for w in ("rate", "limit", "retry", "remaining"))
            }
            status_info = f"[{i+1}/{burst}] {resp.status_code} in {elapsed*1000:.0f}ms"
            if rl:
                status_info += f"  RL: {rl}"
            print(f"  {status_info}")

            if resp.status_code == 429:
                print(f"  *** RATE LIMITED at request {i+1}.")
                break
        except httpx.TimeoutException:
            elapsed = time.monotonic() - t0
            print(f"  [{i+1}/{burst}] TIMEOUT after {elapsed*1000:.0f}ms")
        except httpx.HTTPError as exc:
            elapsed = time.monotonic() - t0
            print(f"  [{i+1}/{burst}] ERROR: {exc} in {elapsed*1000:.0f}ms")

        time.sleep(delay)

    if times:
        avg = sum(times) / len(times)
        print("-" * 60)
        print(f"Results: {len(times)} successful requests")
        print(f"  Avg response time: {avg*1000:.0f}ms")
        print(f"  Min: {min(times)*1000:.0f}ms, Max: {max(times)*1000:.0f}ms")

        # EFSM20 is an academic service; recommend conservative courtesy delay
        if len(times) == burst:
            print(f"  No rate limiting detected in {burst} requests")
            print("  Recommended: 0.5s inter-request delay (courtesy for academic service)")
        else:
            sustained_rate = len(times) / sum(times) if sum(times) > 0 else 0
            safe_rate = sustained_rate * 0.5
            print(f"  Sustained rate: {sustained_rate:.1f} req/s")
            print(f"  Recommended safe rate: {safe_rate:.1f} req/s")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Rate limit probe for EFSM20 WFS")
    p.add_argument("--burst", type=int, default=20)
    p.add_argument("--delay", type=float, default=0.1)
    a = p.parse_args()
    probe(a.burst, a.delay)
