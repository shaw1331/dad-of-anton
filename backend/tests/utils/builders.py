"""Mock data builders for tests."""
from __future__ import annotations


def build_stock(name="Test Corp", ticker="TEST", bse="500001", sector="Finance") -> dict:
    return {"name": name, "ticker": ticker, "bse_code": bse, "sector": sector}
