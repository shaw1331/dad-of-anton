"""Reconstruct the analysis prompt sent to AnalyzeStocksTask for a given workflow run.

Usage:
    cd backend && python -m pytest tests/test_reconstruct_prompt.py --run-id=<RUN_ID> -v -s
"""
from __future__ import annotations

import pytest

from app.stock_analyser.analysis.factory import AnalysisFactory
from app.workflow.repositories import WorkflowRunRepository, WorkflowTaskRunRepository

run_repo = WorkflowRunRepository()
task_run_repo = WorkflowTaskRunRepository()

EXPECTED_WORKFLOW = "single_stock_analyser"
ANALYZE_TASK_NAME = "analyze_stocks"


@pytest.fixture
def run_id(request):
    val = request.config.getoption("--run-id")
    if not val:
        pytest.fail("--run-id is required. Usage: --run-id=<RUN_ID>")
    return val


def _task_output_by_name(task_runs, name: str) -> dict | None:
    for tr in task_runs:
        if tr.task_name == name and tr.status == "completed" and tr.output:
            return tr.output
    return None


def test_reconstruct_analysis_prompt(run_id: str) -> None:
    run = run_repo.get(run_id)
    assert run.workflow_name == EXPECTED_WORKFLOW, (
        f"Run {run_id} is '{run.workflow_name}', expected '{EXPECTED_WORKFLOW}'"
    )

    task_runs = task_run_repo.list_by_run(run_id)

    analyze_task_run = None
    for tr in task_runs:
        if tr.task_name == ANALYZE_TASK_NAME:
            analyze_task_run = tr
            break
    assert analyze_task_run is not None, f"No '{ANALYZE_TASK_NAME}' task run found for {run_id}"

    strategy_name = (run.input or {}).get("strategy", "momentum")
    strategy = AnalysisFactory.get(strategy_name)

    scrape_output = _task_output_by_name(task_runs, "scrape_stocks")
    assert scrape_output is not None, "scrape_stocks output not found"
    stocks = scrape_output["stocks"]

    trendlyne_output = _task_output_by_name(task_runs, "scrape_trendlyne")
    trendlyne_map: dict[str, dict] = {}
    if trendlyne_output:
        trendlyne_map = {s["ticker"]: s for s in trendlyne_output.get("stocks", [])}

    tradingview_output = _task_output_by_name(task_runs, "scrape_tradingview")
    tradingview_map: dict[str, list] = {}
    if tradingview_output:
        tradingview_map = tradingview_output.get("candles", {})

    levels_output = _task_output_by_name(task_runs, "calculate_levels")
    levels_map: dict[str, dict] = {}
    if levels_output:
        levels_map = levels_output.get("levels", {})

    news_output = _task_output_by_name(task_runs, "analyze_news")
    analyzed_news_map: dict[str, list] = {}
    if news_output:
        analyzed_news_map = news_output.get("analyses", {})

    prompts = {}
    for stock in stocks:
        ticker = stock.get("ticker", "UNKNOWN")
        stock_with_tl = {
            **stock,
            "trendlyne": trendlyne_map.get(ticker),
            "tradingview": tradingview_map.get(ticker, []),
            "levels": levels_map.get(ticker),
        }
        stock_news = analyzed_news_map.get(ticker, [])
        prompt = strategy.get_analysis_prompt(stock_with_tl, stock_news)
        prompts[ticker] = prompt

    for ticker, prompt in prompts.items():
        print("\n" + "=" * 60)
        print(f"PROMPT FOR {ticker} (run {run_id})")
        print("=" * 60)
        print(prompt)
        print("=" * 60)

    assert len(prompts) > 0, "No prompts reconstructed"
