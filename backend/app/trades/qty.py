from __future__ import annotations

import math

TRADE_NOTIONAL_INR = 8000


def suggested_quantity(ltp: float, notional: float = TRADE_NOTIONAL_INR) -> int:
    if ltp <= 0:
        raise ValueError("LTP must be positive")
    return max(1, math.floor(notional / ltp))


def suggested_stop(ltp: float) -> float:
    return round(ltp * 0.95, 2)


def suggested_take_profit(ltp: float) -> float:
    return round(ltp * 1.09, 2)
