from __future__ import annotations

from app.stock_analyser.tasks import (
    AnalyzeNewsTask,
    AnalyzeStocksTask,
    ScrapeNewsTask,
    ScrapeStocksTask,
    ScrapeTradingViewTask,
    ScrapeTrendlyneTask,
)
from app.stock_jury.tasks import EvaluateStockJuryTask, RunCandidateStockWorkflowsTask
from app.workflow.base_workflow_config import BaseWorkflowConfig, InputField
from app.workflow.workflow_orchestrator_v1.workflow_registry import WORKFLOWS


SWING_MOMENTUM_WORKFLOW = BaseWorkflowConfig(
    name="swing_momentum",
    description="Single-stock 4–8 week momentum analysis",
    input_fields=[
        InputField(name="ticker", type="str", label="Ticker", required=True),
        InputField(name="exchange", type="str", label="Exchange", required=False, default="NSE"),
        InputField(name="enable_news", type="bool", label="Enable News", required=False, default=True),
        InputField(name="news_lookback_days", type="int", label="News Lookback", required=False, default=15),
        InputField(name="strategy", type="str", label="Strategy", required=False, default="swing_momentum"),
    ],
    tasks=[ScrapeStocksTask, ScrapeTrendlyneTask, ScrapeTradingViewTask, ScrapeNewsTask, AnalyzeNewsTask, AnalyzeStocksTask],
)

STOCK_JURY_WORKFLOW = BaseWorkflowConfig(
    name="stock_jury",
    description="Sequential stock analysis followed by parallel evidence-grounded jury",
    input_fields=[
        InputField(name="stocks", type="json", label="Stocks", description="Ticker and exchange objects", required=True),
        InputField(name="analysis_workflow", type="str", label="Analysis Workflow", required=False, default="swing_momentum", choices=["swing_momentum"]),
        InputField(name="policy", type="json", label="Jury Policy", required=False, default={}),
    ],
    tasks=[RunCandidateStockWorkflowsTask, EvaluateStockJuryTask],
)

WORKFLOWS["swing_momentum"] = SWING_MOMENTUM_WORKFLOW
WORKFLOWS["stock_jury"] = STOCK_JURY_WORKFLOW
