__all__ = ["ScrapeTickersTask", "STOCK_SCRAPER_WORKFLOW"]


def __getattr__(name: str):
    if name == "ScrapeTickersTask":
        from app.stock_scraper.tasks.scrape_tickers import ScrapeTickersTask
        return ScrapeTickersTask
    elif name == "STOCK_SCRAPER_WORKFLOW":
        from app.stock_scraper.workflow import STOCK_SCRAPER_WORKFLOW
        return STOCK_SCRAPER_WORKFLOW
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
