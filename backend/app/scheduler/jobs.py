from __future__ import annotations

import logging

from app.workflow.workflow_orchestrator_v1.workflow_orchestrator import WorkflowOrchestrator

logger = logging.getLogger(__name__)

SCHEDULED_INDICES: list[dict[str, str]] = [
    {"index": "SMALLCAP50", "strategy": "momentum"},
    {"index": "1186", "strategy": "momentum"},  # BSE Momentum Index
]

orchestrator = WorkflowOrchestrator()


async def run_scheduled_stock_analysis() -> None:
    logger.info("Scheduled stock analysis started for %d indices", len(SCHEDULED_INDICES))

    for entry in SCHEDULED_INDICES:
        index_name = entry["index"]
        try:
            run_id = orchestrator.create_run("stock_analyser", entry, trigger_type="scheduled")
            logger.info("Starting workflow run %s for index %s", run_id, index_name)
            await orchestrator.run_workflow(run_id)
            logger.info("Completed workflow run %s for index %s", run_id, index_name)
        except Exception:
            logger.exception("Scheduled stock analysis failed for index %s", index_name)
