# man_hours: 4.0
"""Configuration loading: YAML + environment variables + validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CONFIG = _PROJECT_ROOT / "config" / "default.yml"


class DatabaseSettings(BaseSettings):
    host: str = "localhost"
    port: int = 5432
    db: str = "atoms_vs_ashes"
    user: str = "atoms"
    password: str = "changeme"

    model_config = {"env_prefix": "POSTGRES_"}

    @property
    def url(self) -> str:
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.db}"
        )


class Settings:
    """Merged view of YAML config + env-driven database settings."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        path = Path(config_path) if config_path else _DEFAULT_CONFIG
        with open(path) as f:
            self._yaml: dict[str, Any] = yaml.safe_load(f) or {}
        self.database = DatabaseSettings()

    # --- convenience accessors -------------------------------------------

    @property
    def in_scope_countries(self) -> list[str]:
        return self._yaml.get("ingestion", {}).get("in_scope_countries", [])

    @property
    def source_files(self) -> dict[str, str]:
        return self._yaml.get("ingestion", {}).get("source_files", {})

    @property
    def supplementary_sites(self) -> list[dict[str, Any]]:
        return self._yaml.get("ingestion", {}).get("supplementary_sites", [])

    @property
    def screening(self) -> dict[str, Any]:
        return self._yaml.get("screening", {})

    @property
    def smr_types(self) -> dict[str, dict[str, Any]]:
        return self.screening.get("smr_types", {})

    @property
    def basic_filters(self) -> dict[str, dict[str, Any]]:
        return self.screening.get("basic_filters", {})

    @property
    def connectors(self) -> dict[str, Any]:
        return self._yaml.get("connectors", {})

    def connector_config(self, slug: str) -> dict[str, Any]:
        """Return config dict for a specific connector by slug."""
        return self.connectors.get(slug, {})

    @property
    def retry(self) -> dict[str, Any]:
        return self._yaml.get("retry", {})

    @property
    def cache(self) -> dict[str, Any]:
        return self._yaml.get("cache", {})

    @property
    def scoring_weights(self) -> dict[str, float]:
        return self._yaml.get("scoring", {}).get("weights", {})

    @property
    def alert_thresholds(self) -> dict[str, float]:
        return self._yaml.get("observability", {}).get("alert_thresholds", {})

    def raw(self) -> dict[str, Any]:
        return dict(self._yaml)
