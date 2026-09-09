from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.stock_jury.service import StockJury

logger = logging.getLogger(__name__)


class RunCandidateStockWorkflowsTask:
    name = "run_candidate_workflows"

    def run(self, ctx: Any) -> None:
        from app.workflow.workflow_orchestrator_v1.workflow_orchestrator import WorkflowOrchestrator

        candidates = ctx.get_input("stocks") or []
        workflow_name = ctx.get_input("analysis_workflow") or "swing_momentum"
        if workflow_name != "swing_momentum":
            raise ValueError(f"Unsupported jury analysis workflow: {workflow_name}")
        orchestrator = WorkflowOrchestrator()
        reports: list[dict] = []
        children: list[dict] = []
        parent_run_id = ctx.get_input("_run_id")
        for candidate in candidates:
            ticker = str(candidate.get("ticker", "")).strip().upper()
            exchange = str(candidate.get("exchange", "NSE")).strip().upper()
            try:
                child_id = orchestrator.create_run(
                    workflow_name,
                    {"ticker": ticker, "exchange": exchange, "enable_news": True, "news_lookback_days": 15},
                    trigger_type="manual",
                )
                asyncio.run(orchestrator.run_workflow(child_id))
                child = orchestrator.run_repo.get(child_id)
                report = child.output or {"ticker": ticker, "error": child.error or "No final output"}
                reports.append({"ticker": ticker, "exchange": exchange, "child_run_id": child_id, **report})
                children.append({"ticker": ticker, "exchange": exchange, "run_id": child_id, "status": child.status})
            except Exception as exc:  # noqa: BLE001
                logger.exception("Candidate workflow failed for %s", ticker)
                reports.append({"ticker": ticker, "exchange": exchange, "error": str(exc)})
                children.append({"ticker": ticker, "exchange": exchange, "status": "failed", "error": str(exc)})
            if parent_run_id:
                from app.workflow.repositories import WorkflowRunRepository

                WorkflowRunRepository().update_output(parent_run_id, {
                    "stage": "candidate_workflows",
                    "children": children,
                    "completed": len(children),
                    "total": len(candidates),
                })
        ctx.set_output(self.name, {"reports": reports, "children": children, "workflow": workflow_name})


class EvaluateStockJuryTask:
    name = "evaluate_stock_jury"

    def run(self, ctx: Any) -> None:
        candidate_output = ctx.get_output("run_candidate_workflows")
        if not candidate_output:
            raise Exception("No candidate workflow results found")
        policy = ctx.get_input("policy") or {}
        verdict = StockJury().evaluate(
            candidate_output["reports"],
            max_holdings=int(policy.get("max_holdings", 3)),
            max_allocation_pct=float(policy.get("max_allocation_pct", 50)),
        )
        verdict["candidate_runs"] = candidate_output["children"]
        ctx.set_output(self.name, verdict)
