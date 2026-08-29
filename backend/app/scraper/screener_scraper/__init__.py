from app.scraper.factory import ScraperFactory
from app.scraper.screener_scraper.index_scraper import ScreenerIndexScraper
from app.scraper.screener_scraper.stock_scraper import ScreenerStockScraper

ScraperFactory.register_index_scraper("screener", ScreenerIndexScraper)
ScraperFactory.register_stock_scraper("screener", ScreenerStockScraper)

__all__ = ["ScreenerIndexScraper", "ScreenerStockScraper"]
