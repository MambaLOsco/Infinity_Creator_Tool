"""Custom error types for CreatorPack."""
from __future__ import annotations


class CreatorPackError(Exception):
    """Base class for predictable errors raised by CreatorPack."""


class LicenseError(CreatorPackError):
    """Raised when an asset fails license validation."""


class DownloadError(CreatorPackError):
    """Raised when a remote asset cannot be downloaded."""


class MediaProcessingError(CreatorPackError):
    """Raised when ffmpeg media operations fail."""


class ConfigurationError(CreatorPackError):
    """Raised when user provided configuration is invalid."""
