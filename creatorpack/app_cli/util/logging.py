"""Structured logging helpers."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict


_LOGGER_NAME = "creatorpack.job"


def configure_logging(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "job.log.jsonl"

    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(_JsonLogFormatter())

    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.handlers = [handler]
    logger.propagate = False


def job_logger() -> logging.Logger:
    return logging.getLogger(_LOGGER_NAME)


class _JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        data: Dict[str, Any] = {
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if record.args and isinstance(record.args, dict):
            data.update(record.args)
        for attr in ("error", "probe", "count"):
            if hasattr(record, attr):
                data[attr] = getattr(record, attr)
        return json.dumps(data, ensure_ascii=False)
