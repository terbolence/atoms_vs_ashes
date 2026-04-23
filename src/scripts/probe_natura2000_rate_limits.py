"""Rate limit probe for EEA Natura 2000 WFS.

Usage: python scripts/probe_natura2000_rate_limits.py [--burst 20] [--delay 0.1]

Sends a configurable burst of WFS GetFeature requests to discover
throttling behaviour. The EEA WFS has no documented rate limit, but
this probe verifies the service's tolerance empirically.
"""

from __future__ import annotations

import argparse
import time

import httpx

WFS_URL = (
    "https://bio.discomap.eea.europa.eu/arcgis/services/"
    "ProtectedSites/Natura2000Sites/MapServer/WFSServer"
)

TEST_BBOX = "26.0,44.3,26.3,44.6,EPSG:4326"


def probe(burst: int = 20, delay: float = 0.1) -> None:
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": "Natura2000Sites:Natura2000polygon",
        "outputFormat": "GEOJSON",
        "srsName": "EPSG:4326",
        "bbox": TEST_BBOX,
        "count": "100",
    }

    print(f"Probing EEA Natura 2000 WFS: {burst} requests, {delay}s delay")
    print(f"URL: {WFS_URL}")
    print("-" * 70)

    times: list[float] = []
    statuses: list[int] = []

    with httpx.Client(timeout=30, follow_redirects=True) as client:
        for i in range(burst):
            t0 = time.monotonic()
            try:
                resp = client.get(WFS_URL, params=params)
                elapsed = time.monotonic() - t0
                times.append(elapsed)
                statuses.append(resp.status_code)

                rl_headers = {
                    k: v for k, v in resp.headers.items()
                    if any(w in k.lower() for w in ("rate", "limit", "retry", "remaining"))
                }

                status_str = f"{resp.status_code}"
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        fc = len(data.get("features", []))
                        status_str += f" ({fc} features)"
                    except Exception:
                        status_str += " (non-JSON)"

                print(
                    f"  [{i+1:3d}/{burst}] {status_str} in {elapsed*1000:.0f}ms"
                    + (f"  RL: {rl_headers}" if rl_headers else "")
                )

                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    print(f"  *** RATE LIMITED at request {i+1}.")
                    if retry_after:
                        print(f"  *** Retry-After: {retry_after}")
                    break

            except httpx.TimeoutException:
                elapsed = time.monotonic() - t0
                print(f"  [{i+1:3d}/{burst}] TIMEOUT after {elapsed*1000:.0f}ms")
                times.append(elapsed)
                statuses.append(0)
            except httpx.HTTPError as exc:
                elapsed = time.monotonic() - t0
                print(f"  [{i+1:3d}/{burst}] ERROR: {exc} ({elapsed*1000:.0f}ms)")
                times.append(elapsed)
                statuses.append(-1)

            time.sleep(delay)

    print("-" * 70)
    if times:
        ok_times = [t for t, s in zip(times, statuses) if s == 200]
        print(f"Requests sent: {len(times)}")
        print(f"  200 OK: {statuses.count(200)}")
        print(f"  429 Rate Limited: {statuses.count(429)}")
        print(f"  Other errors: {sum(1 for s in statuses if s not in (200, 429))}")
        if ok_times:
            avg = sum(ok_times) / len(ok_times)
            print(f"  Avg response time: {avg*1000:.0f}ms")
            print(f"  Min response time: {min(ok_times)*1000:.0f}ms")
            print(f"  Max response time: {max(ok_times)*1000:.0f}ms")

        if statuses.count(429) == 0:
            effective_rate = len(ok_times) / (sum(ok_times) + delay * len(ok_times))
            recommended = effective_rate * 0.5
            print(f"\n  No rate limiting detected.")
            print(f"  Effective throughput: ~{effective_rate:.1f} req/s")
            print(f"  Recommended inter_request_delay_s: {1/recommended:.1f}s (50% safety margin)")
            print(f"  Current config: 0.5s (courtesy delay)")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Rate limit probe for EEA Natura 2000 WFS")
    p.add_argument("--burst", type=int, default=20, help="Number of requests to send")
    p.add_argument("--delay", type=float, default=0.1, help="Delay between requests (seconds)")
    a = p.parse_args()
    probe(a.burst, a.delay)
