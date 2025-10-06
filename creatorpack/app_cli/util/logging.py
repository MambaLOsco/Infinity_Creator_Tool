"""JSON structured logging utilities."""
from __future__ import annotations

import json
import logging
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class LogRecord:
    """Structured log record."""

    level: str
    message: str
    timestamp: str
    context: Dict[str, Any]

    def to_json(self) -> str:
        """Serialize the record to JSON."""
        return json.dumps(asdict(self), ensure_ascii=False)


class JsonLogger:
    """Simple JSON logger that writes to a stream."""

    def __init__(self, stream: Any = sys.stdout) -> None:
        self._stream = stream

    def log(self, level: str, message: str, **context: Any) -> None:
        record = LogRecord(
            level=level.upper(),
            message=message,
            timestamp=datetime.now(timezone.utc).isoformat(),
            context=context,
        )
        self._stream.write(record.to_json() + "\n")
        self._stream.flush()

    def info(self, message: str, **context: Any) -> None:
        self.log("info", message, **context)

    def error(self, message: str, **context: Any) -> None:
        self.log("error", message, **context)

    def warning(self, message: str, **context: Any) -> None:
        self.log("warning", message, **context)


_logger: Optional[JsonLogger] = None


def get_logger() -> JsonLogger:
    """Return a singleton :class:`JsonLogger`."""
    global _logger
    if _logger is None:
        _logger = JsonLogger()
        logging.basicConfig(level=logging.INFO)
    return _logger
