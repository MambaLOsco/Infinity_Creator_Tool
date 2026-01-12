"""Brand theme parsing."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..util.errors import CreatorPackError, ExitCodes

try:  # pragma: no cover - optional dependency
    import yaml  # type: ignore
except Exception:  # pragma: no cover - fallback parser
    yaml = None


def _fallback_yaml_load(content: str) -> dict:
    """Very small YAML subset parser to avoid hard dependency."""

    root: dict[str, object] = {}
    stack: list[tuple[int, dict[str, object]]] = [(0, root)]

    for line in content.splitlines():
        if not line.strip() or line.strip().startswith('#'):
            continue
        indent = len(line) - len(line.lstrip())
        key, _, raw_value = line.partition(':')
        key = key.strip()
        value = raw_value.strip()

        while stack and indent < stack[-1][0]:
            stack.pop()
        container = stack[-1][1]

        if not value:
            new_map: dict[str, object] = {}
            container[key] = new_map
            stack.append((indent + 2, new_map))
            continue

        if value.startswith('"') and value.endswith('"'):
            parsed: object = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            parsed = value[1:-1]
        elif value.lower() in {"true", "false"}:
            parsed = value.lower() == "true"
        else:
            try:
                parsed = float(value) if '.' in value else int(value)
            except ValueError:
                parsed = value
        container[key] = parsed

    return root


def _load_yaml(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(content)
    return _fallback_yaml_load(content)


@dataclass
class BrandTheme:
    name: str
    fonts: dict
    colors: dict
    captions: dict
    intro_path: Optional[Path]
    outro_path: Optional[Path]
    watermark_path: Optional[Path]
    watermark_position_expr: str
    watermark_scale: float
    watermark_opacity: float

    @property
    def watermark_position(self) -> str:
        return self.watermark_position_expr


def _resolve_overlay(position: str) -> str:
    mapping = {
        "top_left": "10:10",
        "top_right": "main_w-overlay_w-10:10",
        "bottom_left": "10:main_h-overlay_h-10",
        "bottom_right": "main_w-overlay_w-10:main_h-overlay_h-10",
        "center": "(main_w-overlay_w)/2:(main_h-overlay_h)/2",
    }
    return mapping.get(position, "10:10")


class BrandThemeError(CreatorPackError):
    """Raised when branding configuration is invalid."""

    exit_code = ExitCodes.INVALID_INPUT


def load_brand_theme(path: Path) -> BrandTheme:
    content = _load_yaml(path)
    if not isinstance(content, dict):
        raise BrandThemeError("Brand theme config must be a YAML mapping")

    watermark = content.get("watermark", {})
    if watermark is None:
        watermark = {}
    if not isinstance(watermark, dict):
        raise BrandThemeError("Brand theme watermark config must be a mapping")

    watermark_file = watermark.get("file")
    watermark_path = Path(watermark_file) if watermark_file else None
    if watermark_path and not watermark_path.exists():
        raise BrandThemeError(f"Watermark file not found: {watermark_path}")

    scale = float(watermark.get("scale", 1.0))
    opacity = float(watermark.get("opacity", 1.0))
    if not 0.05 <= scale <= 1.0:
        raise BrandThemeError("Watermark scale must be between 0.05 and 1.0")
    if not 0.0 < opacity <= 1.0:
        raise BrandThemeError("Watermark opacity must be between 0 and 1.0")

    return BrandTheme(
        name=content.get("name", "Untitled"),
        fonts=content.get("fonts", {}),
        colors=content.get("colors", {}),
        captions=content.get("captions", {}),
        intro_path=Path(content["intro"]) if content.get("intro") else None,
        outro_path=Path(content["outro"]) if content.get("outro") else None,
        watermark_path=watermark_path,
        watermark_position_expr=_resolve_overlay(watermark.get("position", "top_right")),
        watermark_scale=scale,
        watermark_opacity=opacity,
    )
