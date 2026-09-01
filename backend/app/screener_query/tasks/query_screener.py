from __future__ import annotations

import logging
from typing import Any

from app.scraper.factory import ScraperFactory

logger = logging.getLogger(__name__)


class QueryScreenerTask:
    """Finds stocks matching a screener query/index name.

    Compatible with BaseWorkflowTask interface (name, run(ctx)).
    """

    name = "query_screener"

    def __init__(self, source: str = "screener") -> None:
        self.source = source

    def run(self, ctx: Any) -> None:
        query = ctx.get_input("query")
        if not query:
            raise ValueError("No query provided")

        logger.info("Running screener query: %s", query)

        index_scraper = ScraperFactory.get_index_scraper(self.source)
        result = index_scraper.get_stocks(query)

        if not result.success:
            raise Exception(result.error)

        stocks = result.data
        logger.info("Found %d stocks matching '%s'", len(stocks), query)

        ctx.set_output(self.name, {
            "query": query,
            "stocks": [s.model_dump(mode="json") for s in stocks],
        })
