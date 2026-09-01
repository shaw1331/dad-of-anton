from __future__ import annotations


class ScreenerError(Exception):
    """Base exception for NSE screener errors."""


class DataFetchError(ScreenerError):
    """Failed to fetch stock data from NSE/yfinance."""


class ConfigError(ScreenerError):
    """Invalid screener configuration."""
