__all__ = ["ScrapeTickersTask"]


def __getattr__(name: str):
    if name == "ScrapeTickersTask":
        from app.stock_scraper.tasks.scrape_tickers import ScrapeTickersTask
        return ScrapeTickersTask
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
