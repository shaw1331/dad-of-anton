from __future__ import annotations

import pytest

from app.stock_jury.evaluation import HistoricalCase, evaluate_cases
from app.stock_jury.models import CandidateVerdict, JuryVerdict
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
        evidence_refs=["REPORT.REASONING"],
    )


def test_all_candidates_can_be_bad_with_cash() -> None:
    verdict = JuryVerdict(
        decision="NO_ACTION",
        market_view="Evidence is broadly weak.",
        portfolio_reasoning="No candidate has a sufficient edge.",
        candidates=[candidate("AAA"), candidate("BBB")],
        cash_allocation_pct=100,
    )
    validate_verdict(verdict, {"AAA", "BBB"}, {"REPORT.REASONING"})


def test_allocations_are_validated_without_rating_quotas() -> None:
    verdict = JuryVerdict(
        decision="ACTIONABLE",
        market_view="Two candidates have an edge.",
        portfolio_reasoning="Concentrated selection.",
        candidates=[candidate("AAA", "SELECTED", 50), candidate("BBB", "NOT_SELECTED")],
        cash_allocation_pct=50,
    )
    verdict.candidates[0].rating = "BUY_NOW"
    validate_verdict(verdict, {"AAA", "BBB"}, {"REPORT.REASONING"})


def test_unknown_evidence_is_rejected() -> None:
    verdict = JuryVerdict(
        decision="NO_ACTION",
        market_view="x",
        portfolio_reasoning="x",
        candidates=[candidate("AAA")],
        cash_allocation_pct=100,
    )
    with pytest.raises(JuryValidationError, match="Unknown evidence"):
        validate_verdict(verdict, {"AAA"}, {"REPORT.OTHER"})


def test_evaluation_reports_direction_and_returns() -> None:
    metrics = evaluate_cases([
        HistoricalCase("AAA", "BUY_NOW", 0.8, 100, 3, 8),
        HistoricalCase("BBB", "SELL", 0.8, 100, -2, -5),
    ])
    assert metrics["directional_accuracy_40d"] == 1
    assert metrics["actionable_mean_return_40d_pct"] == 8
