"""Brand theme parsing."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml

from ..util.errors import ConfigurationError


@dataclass
class BrandTheme:
    """Represents branding configuration."""

    name: str
    fonts: Dict[str, str]
    colors: Dict[str, str]
    captions: Dict[str, Any]
    intro: str | None
    outro: str | None
    watermark: Dict[str, Any] | None
    safe_areas: Dict[str, bool] | None


def load_theme(path: Path) -> BrandTheme:
    """Load and validate a brand theme YAML file."""
    if not path.exists():
        raise ConfigurationError(f"Brand theme file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ConfigurationError("Brand theme must be a mapping")
    required = {"name", "fonts", "colors", "captions"}
    missing = required - data.keys()
    if missing:
        raise ConfigurationError(f"Brand theme missing fields: {', '.join(sorted(missing))}")
    return BrandTheme(
        name=str(data["name"]),
        fonts=dict(data["fonts"]),
        colors=dict(data["colors"]),
        captions=dict(data["captions"]),
        intro=data.get("intro"),
        outro=data.get("outro"),
        watermark=data.get("watermark"),
        safe_areas=data.get("safe_areas"),
    )
