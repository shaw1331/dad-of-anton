__all__ = [
    "AnalyzeNewsTask",
    "AnalyzeStocksTask",
    "ScrapeSingleStockTask",
    "ScrapeNewsTask",
    "ScrapeStocksTask",
    "ScrapeTrendlyneTask",
    "ScrapeTradingViewTask",
]


def __getattr__(name: str):
    if name == "ScrapeStocksTask":
        from app.stock_analyser.tasks.scrape_stocks import ScrapeStocksTask
        return ScrapeStocksTask
    if name == "ScrapeSingleStockTask":
        from app.stock_analyser.tasks.scrape_single_stock import ScrapeSingleStockTask
        return ScrapeSingleStockTask
    if name == "ScrapeTrendlyneTask":
        from app.stock_analyser.tasks.scrape_trendlyne import ScrapeTrendlyneTask
        return ScrapeTrendlyneTask
    if name == "ScrapeNewsTask":
        from app.stock_analyser.tasks.scrape_news import ScrapeNewsTask
        return ScrapeNewsTask
    if name == "AnalyzeStocksTask":
        from app.stock_analyser.tasks.analyze_stocks import AnalyzeStocksTask
        return AnalyzeStocksTask
    if name == "AnalyzeNewsTask":
        from app.stock_analyser.tasks.analyze_news import AnalyzeNewsTask
        return AnalyzeNewsTask
    if name == "ScrapeTradingViewTask":
        from app.stock_analyser.tasks.scrape_tradingview import ScrapeTradingViewTask
        return ScrapeTradingViewTask
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
