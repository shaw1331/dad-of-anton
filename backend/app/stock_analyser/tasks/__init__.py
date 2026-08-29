__all__ = ["ScrapeStocksTask"]


def __getattr__(name: str):
    if name == "ScrapeStocksTask":
        from app.stock_analyser.tasks.scrape_stocks import ScrapeStocksTask
        return ScrapeStocksTask
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
