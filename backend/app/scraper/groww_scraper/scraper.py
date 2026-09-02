from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from app.scraper.groww_scraper.config import (
    NEWS_LOOKBACK_DAYS,
    NEWS_PAGE_SIZE,
    NEWS_URL,
    SEARCH_URL,
)
from app.scraper.groww_scraper.http import get_json
from app.scraper.groww_scraper.models import NewsArticle
from app.scraper.models import ScraperResult

logger = logging.getLogger(__name__)


class GrowwNewsScraper:
    """Scrapes stock news from Groww's API."""

    def search_ticker(self, ticker: str) -> tuple[str, str] | None:
        """Search Groww for a ticker and return (groww_contract_id, company_name).

        Filters results to Stocks entity type only.
        Returns None if no match found.
        """
        params = {
            "from": 0,
            "is_us_stocks": 0,
            "query": ticker,
            "size": 6,
            "web": "true",
        }
        data = get_json(SEARCH_URL, params=params)
        if not data:
            return None

        content = data.get("data", {}).get("content", [])
        for item in content:
            if item.get("entity_type") == "Stocks":
                contract_id = item.get("groww_contract_id")
                company_name = item.get("title", "")
                if contract_id:
                    return contract_id, company_name
        return None

    def get_news(
        self, ticker: str, lookback_days: int = NEWS_LOOKBACK_DAYS
    ) -> ScraperResult[list[NewsArticle]]:
        """Fetch news articles for a given stock ticker from Groww.

        Returns articles from the last `lookback_days` days.
        """
        result = self.search_ticker(ticker)
        if not result:
            return ScraperResult(
                success=False,
                error=f"No Groww stock found for ticker '{ticker}'",
                source="groww",
            )

        groww_contract_id, company_name = result
        logger.info(
            "Found groww_contract_id=%s for ticker=%s", groww_contract_id, ticker
        )

        news_url = f"{NEWS_URL}/{groww_contract_id}"
        params = {"page": 0, "size": NEWS_PAGE_SIZE}
        data = get_json(news_url, params=params)
        if not data:
            return ScraperResult(
                success=False,
                error=f"Failed to fetch news for ticker '{ticker}'",
                source="groww",
            )

        raw_articles = data.get("results", [])
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)

        articles: list[NewsArticle] = []
        for item in raw_articles:
            pub_date_str = item.get("pubDate", "")
            try:
                pub_date = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
            except (ValueError, AttributeError):
                continue

            if pub_date < cutoff:
                continue

            articles.append(
                NewsArticle(
                    id=item.get("id", ""),
                    summary=item.get("summary", ""),
                    url=item.get("url", ""),
                    image_url=item.get("imageUrl"),
                    pub_date=pub_date,
                    source=item.get("source", ""),
                )
            )

        articles.sort(key=lambda a: a.pub_date, reverse=True)

        return ScraperResult(
            success=True,
            data=articles,
            source="groww",
        )
