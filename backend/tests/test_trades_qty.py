from __future__ import annotations

import pytest

from app.trades.qty import suggested_quantity, suggested_stop, suggested_take_profit


class TestSuggestedQuantity:
    def test_1398(self) -> None:
        assert suggested_quantity(1398) == 5

    def test_8000(self) -> None:
        assert suggested_quantity(8000) == 1

    def test_8001(self) -> None:
        assert suggested_quantity(8001) == 1

    def test_16000(self) -> None:
        assert suggested_quantity(16000) == 1

    def test_1(self) -> None:
        assert suggested_quantity(1) == 8000

    def test_zero_raises(self) -> None:
        with pytest.raises(ValueError):
            suggested_quantity(0)

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError):
            suggested_quantity(-5)


class TestSuggestedStop:
    def test_1398(self) -> None:
        assert suggested_stop(1398.2) == round(1398.2 * 0.95, 2)


class TestSuggestedTakeProfit:
    def test_1398(self) -> None:
        assert suggested_take_profit(1398.2) == round(1398.2 * 1.09, 2)
