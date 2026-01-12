"""Brand theme parsing."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

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


def load_brand_theme(path: Path) -> BrandTheme:
    content = _load_yaml(path)
    watermark = content.get("watermark", {}) if isinstance(content, dict) else {}
    watermark_file = watermark.get("file") if isinstance(watermark, dict) else None
    watermark_path = Path(watermark_file) if watermark_file else None
    return BrandTheme(
        name=content.get("name", "Untitled") if isinstance(content, dict) else "Untitled",
        fonts=content.get("fonts", {}) if isinstance(content, dict) else {},
        colors=content.get("colors", {}) if isinstance(content, dict) else {},
        captions=content.get("captions", {}) if isinstance(content, dict) else {},
        intro_path=Path(content["intro"]) if isinstance(content, dict) and content.get("intro") else None,
        outro_path=Path(content["outro"]) if isinstance(content, dict) and content.get("outro") else None,
        watermark_path=watermark_path,
        watermark_position_expr=_resolve_overlay(
            watermark.get("position", "top_right") if isinstance(watermark, dict) else "top_right"
        ),
    )
