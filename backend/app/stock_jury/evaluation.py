from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median


@dataclass(frozen=True)
class HistoricalCase:
    ticker: str
    rating: str
    confidence: float
    entry_price: float | None
    return_20d_pct: float | None
    return_40d_pct: float | None
    max_favorable_pct: float | None = None
    max_adverse_pct: float | None = None


def evaluate_cases(cases: list[HistoricalCase]) -> dict:
    """Calculate prompt-evaluation metrics from frozen, post-analysis outcomes."""
    actionable = [case for case in cases if case.rating in {"BUY_NOW", "STAGED_ENTRY"}]
    directional = [
        case for case in cases
        if case.return_40d_pct is not None and case.rating in {"BUY_NOW", "STAGED_ENTRY", "SELL"}
    ]
    correct = [
        case for case in directional
        if (case.rating in {"BUY_NOW", "STAGED_ENTRY"} and case.return_40d_pct > 0)
        or (case.rating == "SELL" and case.return_40d_pct < 0)
    ]
    returns = [case.return_40d_pct for case in actionable if case.return_40d_pct is not None]
    return {
        "case_count": len(cases),
        "actionable_count": len(actionable),
        "directional_accuracy_40d": len(correct) / len(directional) if directional else None,
        "actionable_mean_return_40d_pct": mean(returns) if returns else None,
        "actionable_median_return_40d_pct": median(returns) if returns else None,
        "max_adverse_mean_pct": mean([c.max_adverse_pct for c in cases if c.max_adverse_pct is not None]) if any(c.max_adverse_pct is not None for c in cases) else None,
    }
