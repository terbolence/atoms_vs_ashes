"""Phase 4 — Generate run summary report."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ava_client import display
from ava_client.cache import SiteDataCache
from ava_client.snapshot import build_header, timestamp_utc, write_snapshot


def generate_summary(
    run_id: str,
    site_count: int,
    health_results: list[dict[str, Any]],
    fetch_stats: dict[str, dict[str, int]],
    analysis_stats: dict[str, int],
    elapsed_s: float,
    cache: SiteDataCache,
    output_dir: Path,
    write_snapshots: bool = True,
) -> dict[str, Any]:
    """Build the final summary, display it, and write snapshot files."""

    # Aggregate fetch stats across all workers
    total_fetch_ok = sum(s.get("ok", 0) for s in fetch_stats.values())
    total_fetch_fail = sum(s.get("fail", 0) for s in fetch_stats.values())

    total_analysis_ok = analysis_stats.get("ok", 0)
    total_analysis_fail = analysis_stats.get("fail", 0)
    total_analysis_skip = analysis_stats.get("skip", 0)

    health_pass = sum(1 for r in health_results if r["status"] == "PASS")
    health_fail = sum(1 for r in health_results if r["status"] == "FAIL")
    health_skip = sum(1 for r in health_results if r["status"] == "SKIP")

    snapshot_count = len(cache.all_snapshots)

    stats = {
        "Run ID": run_id,
        "Sites processed": site_count,
        "Health: PASS / FAIL / SKIP": f"{health_pass} / {health_fail} / {health_skip}",
        "Fetch: OK / FAIL": f"{total_fetch_ok} / {total_fetch_fail}",
        "Analysis: OK / FAIL / SKIP": f"{total_analysis_ok} / {total_analysis_fail} / {total_analysis_skip}",
        "Snapshots written": snapshot_count,
        "Total elapsed": f"{elapsed_s:.1f}s ({elapsed_s / 60:.1f} min)",
    }

    display.print_summary_table(stats)

    # Write all cached snapshots to disk
    if write_snapshots:
        for filename, content in cache.all_snapshots.items():
            write_snapshot(output_dir, filename, content)

    # Write unique run summary
    if write_snapshots:
        md = build_header("Run Summary", f"Automated run {run_id}",
                          run_id, site_count)
        md += f"**Completed:** {timestamp_utc()}\n\n"
        md += "| Metric | Value |\n|--------|-------|\n"
        for k, v in stats.items():
            md += f"| {k} | {v} |\n"
        md += "\n---\n\n## Snapshot Files\n\n"
        for fname in sorted(cache.all_snapshots):
            md += f"- `{fname}`\n"
        write_snapshot(output_dir, f"run_summary_{run_id}.md", md)

    return stats
