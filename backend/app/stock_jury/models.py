from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Rating = Literal["BUY_NOW", "STAGED_ENTRY", "WATCH", "AVOID", "SELL"]
PortfolioStatus = Literal["SELECTED", "NOT_SELECTED", "INSUFFICIENT_DATA"]


class TradePlan(BaseModel):
    entry_mode: Literal["IMMEDIATE", "TRIGGERED", "NONE"] = "NONE"
    entry_low: float | None = None
    entry_high: float | None = None
    trigger_expiry_sessions: int | None = Field(default=None, ge=1, le=40)
    stop_price: float | None = None
    profit_targets: list[float] = Field(default_factory=list)
    max_holding_sessions: int = Field(default=40, ge=1, le=40)
    expected_return_direction: Literal["POSITIVE", "FLAT", "NEGATIVE", "UNKNOWN"] = "UNKNOWN"


class CandidateVerdict(BaseModel):
    ticker: str
    name: str = ""
    rank: int | None = Field(default=None, ge=1)
    rating: Rating
    portfolio_status: PortfolioStatus
    allocation_pct: float = Field(default=0, ge=0, le=100)
    conviction: float = Field(ge=0, le=1)
    outlook: Literal["BULLISH", "NEUTRAL", "BEARISH"]
    summary: str
    supporting_evidence: list[str] = Field(default_factory=list)
    counter_evidence: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    counter_evidence_refs: list[str] = Field(default_factory=list)
    catalysts: list[str] = Field(default_factory=list)
    key_risks: list[str] = Field(default_factory=list)
    success_scenario: str = ""
    underperformance_scenario: str = ""
    entry_conditions: list[str] = Field(default_factory=list)
    profit_taking_conditions: list[str] = Field(default_factory=list)
    invalidation_conditions: list[str] = Field(default_factory=list)
    reconsideration_conditions: list[str] = Field(default_factory=list)
    comparative_advantages: list[str] = Field(default_factory=list)
    comparative_disadvantages: list[str] = Field(default_factory=list)
    better_than: list[str] = Field(default_factory=list)
    lost_to: list[str] = Field(default_factory=list)
    data_quality_warnings: list[str] = Field(default_factory=list)
    trade_plan: TradePlan = Field(default_factory=TradePlan)


class JuryBallot(BaseModel):
    juror: str
    candidates: list[CandidateVerdict]
    reasoning: str = ""
    disagreements: list[str] = Field(default_factory=list)


class JuryChallenge(BaseModel):
    challenger: Literal["BULL", "BEAR"]
    challenged_tickers: list[str] = Field(default_factory=list)
    arguments: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    unresolved_risks: list[str] = Field(default_factory=list)


class JuryVerdict(BaseModel):
    schema_version: str = "stock_jury.v1"
    decision: Literal["ACTIONABLE", "NO_ACTION"]
    market_view: str
    portfolio_reasoning: str
    candidates: list[CandidateVerdict]
    selected: list[CandidateVerdict] = Field(default_factory=list)
    rejected: list[CandidateVerdict] = Field(default_factory=list)
    cash_allocation_pct: float = Field(ge=0, le=100)
    concentration_risks: list[str] = Field(default_factory=list)
    data_quality_warnings: list[str] = Field(default_factory=list)
    prompt_version: str = "stock_jury.v1"
    jury_audit: dict = Field(default_factory=dict)
