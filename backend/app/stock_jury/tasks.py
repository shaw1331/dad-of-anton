from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from app.stock_jury.service import StockJury

logger = logging.getLogger(__name__)


class RunCandidateStockWorkflowsTask:
    name = "run_candidate_workflows"

    def run(self, ctx: Any) -> None:
        from app.workflow.workflow_orchestrator_v1.workflow_orchestrator import WorkflowOrchestrator

        candidates = ctx.get_input("stocks") or []
        if not 2 <= len(candidates) <= 10:
            raise ValueError("A jury run requires 2 to 10 stocks")
        workflow_name = ctx.get_input("analysis_workflow") or "swing_momentum"
        if workflow_name != "swing_momentum":
            raise ValueError(f"Unsupported jury analysis workflow: {workflow_name}")
        orchestrator = WorkflowOrchestrator()
        reports: list[dict] = []
        children: list[dict] = []
        parent_run_id = ctx.get_input("_run_id")
        def run_candidate(candidate: dict) -> tuple[dict, dict]:
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
                return (
                    {"ticker": ticker, "exchange": exchange, "child_run_id": child_id, **report},
                    {"ticker": ticker, "exchange": exchange, "run_id": child_id, "status": child.status},
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception("Candidate workflow failed for %s", ticker)
                return (
                    {"ticker": ticker, "exchange": exchange, "error": str(exc)},
                    {"ticker": ticker, "exchange": exchange, "status": "failed", "error": str(exc)},
                )

        with ThreadPoolExecutor(max_workers=len(candidates)) as pool:
            futures = [pool.submit(run_candidate, candidate) for candidate in candidates]
            for future in as_completed(futures):
                report, child = future.result()
                reports.append(report)
                children.append(child)
                if parent_run_id:
                    from app.workflow.repositories import WorkflowRunRepository

                    WorkflowRunRepository().update_output(parent_run_id, {
                        "stage": "candidate_workflows",
                        "candidate_runs": children,
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
