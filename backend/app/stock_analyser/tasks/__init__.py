__all__ = ["AnalyzeNewsTask", "AnalyzeStocksTask", "ScrapeNewsTask", "ScrapeStocksTask", "ScrapeTrendlyneTask"]


def __getattr__(name: str):
    if name == "ScrapeStocksTask":
        from app.stock_analyser.tasks.scrape_stocks import ScrapeStocksTask
        return ScrapeStocksTask
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
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
