from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from statistics import mean, median
from typing import Any

MIN_HISTORICAL_CASES = 100


@dataclass(frozen=True)
class HistoricalCase:
    ticker: str
    rating: str
    confidence: float
    entry_price: float | None
    return_20d_pct: float | None
    return_40d_pct: float | None
    case_id: str = ""
    analysis_date: str = "2000-01-01"
    candidate_set_id: str = ""
    prompt_version: str = ""
    model: str = ""
    provider: str = ""
    temperature: float | None = None
    schema_version: str = ""
    max_favorable_pct: float | None = None
    max_adverse_pct: float | None = None
    staged_filled: bool = False
    target_before_stop: bool | None = None
    stop_before_target: bool | None = None
    selected_rank: int | None = None
    top_three_return_40d_pct: float | None = None
    all_positive_return_40d_pct: float | None = None
    missed_upside_pct: float | None = None
    citation_failure: bool = False
    schema_failure: bool = False
    leakage_detected: bool = False
    agent_disagreement: bool = False

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "HistoricalCase":
        return cls(**value)


def load_cases(path: str | Path) -> list[HistoricalCase]:
    cases = [HistoricalCase.from_dict(item) for item in json.loads(Path(path).read_text(encoding="utf-8"))]
    validate_dataset(cases)
    return cases


def validate_dataset(cases: list[HistoricalCase], minimum: int = MIN_HISTORICAL_CASES) -> None:
    if len(cases) < minimum:
        raise ValueError(f"Historical evaluation needs at least {minimum} cases")
    seen: set[str] = set()
    for case in cases:
        if case.case_id in seen:
            raise ValueError(f"Duplicate historical case: {case.case_id}")
        seen.add(case.case_id)
        date.fromisoformat(case.analysis_date)
        if not 0 <= case.confidence <= 1:
            raise ValueError(f"Invalid confidence for {case.case_id}")
        if case.leakage_detected:
            raise ValueError(f"Future-data leakage in {case.case_id}")


def evaluate_cases(cases: list[HistoricalCase]) -> dict:
    """Calculate deterministic metrics from frozen, post-analysis outcomes."""
    actionable = [case for case in cases if case.rating in {"BUY_NOW", "STAGED_ENTRY"} and (case.rating != "STAGED_ENTRY" or case.staged_filled)]
    directional = [case for case in cases if case.return_40d_pct is not None and case.rating in {"BUY_NOW", "STAGED_ENTRY", "SELL"}]
    correct = [case for case in directional if _is_correct(case, 40)]
    returns = [case.return_40d_pct for case in actionable if case.return_40d_pct is not None]
    target_cases = [case for case in cases if case.target_before_stop is not None or case.stop_before_target is not None]
    bins = {"0-49": [], "50-74": [], "75-100": []}
    for case in directional:
        bins["0-49" if case.confidence < 0.5 else "50-74" if case.confidence < 0.75 else "75-100"].append(case)
    return {
        "case_count": len(cases),
        "actionable_count": len(actionable),
        "directional_accuracy_20d": _directional_accuracy(cases, 20),
        "directional_accuracy_40d": len(correct) / len(directional) if directional else None,
        "actionable_mean_return_20d_pct": _mean([case.return_20d_pct for case in actionable if case.return_20d_pct is not None]),
        "actionable_median_return_20d_pct": _median([case.return_20d_pct for case in actionable if case.return_20d_pct is not None]),
        "actionable_mean_return_40d_pct": mean(returns) if returns else None,
        "actionable_median_return_40d_pct": median(returns) if returns else None,
        "profitable_actionable_pct": _ratio([case for case in actionable if case.return_40d_pct is not None and case.return_40d_pct > 0], [case for case in actionable if case.return_40d_pct is not None]),
        "target_before_stop_rate": _ratio([case for case in target_cases if case.target_before_stop], target_cases),
        "stop_before_target_rate": _ratio([case for case in target_cases if case.stop_before_target], target_cases),
        "max_drawdown_pct": min((case.max_adverse_pct for case in cases if case.max_adverse_pct is not None), default=None),
        "max_adverse_mean_pct": _mean([case.max_adverse_pct for case in cases if case.max_adverse_pct is not None]),
        "top_three_portfolio_return_40d_pct": _mean([case.top_three_return_40d_pct for case in cases if case.top_three_return_40d_pct is not None]),
        "positive_universe_return_40d_pct": _mean([case.all_positive_return_40d_pct for case in cases if case.all_positive_return_40d_pct is not None]),
        "missed_upside_mean_pct": _mean([case.missed_upside_pct for case in cases if case.missed_upside_pct is not None]),
        "jury_rank_return_correlation": _rank_correlation(cases),
        "confidence_calibration": {bucket: _ratio([case for case in bucket_cases if _is_correct(case, 40)], bucket_cases) for bucket, bucket_cases in bins.items()},
        "citation_failure_rate": _ratio([case for case in cases if case.citation_failure], cases),
        "schema_failure_rate": _ratio([case for case in cases if case.schema_failure], cases),
        "agent_disagreement_rate": _ratio([case for case in cases if case.agent_disagreement], cases),
    }


def _is_correct(case: HistoricalCase, days: int) -> bool:
    result = getattr(case, f"return_{days}d_pct")
    return (case.rating in {"BUY_NOW", "STAGED_ENTRY"} and (result or 0) > 0) or (case.rating == "SELL" and (result or 0) < 0)


def _directional_accuracy(cases: list[HistoricalCase], days: int) -> float | None:
    values = [case for case in cases if getattr(case, f"return_{days}d_pct") is not None and case.rating in {"BUY_NOW", "STAGED_ENTRY", "SELL"}]
    return sum(_is_correct(case, days) for case in values) / len(values) if values else None


def _mean(values: list[float]) -> float | None:
    return mean(values) if values else None


def _median(values: list[float]) -> float | None:
    return median(values) if values else None


def _ratio(numerator: list[Any], denominator: list[Any]) -> float | None:
    return len(numerator) / len(denominator) if denominator else None


def _rank_correlation(cases: list[HistoricalCase]) -> float | None:
    ranked = [case for case in cases if case.selected_rank is not None and case.return_40d_pct is not None]
    if len(ranked) < 2:
        return None
    ordered = sorted(ranked, key=lambda case: case.return_40d_pct or 0, reverse=True)
    actual = {case.case_id or case.ticker: index for index, case in enumerate(ordered)}
    first = [case.selected_rank for case in ranked]
    second = [actual[case.case_id or case.ticker] for case in ranked]
    first_mean = mean(first)
    second_mean = mean(second)
    numerator = sum((left - first_mean) * (right - second_mean) for left, right in zip(first, second))
    denominator = (sum((left - first_mean) ** 2 for left in first) * sum((right - second_mean) ** 2 for right in second)) ** 0.5
    return numerator / denominator if denominator else None


def release_gate(candidate: dict[str, Any], approved: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "minimum_dataset": candidate.get("case_count", 0) >= MIN_HISTORICAL_CASES,
        "schema": candidate.get("schema_failure_rate", 1) == 0,
        "citations": candidate.get("citation_failure_rate", 1) == 0,
        "no_drawdown_regression": _not_worse(candidate.get("max_drawdown_pct"), approved.get("max_drawdown_pct")),
        "accuracy_no_regression": candidate.get("directional_accuracy_40d", 0) >= approved.get("directional_accuracy_40d", 0),
        "median_return_no_regression": candidate.get("actionable_median_return_40d_pct", float("-inf")) >= approved.get("actionable_median_return_40d_pct", float("-inf")),
    }
    return {"passed": all(checks.values()), "checks": checks}


def _not_worse(candidate: float | None, approved: float | None) -> bool:
    return candidate is None or approved is None or candidate >= approved


def serialize_cases(cases: list[HistoricalCase]) -> list[dict[str, Any]]:
    return [asdict(case) for case in cases]
