"""Shared error types."""
from __future__ import annotations

from typing import Optional


class ExitCodes:
    """Numeric exit codes used by the CLI."""

    SUCCESS = 0
    INVALID_INPUT = 2
    LICENSE_BLOCKED = 3
    DOWNLOAD_FAILED = 4
    MEDIA_ERROR = 5
    TRANSCRIPTION_ERROR = 6


class CreatorPackError(Exception):
    """Base exception with exit code support."""

    exit_code = ExitCodes.INVALID_INPUT

    def __init__(self, message: str, *, exit_code: Optional[int] = None) -> None:
        super().__init__(message)
        if exit_code is not None:
            self.exit_code = exit_code
