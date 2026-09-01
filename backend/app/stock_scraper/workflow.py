from __future__ import annotations

from app.stock_scraper.tasks import ScrapeTickersTask
from app.workflow.base_workflow_config import BaseWorkflowConfig, InputField
from app.workflow.workflow_orchestrator_v1.workflow_registry import WORKFLOWS

STOCK_SCRAPER_WORKFLOW = BaseWorkflowConfig(
    name="stock_scraper",
    description="Scrapes stock data for a list of tickers from screener.in",
    input_fields=[
        InputField(
            name="tickers",
            type="str",
            label="Stock Tickers",
            description="Comma-separated list of stock tickers (e.g. RELIANCE, TCS, INFY)",
            required=True,
        ),
    ],
    tasks=[ScrapeTickersTask],
)

WORKFLOWS["stock_scraper"] = STOCK_SCRAPER_WORKFLOW
