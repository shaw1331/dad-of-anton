from __future__ import annotations

from app.workflow.workflow_orchestrator_v1.workflow_orchestrator import WorkflowOrchestrator
from app.workflow.workflow_orchestrator_v1.workflow_registry import WORKFLOWS
import app.scraper.screener_scraper  # noqa: F401
import app.scraper.trendlyne_scraper  # noqa: F401


def _register_stock_analyser() -> None:
    import app.stock_analyser.workflow  # noqa: F401
    import app.stock_analyser.single_stock_workflow  # noqa: F401


def _register_stock_jury() -> None:
    import app.stock_jury.workflow  # noqa: F401


_register_stock_analyser()
_register_stock_jury()

__all__ = [
    "WorkflowOrchestrator",
    "WORKFLOWS",
]
