from __future__ import annotations

from abc import ABC, abstractmethod


class BaseScreener(ABC):
    """Interface for NSE stock screeners.

    Each screener scans the full NSE universe and returns
    stocks matching its criteria.
    """

    name: str
    description: str

    @abstractmethod
    def run(self) -> list[dict]:
        """Run the screener and return matching stocks.

        Returns:
            List of dicts, each representing a stock row.
            Keys become table columns on the frontend.
        """
        ...
