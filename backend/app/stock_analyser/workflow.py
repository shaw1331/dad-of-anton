from __future__ import annotations

from app.stock_analyser.tasks import AnalyzeStocksTask, ScrapeStocksTask
from app.workflow.base_workflow_config import BaseWorkflowConfig, InputField
from app.workflow.workflow_orchestrator_v1.workflow_registry import WORKFLOWS

STOCK_ANALYSER_WORKFLOW = BaseWorkflowConfig(
    name="stock_analyser",
    description="Scrapes and analyzes stocks for a given index",
    input_fields=[
        InputField(
            name="index",
            type="str",
            label="Stock Index",
            description="The stock index to analyze (e.g. NIFTY50, SENSEX)",
            required=True,
        ),
        InputField(
            name="strategy",
            type="str",
            label="Analysis Strategy",
            description="Analysis strategy to use (value_investing, momentum)",
            required=False,
            default="value_investing",
        ),
        InputField(
            name="num_stocks",
            type="int",
            label="Number of Stocks",
            description="How many top stocks to analyze (leave empty for all)",
            required=False,
            default=None,
        ),
        InputField(
            name="selection_criteria",
            type="str",
            label="Selection Criteria",
            description="How to pick stocks when number is specified",
            required=False,
            default="all",
            choices=["top", "bottom", "random", "all"],
        ),
    ],
    tasks=[ScrapeStocksTask, AnalyzeStocksTask],
)

WORKFLOWS["stock_analyser"] = STOCK_ANALYSER_WORKFLOW
