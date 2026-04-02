"""Client-specific constants and built-in test sites."""

from __future__ import annotations

from pathlib import Path

from ava_client.resolver import ResolvedSite

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "default.yml"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "tests" / "integrationSnapshots"

VALID_SKIP_CHOICES = ("corine", "osm", "population", "egdi", "seismic", "analysis")

# Three representative coal-to-nuclear candidate sites used for quick test runs.
TEST_SITES: list[ResolvedSite] = [
    ResolvedSite(name="Rovinari", country="RO", lat=44.1456, lon=23.1234, source="coords"),
    ResolvedSite(name="Bełchatów", country="PL", lat=51.2644, lon=19.3278, source="coords"),
    ResolvedSite(name="Tušimice", country="CZ", lat=50.3928, lon=13.3278, source="coords"),
]

# Per-API rate-limit profiles: (inter_request_delay_s, max_concurrency)
RATE_LIMITS: dict[str, tuple[float, int]] = {
    "overpass": (5.0, 1),
    "corine": (2.0, 1),
    "egdi": (1.0, 1),
    "seismic": (0.5, 1),
}

# Delay between OSM endpoint groups within a single site
OSM_INTER_ENDPOINT_DELAY_S = 3.0
