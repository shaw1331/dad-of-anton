from __future__ import annotations

import logging
import time

import requests
from bs4 import BeautifulSoup

from app.scraper.trendlyne_scraper.config import (
    MAX_RETRIES,
    REQUEST_DELAY,
    REQUEST_TIMEOUT,
)

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://trendlyne.com/",
}

session = requests.Session()
session.headers.update(HEADERS)


def get_json(url: str, params: dict | None = None) -> dict | list | None:
    """Fetch JSON from a URL with exponential backoff."""
    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            if response.status_code == 429:
                wait = 30
                logger.warning("Rate limited (429) — waiting %ds", wait)
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            wait = REQUEST_DELAY * (2**attempt)
            logger.warning(
                "Attempt %d failed: %s — retrying in %.1fs", attempt + 1, e, wait
            )
            if attempt < MAX_RETRIES - 1:
                time.sleep(wait)
    return None


def get_page(url: str) -> BeautifulSoup | None:
    """Fetch an HTML page and return a BeautifulSoup object."""
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
