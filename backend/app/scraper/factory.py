from __future__ import annotations

from typing import Type

from app.scraper.exceptions import ConfigError
from app.scraper.interfaces import IndexScraper, StockScraper


class ScraperFactory:
    """Factory for creating scraper instances.

    Scrapers are registered by source name (e.g., "screener", "yahoo").
    Use get_index_scraper() or get_stock_scraper() to retrieve instances.
    """

    _index_scrapers: dict[str, Type[IndexScraper]] = {}
    _stock_scrapers: dict[str, Type[StockScraper]] = {}

    @classmethod
    def register_index_scraper(cls, source: str, scraper_cls: Type[IndexScraper]) -> None:
        """Register an IndexScraper implementation for a given source."""
        cls._index_scrapers[source] = scraper_cls

    @classmethod
    def register_stock_scraper(cls, source: str, scraper_cls: Type[StockScraper]) -> None:
        """Register a StockScraper implementation for a given source."""
        cls._stock_scrapers[source] = scraper_cls

    @classmethod
    def get_index_scraper(cls, source: str = "screener") -> IndexScraper:
        """Get an IndexScraper instance for the given source.

        Args:
            source: The data source name (e.g., "screener").

        Returns:
            An IndexScraper instance.

        Raises:
            ConfigError: If no scraper is registered for the source.
        """
        scraper_cls = cls._index_scrapers.get(source)
        if scraper_cls is None:
            available = list(cls._index_scrapers.keys())
            raise ConfigError(
                f"No IndexScraper registered for source '{source}'. "
                f"Available sources: {available}"
            )
        return scraper_cls()

    @classmethod
    def get_stock_scraper(cls, source: str = "screener") -> StockScraper:
        """Get a StockScraper instance for the given source.

        Args:
            source: The data source name (e.g., "screener").

        Returns:
            A StockScraper instance.

        Raises:
            ConfigError: If no scraper is registered for the source.
        """
        scraper_cls = cls._stock_scrapers.get(source)
        if scraper_cls is None:
            available = list(cls._stock_scrapers.keys())
            raise ConfigError(
                f"No StockScraper registered for source '{source}'. "
                f"Available sources: {available}"
            )
        return scraper_cls()
