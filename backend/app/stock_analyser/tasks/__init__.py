__all__ = [
    "AnalyzeNewsTask",
    "AnalyzeStocksTask",
    "CalculateLevelsTask",
    "ScrapeSingleStockTask",
    "ScrapeNewsTask",
    "ScrapeStocksTask",
    "ScrapeTrendlyneTask",
    "ScrapeTradingViewTask",
    "SHARED_TASKS",
    "SHARED_INPUT_FIELDS",
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
    if name == "CalculateLevelsTask":
        from app.stock_analyser.tasks.calculate_levels import CalculateLevelsTask
        return CalculateLevelsTask
    if name == "SHARED_TASKS":
        from app.stock_analyser.tasks.scrape_trendlyne import ScrapeTrendlyneTask
        from app.stock_analyser.tasks.scrape_news import ScrapeNewsTask
        from app.stock_analyser.tasks.analyze_news import AnalyzeNewsTask
        from app.stock_analyser.tasks.analyze_stocks import AnalyzeStocksTask
        return [ScrapeTrendlyneTask, ScrapeNewsTask, AnalyzeNewsTask, AnalyzeStocksTask]
    if name == "SHARED_INPUT_FIELDS":
        from app.stock_analyser.analysis.factory import AnalysisFactory
        from app.workflow.base_workflow_config import InputField
        return [
            InputField(
                name="strategy",
                type="str",
                label="Analysis Strategy",
                description="Analysis strategy to use",
                required=False,
                default="momentum",
                choices=list(AnalysisFactory._strategies.keys()),
            ),
            InputField(
                name="enable_news",
                type="bool",
                label="Enable News Analysis",
                description="Scrape and analyze news for each stock",
                required=False,
                default=True,
            ),
            InputField(
                name="num_news_articles",
                type="int",
                label="Number of News Articles",
                description="How many top news articles to include in analysis (scrapes n+2, selects top n by impact and recency)",
                required=False,
                default=3,
            ),
        ]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
