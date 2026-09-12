from __future__ import annotations

from app.stock_analyser.tasks import (
    SHARED_INPUT_FIELDS,
    SHARED_TASKS,
    CalculateLevelsTask,
    ScrapeSingleStockTask,
    ScrapeTradingViewTask,
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
        *SHARED_INPUT_FIELDS,
    ],
    tasks=[
        ScrapeSingleStockTask,
        ScrapeTradingViewTask,
        CalculateLevelsTask,
        *SHARED_TASKS,
    ],
)

WORKFLOWS["single_stock_analyser"] = SINGLE_STOCK_ANALYSER_WORKFLOW
