from __future__ import annotations

import logging

from app.workflow.workflow_orchestrator_v1.workflow_orchestrator import WorkflowOrchestrator

logger = logging.getLogger(__name__)

SCHEDULED_INDICES: list[dict[str, object]] = [
    {
        "index": "SMALLCAP50",
        "strategy": "momentum",
        "num_stocks": None,
        "selection_criteria": "all",
        "enable_news": True,
        "num_news_articles": 3,
    },
    {
        "index": "1186",
        "strategy": "momentum",
        "num_stocks": None,
        "selection_criteria": "all",
        "enable_news": True,
        "num_news_articles": 3,
    },
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


def refresh_open_trade_prices() -> None:
    from app.trades.prices import fetch_ltp
    from app.trades.repo import TradeRepo

    repo = TradeRepo()
    rows = repo.list_open()
    prices: dict[str, float] = {}
    for ticker in sorted({r["ticker"] for r in rows}):
        price = fetch_ltp(ticker)
        if price is None:
            logger.warning("CMP fetch failed for %s", ticker)
            continue
        prices[ticker] = price
        repo.update_open_price(ticker, price)
    for row in rows:
        cmp = prices.get(row["ticker"])
        if cmp is None:
            continue
        sl, tp = row.get("stop_loss"), row.get("take_profit")
        if sl is not None and cmp <= float(sl):
            repo.close(row["id"], "sl", cmp)
        elif tp is not None and cmp >= float(tp):
            repo.close(row["id"], "tp", cmp)
