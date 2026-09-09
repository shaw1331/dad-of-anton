from __future__ import annotations

from app.stock_analyser.analysis.factory import AnalysisFactory
from app.stock_analyser.tasks import (
    AnalyzeNewsTask,
    AnalyzeStocksTask,
        ScrapeSingleStockTask,
    ScrapeNewsTask,
    ScrapeTrendlyneTask,
)
from app.workflow.base_workflow_config import BaseWorkflowConfig, InputField
from app.workflow.workflow_orchestrator_v1.workflow_registry import WORKFLOWS

SINGLE_STOCK_ANALYSER_WORKFLOW = BaseWorkflowConfig(
    name="single_stock_analyser",
    description="Analyzes a single stock using screener data",
    input_fields=[
        InputField(
            name="ticker",
            type="ticker",
            label="Stock Ticker",
            description="NSE stock ticker symbol (e.g. RELIANCE, TCS)",
            required=True,
        ),
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
            description="Scrape and analyze news for the stock",
            required=False,
            default=False,
        ),
        InputField(
            name="news_lookback_days",
            type="int",
            label="News Lookback Days",
            description="How many days back to look for news articles",
            required=False,
            default=15,
        ),
    ],
    tasks=[
    ScrapeSingleStockTask,
        ScrapeTrendlyneTask,
        ScrapeNewsTask,
        AnalyzeNewsTask,
        AnalyzeStocksTask,
    ],
)

WORKFLOWS["single_stock_analyser"] = SINGLE_STOCK_ANALYSER_WORKFLOW
