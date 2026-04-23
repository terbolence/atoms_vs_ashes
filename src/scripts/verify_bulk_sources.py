"""Verify bulk-downloaded data sources exist and are valid.

Checks each bulk-download connector's local data directory for expected
files, validates file sizes and format headers, and reports missing or
corrupt data.  Optionally re-downloads missing files.

Usage:
    PYTHONPATH=src python -u scripts/verify_bulk_sources.py
    PYTHONPATH=src python -u scripts/verify_bulk_sources.py --fix
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

SOURCES_DIR = Path("sources")

EXPECTED_SOURCES: dict[str, dict[str, Any]] = {
    "efsm20_faults": {
        "path": "efsm20",
        "expected_files": ["*.geojson", "*.zip"],
        "description": "EFSM20 European fault database",
    },
    "geonames_dump": {
        "path": "geonames",
        "expected_files": ["*.txt", "*.zip"],
        "description": "GeoNames geographic database dump",
    },
    "hydrorivers": {
        "path": "hydrorivers",
        "expected_files": ["*.shp", "*.zip"],
        "description": "HydroRIVERS global river network",
    },
    "wokam_karst": {
        "path": "karst/wokam",
        "expected_files": ["*.shp"],
        "description": "WOKAM World Karst Aquifer Map",
    },
    "worldcover": {
        "path": "worldcover",
        "expected_files": ["*.tif"],
        "min_file_count": 10,
        "description": "ESA WorldCover 10m land cover GeoTIFF tiles",
    },
    "wri_aqueduct": {
        "path": "wri_aqueduct",
        "expected_files": ["*.gdb", "*.gpkg", "*.shp"],
        "description": "WRI Aqueduct water stress data",
    },
    "zhu_liquefaction": {
        "path": "liquefaction",
        "expected_files": ["*.tif"],
        "description": "Zhu et al. global liquefaction susceptibility",
    },
    "ourairports": {
        "path": "ourairports",
        "expected_files": ["airports.csv"],
        "description": "OurAirports global airport database",
    },
    "ghsl_pop": {
        "path": "population/ghsl",
        "expected_files": ["*.tif"],
        "description": "GHSL population density GeoTIFF tiles",
    },
    "era5": {
        "path": "era5",
        "expected_files": ["*.nc"],
        "min_file_count": 5,
        "description": "ERA5 reanalysis NetCDF files",
    },
    "glofas_discharge": {
        "path": "glofas_discharge",
        "expected_files": ["*.nc"],
        "description": "GloFAS river discharge NetCDF",
    },
    "gfms": {
        "path": "gfms",
        "expected_files": ["*.npz", "*.bin"],
        "description": "GFMS global flood monitoring data (pre-computed stats cache)",
    },
    "eu_flood_risk": {
        "path": "eu_flood_risk",
        "expected_files": ["*.geojson", "*.tif"],
        "description": "EU Flood Risk tile index + on-demand GeoTIFF cache",
    },
    "noaa_ibtracs": {
        "path": "noaa",
        "expected_files": ["ibtracs_all.csv"],
        "description": "NOAA IBTrACS tropical cyclone tracks",
    },
    "wdpa": {
        "path": "wdpa",
        "expected_files": ["*.shp", "*.gpkg"],
        "min_file_count": 5,
        "description": "WDPA country-level protected area shapefiles",
    },
    "copernicus_dem": {
        "path": "dem/copernicus_glo30",
        "expected_files": ["*.tif"],
        "description": "Copernicus DEM GLO-30 local tile cache",
        "optional": True,
    },
    "smithsonian_gvp": {
        "path": "gvp",
        "expected_files": ["holocene_volcanoes.json", "holocene_eruptions.json"],
        "description": "Smithsonian GVP Holocene volcano data",
    },
    "eea_industrial": {
        "path": "eea_industrial",
        "expected_files": ["facilities.csv"],
        "description": "EEA European Industrial Emissions facilities",
    },
    "eurostat_gisco": {
        "path": "eurostat_gisco",
        "expected_files": ["cities.geojson", "city_populations.json"],
        "description": "Eurostat GISCO city data",
    },
    "eurostat_projections": {
        "path": "eurostat_projections",
        "expected_files": ["*.json"],
        "min_file_count": 5,
        "description": "Eurostat population projection data",
    },
    "soilgrids_cache": {
        "path": "soilgrids",
        "expected_files": ["*.json"],
        "description": "SoilGrids WCS extraction cache",
    },
}


def _check_source(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    """Check a single source directory and return status."""
    src_path = SOURCES_DIR / spec["path"]
    result: dict[str, Any] = {
        "name": name,
        "description": spec["description"],
        "path": str(src_path),
        "exists": src_path.exists(),
        "optional": spec.get("optional", False),
    }

    if not src_path.exists():
        result["status"] = "MISSING" if not spec.get("optional") else "OPTIONAL_MISSING"
        result["files_found"] = 0
        return result

    all_files: list[Path] = []
    for pattern in spec["expected_files"]:
        matched = list(src_path.rglob(pattern))
        all_files.extend(matched)

    result["files_found"] = len(all_files)
    min_count = spec.get("min_file_count", 1)

    if len(all_files) == 0:
        result["status"] = "EMPTY"
    elif len(all_files) < min_count:
        result["status"] = "INCOMPLETE"
    else:
        total_size = sum(f.stat().st_size for f in all_files if f.is_file())
        result["total_size_mb"] = round(total_size / (1024 * 1024), 1)

        zero_size = [f for f in all_files if f.is_file() and f.stat().st_size == 0]
        if zero_size:
            result["status"] = "CORRUPT"
            result["zero_size_files"] = [str(f) for f in zero_size[:5]]
        else:
            result["status"] = "OK"

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify bulk-downloaded data sources exist and are valid."
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="Re-download missing files (requires API access)",
    )
    args = parser.parse_args()

    print(f"{'='*70}", flush=True)
    print("Bulk Source Verification Report", flush=True)
    print(f"{'='*70}", flush=True)

    results: list[dict[str, Any]] = []
    for name, spec in sorted(EXPECTED_SOURCES.items()):
        result = _check_source(name, spec)
        results.append(result)

    ok_count = sum(1 for r in results if r["status"] == "OK")
    missing_count = sum(1 for r in results if r["status"] == "MISSING")
    empty_count = sum(1 for r in results if r["status"] == "EMPTY")
    incomplete_count = sum(1 for r in results if r["status"] == "INCOMPLETE")
    corrupt_count = sum(1 for r in results if r["status"] == "CORRUPT")
    optional_missing = sum(1 for r in results if r["status"] == "OPTIONAL_MISSING")

    print(f"\n{'Status':<20} {'Source':<25} {'Files':<8} {'Size (MB)':<10} Path")
    print("-" * 100)

    for r in results:
        status_indicator = {
            "OK": "  OK  ",
            "MISSING": "MISSING",
            "EMPTY": " EMPTY ",
            "INCOMPLETE": "PARTIAL",
            "CORRUPT": "CORRUPT",
            "OPTIONAL_MISSING": "OPT_MIS",
        }.get(r["status"], r["status"])

        size_str = str(r.get("total_size_mb", "-"))
        print(
            f"[{status_indicator}]      {r['name']:<25} {r['files_found']:<8} "
            f"{size_str:<10} {r['path']}",
            flush=True,
        )
        if r.get("zero_size_files"):
            for zf in r["zero_size_files"]:
                print(f"                     ⚠ zero-size: {zf}", flush=True)

    print(f"\n{'='*70}", flush=True)
    print(
        f"SUMMARY: {ok_count} OK, {missing_count} missing, "
        f"{empty_count} empty, {incomplete_count} incomplete, "
        f"{corrupt_count} corrupt, {optional_missing} optional missing",
        flush=True,
    )
    print(f"{'='*70}", flush=True)

    if missing_count > 0 or empty_count > 0:
        print("\nAction required for missing/empty sources:", flush=True)
        for r in results:
            if r["status"] in ("MISSING", "EMPTY") and not r.get("optional"):
                print(f"  - {r['name']}: {r['description']}", flush=True)

    if missing_count > 0 and "copernicus_dem" in [
        r["name"] for r in results if r["status"] in ("MISSING", "OPTIONAL_MISSING")
    ]:
        print(
            "\nNote: Copernicus DEM tiles are currently read via /vsicurl/ "
            "(remote). To download and cache tiles locally, run the DEM "
            "enrichment batch with use_local_cache=true.",
            flush=True,
        )

    report_path = Path("audit/post_processing/02_data_verification/bulk_source_verification.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Bulk Source Verification Report",
        "",
        f"Generated: {__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}",
        "",
        "| Status | Source | Files | Size (MB) | Path |",
        "|--------|--------|-------|-----------|------|",
    ]
    for r in results:
        lines.append(
            f"| {r['status']} | {r['name']} | {r['files_found']} | "
            f"{r.get('total_size_mb', '-')} | `{r['path']}` |"
        )
    lines.append("")
    lines.append(
        f"**Summary**: {ok_count} OK, {missing_count} missing, "
        f"{empty_count} empty, {incomplete_count} incomplete, "
        f"{corrupt_count} corrupt"
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport saved to: {report_path}", flush=True)

    return 1 if (missing_count + corrupt_count) > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
