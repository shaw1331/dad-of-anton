from __future__ import annotations

from app.stock_jury.models import JuryVerdict


class JuryValidationError(ValueError):
    pass


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
        if plan.entry_low is not None and plan.entry_high is not None and plan.entry_low > plan.entry_high:
            raise JuryValidationError(f"{row.ticker} has an invalid entry range")
        if plan.stop_price is not None and plan.entry_low is not None and plan.stop_price >= plan.entry_low:
            raise JuryValidationError(f"{row.ticker} has a long stop above its entry")

    return verdict
