from __future__ import annotations

import re

from app.stock_jury.models import JuryVerdict


class JuryValidationError(ValueError):
    pass


_NUMBER = re.compile(r"(?<![A-Za-z])[+-]?\d+(?:\.\d+)?%?")


def _numbers(text: str) -> set[str]:
    return {match.rstrip("%").lstrip("+") for match in _NUMBER.findall(text)}


def validate_ballot(ballot, expected_role: str, candidate_tickers: set[str]) -> None:
    if ballot.juror != expected_role:
        raise JuryValidationError(f"Ballot role must be {expected_role}")
    seen = [row.ticker.upper() for row in ballot.candidates]
    if set(seen) != {ticker.upper() for ticker in candidate_tickers} or len(seen) != len(set(seen)):
        raise JuryValidationError(f"{expected_role} ballot must contain every candidate exactly once")


def validate_verdict(
    verdict: JuryVerdict,
    candidate_tickers: set[str],
    evidence_ids: set[str] | None = None,
    max_holdings: int = 3,
    max_allocation_pct: float = 50,
) -> JuryVerdict:
    normalized = {ticker.upper() for ticker in candidate_tickers}
    rows = verdict.candidates
    seen = [row.ticker.upper() for row in rows]
    if set(seen) != normalized or len(seen) != len(set(seen)):
        raise JuryValidationError("Every candidate must appear exactly once in the verdict")

    if evidence_ids is not None:
        refs = {ref for row in rows for ref in row.evidence_refs + row.counter_evidence_refs}
        unknown = refs - evidence_ids
        if unknown:
            raise JuryValidationError(f"Unknown evidence references: {sorted(unknown)}")
        for row in rows:
            foreign = {
                ref for ref in row.evidence_refs + row.counter_evidence_refs
                if not ref.startswith(f"{row.ticker.upper()}.")
            }
            if foreign:
                raise JuryValidationError(f"{row.ticker} cites another candidate's evidence: {sorted(foreign)}")

    selected = [row for row in rows if row.portfolio_status == "SELECTED"]
    if len(selected) > max_holdings:
        raise JuryValidationError("Selected holdings exceed the configured maximum")

    total = verdict.cash_allocation_pct + sum(row.allocation_pct for row in rows)
    if abs(total - 100) > 0.01:
        raise JuryValidationError(f"Allocation total must equal 100, got {total}")

    for row in rows:
        if row.allocation_pct > max_allocation_pct:
            raise JuryValidationError(f"{row.ticker} exceeds the allocation limit")
        if row.portfolio_status != "SELECTED" and row.allocation_pct != 0:
            raise JuryValidationError(f"Unselected stock {row.ticker} has an allocation")
        if row.portfolio_status == "SELECTED" and row.rating not in {"BUY_NOW", "STAGED_ENTRY"}:
            raise JuryValidationError(f"{row.ticker} has an invalid selected rating")
        plan = row.trade_plan
        if row.portfolio_status != "INSUFFICIENT_DATA":
            if not row.evidence_refs:
                raise JuryValidationError(f"{row.ticker} has no supporting evidence references")
            if not row.counter_evidence_refs:
                raise JuryValidationError(f"{row.ticker} has no counter-evidence references")
        if row.rating == "BUY_NOW" and plan.entry_mode != "IMMEDIATE":
            raise JuryValidationError(f"{row.ticker} BUY_NOW requires an immediate entry")
        if row.rating == "STAGED_ENTRY":
            if plan.entry_mode != "TRIGGERED" or plan.trigger_expiry_sessions is None:
                raise JuryValidationError(f"{row.ticker} staged entry requires a trigger and expiry")
        if row.rating in {"WATCH", "AVOID", "SELL"} and plan.entry_mode != "NONE":
            raise JuryValidationError(f"{row.ticker} non-actionable rating cannot have an entry plan")
        if plan.entry_mode == "NONE" and any(value is not None for value in (plan.entry_low, plan.entry_high, plan.stop_price)):
            raise JuryValidationError(f"{row.ticker} has prices without an entry plan")
        if plan.entry_low is not None and plan.entry_high is not None and plan.entry_low > plan.entry_high:
            raise JuryValidationError(f"{row.ticker} has an invalid entry range")
        if plan.stop_price is not None and plan.entry_low is not None and plan.stop_price >= plan.entry_low:
            raise JuryValidationError(f"{row.ticker} has a long stop above its entry")
        if plan.profit_targets:
            if plan.entry_high is not None and any(target <= plan.entry_high for target in plan.profit_targets):
                raise JuryValidationError(f"{row.ticker} has a target below its entry")
            if plan.profit_targets != sorted(plan.profit_targets):
                raise JuryValidationError(f"{row.ticker} profit targets must be ascending")
        if plan.entry_mode != "NONE" and plan.entry_low is None:
            raise JuryValidationError(f"{row.ticker} entry plan requires an entry price")

        cited_values = " ".join(str(ref) for ref in row.evidence_refs + row.counter_evidence_refs)
        text = " ".join([row.summary, *row.supporting_evidence, *row.counter_evidence, *row.catalysts, *row.key_risks])
        if _numbers(text) and not cited_values:
            raise JuryValidationError(f"{row.ticker} has numeric claims without evidence")

    return verdict
