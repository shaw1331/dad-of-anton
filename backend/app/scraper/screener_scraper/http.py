from __future__ import annotations

import logging
import time

import requests
from bs4 import BeautifulSoup

from app.scraper.screener_scraper.config import (
    HEADERS,
    MAX_RETRIES,
    REQUEST_DELAY,
    REQUEST_TIMEOUT,
)

logger = logging.getLogger(__name__)

session = requests.Session()
session.headers.update(HEADERS)


def get_page(url: str) -> BeautifulSoup | None:
    """Fetch a page and return BeautifulSoup object with exponential backoff."""
    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, timeout=REQUEST_TIMEOUT)
            if response.status_code == 429:
                wait = 30
                logger.warning("Rate limited (429) — waiting %ds", wait)
                time.sleep(wait)
                continue
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            wait = REQUEST_DELAY * (2**attempt)
            logger.warning(
                "Attempt %d failed: %s — retrying in %.1fs", attempt + 1, e, wait
            )
            if attempt < MAX_RETRIES - 1:
                time.sleep(wait)
    return None
