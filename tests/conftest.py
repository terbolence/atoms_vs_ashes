"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from atoms_vs_ashes.config import Settings


@pytest.fixture()
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture()
def settings(project_root: Path) -> Settings:
    return Settings(project_root / "config" / "default.yml")


@pytest.fixture()
def sample_site_row() -> dict[str, str | None]:
    """A single row as it comes from the GEM tracker, pre-column-map."""
    return {
        "GEM unit/phase ID": "G100001057899",
        "GEM location ID": "L100001050201",
        "Country/Area": "Romania",
        "Wiki URL": "https://example.com",
        "Plant name": "Test Plant",
        "Unit name": "Unit 1",
        "Plant name (other)": "Alt Name",
        "Plant name (local)": None,
        "Owner": "Test Owner",
        "Owner GEM Entity ID": "E000001",
        "Parent": "Parent Co",
        "Parent GEM Entity ID": "E000002",
        "Capacity (MW)": "500",
        "Status": "operating",
        "Start year": "2005",
        "Retired year": None,
        "Planned retirement": None,
        "Coal phaseout year": "2030",
        "Net zero year": None,
        "Combustion technology": "subcritical",
        "Coal type": "lignite",
        "Coal source": "Oltenia",
        "Conversion to (fuel)": None,
        "Conversion to (GEM unit ID)": None,
        "Alternate Fuel": None,
        "Location": "Gorj County",
        "Local area (taluk, county)": "Rovinari",
        "Major area (prefecture, district)": "Gorj",
        "Subnational unit (province, state)": "Gorj",
        "Subregion": "Eastern Europe",
        "Region": "Europe",
        "Latitude": "44.1456",
        "Longitude": "23.1234",
        "Location accuracy": "exact",
        "Permits": None,
        "Permit Date": None,
        "Permit Parsed": None,
        "Captive": None,
        "Captive industry use": None,
        "Captive residential use": None,
        "CHP": None,
        "Capacity factor": "0.6",
        "Plant age (years)": "20",
        "Heat rate (Btu per kWh)": "10000",
        "Emission factor (kg of CO2 per TJ)": "101000",
        "Annual CO2 (million tonnes / annum)": "3.5",
        "Remaining plant lifetime (years)": "10",
        "Lifetime CO2 (million tonnes)": "35",
        "China capacity payment recipient": None,
    }


@pytest.fixture()
def sample_ownership_row() -> dict[str, str | None]:
    """A single ownership row matching the Coal Plant Ownership sheet."""
    return {
        "Parent GEM Entity ID": "E000002",
        "Parent": "Parent Co",
        "Parent Registration Country": "Romania",
        "Parent Headquarters Country": "Romania",
        "Project": "Test Plant Unit 1",
        "Share": "100",
        "Ownership Path": "Parent Co -> Test Plant Unit 1 (100%)",
        "Immediate Project Owner": "Test Owner",
        "Immediate Project Owner GEM Entity ID": "E000001",
        "Tracker": "Global Coal Plant Tracker",
        "Status": "operating",
        "Capacity (MW)": "500",
        "GEM location ID": "L100001050201",
        "GEM unit ID": "G100001057899",
    }
