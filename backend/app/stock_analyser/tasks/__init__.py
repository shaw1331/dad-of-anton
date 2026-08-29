__all__ = ["AnalyzeStocksTask", "ScrapeStocksTask"]


def __getattr__(name: str):
    if name == "ScrapeStocksTask":
        from app.stock_analyser.tasks.scrape_stocks import ScrapeStocksTask
        return ScrapeStocksTask
    if name == "AnalyzeStocksTask":
        from app.stock_analyser.tasks.analyze_stocks import AnalyzeStocksTask
        return AnalyzeStocksTask
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
