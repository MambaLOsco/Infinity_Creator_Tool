"""Minimal schema validation helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Any


class SchemaValidationError(ValueError):
    """Raised when a manifest fails schema validation."""


def validate_manifest(data: Any, schema_path: Path) -> None:
    """Validate a payload against a JSON schema file."""
    schema = _load_schema(schema_path)
    validator = _jsonschema_validator(schema)
    if validator:
        errors = sorted(validator.iter_errors(data), key=lambda err: err.path)
        if errors:
            message = "; ".join(error.message for error in errors)
            raise SchemaValidationError(message)
        return
    _validate_fallback(data, schema)


def _load_schema(path: Path) -> dict:
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def _jsonschema_validator(schema: dict) -> Any:
    try:  # pragma: no cover - optional dependency
        import jsonschema  # type: ignore
    except Exception:  # pragma: no cover - optional dependency
        return None
    return jsonschema.Draft7Validator(schema)


def _validate_fallback(data: Any, schema: dict, path: str = "$") -> None:
    schema_type = schema.get("type")
    if schema_type:
        _assert_type(data, schema_type, path)

    if isinstance(data, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in data:
                raise SchemaValidationError(f"Missing required key '{key}' at {path}")
        properties = schema.get("properties", {})
        for key, value in data.items():
            if key in properties:
                _validate_fallback(value, properties[key], f"{path}.{key}")
    elif isinstance(data, list):
        items = schema.get("items")
        if items:
            for idx, item in enumerate(data):
                _validate_fallback(item, items, f"{path}[{idx}]")


def _assert_type(data: Any, schema_type: str, path: str) -> None:
    if schema_type == "object" and not isinstance(data, dict):
        raise SchemaValidationError(f"Expected object at {path}")
    if schema_type == "array" and not isinstance(data, list):
        raise SchemaValidationError(f"Expected array at {path}")
    if schema_type == "string" and not isinstance(data, str):
        raise SchemaValidationError(f"Expected string at {path}")
    if schema_type == "integer" and not isinstance(data, int):
        raise SchemaValidationError(f"Expected integer at {path}")
    if schema_type == "number" and not isinstance(data, (int, float)):
        raise SchemaValidationError(f"Expected number at {path}")
