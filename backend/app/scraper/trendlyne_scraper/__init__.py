from app.scraper.factory import ScraperFactory
from app.scraper.trendlyne_scraper.index_scraper import TrendlyneIndexScraper
from app.scraper.trendlyne_scraper.stock_scraper import TrendlyneStockScraper

ScraperFactory.register_index_scraper("trendlyne", TrendlyneIndexScraper)
ScraperFactory.register_stock_scraper("trendlyne", TrendlyneStockScraper)
