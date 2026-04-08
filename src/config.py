"""Load and validate config.yaml with defaults."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class PageRange:
    start: int = 154
    end: int = 660


@dataclass
class GeocodingConfig:
    provider: str = "ban"
    cache_path: str = "data/communes_geo.json"
    throttle_rps: int = 10


@dataclass
class UIConfig:
    port: int = 8051
    debug: bool = True


@dataclass
class AppConfig:
    pdf_path: str = "../../RawData/GrosFichiers - Béhague/CAG Bas-Rhin.pdf"
    page_range: PageRange = field(default_factory=PageRange)
    source_label: str = "cag_67"
    department: str = "67"
    db_path: str = "data/cag67.duckdb"
    geocoding: GeocodingConfig = field(default_factory=GeocodingConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    log_level: str = "INFO"


def load_config(path: Path | None = None) -> AppConfig:
    """Load config from YAML file, falling back to defaults."""
    if path is None:
        path = Path("config.yaml")

    if not path.exists():
        return AppConfig()

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    pr = raw.get("page_range", {})
    geo = raw.get("geocoding", {})
    ui = raw.get("ui", {})

    return AppConfig(
        pdf_path=raw.get("pdf_path", AppConfig.pdf_path),
        page_range=PageRange(start=pr.get("start", 154), end=pr.get("end", 660)),
        source_label=raw.get("source_label", "cag_67"),
        department=raw.get("department", "67"),
        db_path=raw.get("db_path", "data/cag67.duckdb"),
        geocoding=GeocodingConfig(
            provider=geo.get("provider", "ban"),
            cache_path=geo.get("cache_path", "data/communes_geo.json"),
            throttle_rps=geo.get("throttle_rps", 10),
        ),
        ui=UIConfig(port=ui.get("port", 8051), debug=ui.get("debug", True)),
        log_level=raw.get("log_level", "INFO"),
    )
