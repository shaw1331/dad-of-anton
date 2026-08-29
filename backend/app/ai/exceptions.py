from __future__ import annotations


class AnalysisError(Exception):
    """Base exception for ai module."""


class GraphError(AnalysisError):
    """Raised when graph execution fails."""


class ConfigError(AnalysisError):
    """Raised when there is a configuration error."""
