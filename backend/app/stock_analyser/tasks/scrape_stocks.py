from __future__ import annotations

from typing import TYPE_CHECKING

from app.workflow.base_workflow_task import BaseWorkflowTask

if TYPE_CHECKING:
    from app.workflow.base_workflow_context import BaseWorkflowContext


class ScrapeStocksTask(BaseWorkflowTask):
    name = "scrape_stocks"

    def run(self, ctx: BaseWorkflowContext) -> None:
        index = ctx.get_input("index")
        # TODO: Scrape all stocks in the index
        # TODO: Scrape technical analysis for each stock
        ctx.set_output(self.name, {"index": index, "stocks": []})
