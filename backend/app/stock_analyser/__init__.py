__all__ = ["ScrapeStocksTask", "STOCK_ANALYSER_WORKFLOW"]


def __getattr__(name: str):
    if name == "ScrapeStocksTask":
        from app.stock_analyser.tasks.scrape_stocks import ScrapeStocksTask
        return ScrapeStocksTask
    elif name == "STOCK_ANALYSER_WORKFLOW":
        from app.stock_analyser.workflow import STOCK_ANALYSER_WORKFLOW
        return STOCK_ANALYSER_WORKFLOW
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
