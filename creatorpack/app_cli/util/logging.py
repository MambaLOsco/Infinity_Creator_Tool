"""Structured logging helpers."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict


_LOGGER_NAME = "creatorpack.job"
_RESERVED_LOG_RECORD_KEYS = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys())


def configure_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "job.log.jsonl"

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
        for key, value in record.__dict__.items():
            if key in _RESERVED_LOG_RECORD_KEYS:
                continue
            data[key] = value
        return json.dumps(data, ensure_ascii=False)
