from app.stock_analyser.tasks import ScrapeStocksTask
from app.workflow.base_workflow_config import BaseWorkflowConfig, InputField
from app.workflow.workflow_orchestrator_v1.workflow_registry import WORKFLOWS

STOCK_ANALYSER_WORKFLOW = BaseWorkflowConfig(
    name="stock_analyser",
    description="Scrapes stocks and technical analysis for a given index",
    input_fields=[
        InputField(
            name="index",
            type="str",
            label="Stock Index",
            description="The stock index to analyze (e.g. NIFTY50, SENSEX)",
            required=True,
        ),
    ],
    tasks=[ScrapeStocksTask],
)

WORKFLOWS["stock_analyser"] = STOCK_ANALYSER_WORKFLOW
