from __future__ import annotations

import pytest

from app.stock_jury.evaluation import HistoricalCase, evaluate_cases, validate_dataset
from app.stock_jury.models import CandidateVerdict, JuryVerdict, TradePlan
from app.stock_jury.validation import JuryValidationError, validate_verdict


def candidate(ticker: str, status: str = "NOT_SELECTED", allocation: float = 0) -> CandidateVerdict:
    return CandidateVerdict(
        ticker=ticker,
        rating="AVOID",
        portfolio_status=status,
        allocation_pct=allocation,
        conviction=0.8,
        outlook="BEARISH",
        summary="Supported bearish setup.",
        evidence_refs=[f"{ticker}.REPORT.REASONING"],
        counter_evidence_refs=[f"{ticker}.REPORT.REASONING"],
        trade_plan=TradePlan(entry_mode="IMMEDIATE", entry_low=100, entry_high=100, stop_price=90) if status == "SELECTED" else TradePlan(),
    )


def test_all_candidates_can_be_bad_with_cash() -> None:
    verdict = JuryVerdict(
        decision="NO_ACTION",
        market_view="Evidence is broadly weak.",
        portfolio_reasoning="No candidate has a sufficient edge.",
        candidates=[candidate("AAA"), candidate("BBB")],
        cash_allocation_pct=100,
    )
    validate_verdict(verdict, {"AAA", "BBB"}, {"AAA.REPORT.REASONING", "BBB.REPORT.REASONING"})


def test_allocations_are_validated_without_rating_quotas() -> None:
    verdict = JuryVerdict(
        decision="ACTIONABLE",
        market_view="Two candidates have an edge.",
        portfolio_reasoning="Concentrated selection.",
        candidates=[candidate("AAA", "SELECTED", 50), candidate("BBB", "NOT_SELECTED")],
        cash_allocation_pct=50,
    )
    verdict.candidates[0].rating = "BUY_NOW"
    validate_verdict(verdict, {"AAA", "BBB"}, {"AAA.REPORT.REASONING", "BBB.REPORT.REASONING"})


def test_unknown_evidence_is_rejected() -> None:
    verdict = JuryVerdict(
        decision="NO_ACTION",
        market_view="x",
        portfolio_reasoning="x",
        candidates=[candidate("AAA")],
        cash_allocation_pct=100,
    )
    with pytest.raises(JuryValidationError, match="Unknown evidence"):
        validate_verdict(verdict, {"AAA"}, {"AAA.REPORT.OTHER"})


def test_evaluation_reports_direction_and_returns() -> None:
    metrics = evaluate_cases([
        HistoricalCase("AAA", "BUY_NOW", 0.8, 100, 3, 8),
        HistoricalCase("BBB", "SELL", 0.8, 100, -2, -5),
    ])
    assert metrics["directional_accuracy_40d"] == 1
    assert metrics["actionable_mean_return_40d_pct"] == 8


def test_historical_dataset_requires_minimum_and_no_leakage() -> None:
    cases = [HistoricalCase("AAA", "BUY_NOW", 0.8, 100, 3, 8, case_id="case-1")]
    with pytest.raises(ValueError, match="at least 100"):
        validate_dataset(cases)
    leaked = [HistoricalCase("AAA", "BUY_NOW", 0.8, 100, 3, 8, case_id=f"case-{i}", leakage_detected=i == 1) for i in range(100)]
    with pytest.raises(ValueError, match="Future-data"):
        validate_dataset(leaked)
