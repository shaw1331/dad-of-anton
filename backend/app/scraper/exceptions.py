from __future__ import annotations


class ScraperError(Exception):
    """Base exception for scraper module."""


class RateLimitError(ScraperError):
    """Raised when rate limit is exceeded."""


class NotFoundError(ScraperError):
    """Raised when a resource is not found."""


class ConfigError(ScraperError):
    """Raised when there is a configuration error."""
