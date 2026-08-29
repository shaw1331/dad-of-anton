from __future__ import annotations

BASE_URL = "https://www.screener.in"

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
REQUEST_DELAY = 1.5
RESULTS_PER_PAGE = 25

HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

COMPANY_DATA_POINTS: list[tuple[str, str, str]] = [
    ("Market Cap", "ratio", "Market Cap"),
    ("Current Price", "ratio", "Current Price"),
    ("High / Low", "ratio", "High / Low"),
    ("Stock P/E", "ratio", "Stock P/E"),
    ("Book Value", "ratio", "Book Value"),
    ("Dividend Yield", "ratio", "Dividend Yield"),
    ("ROCE", "ratio", "ROCE"),
    ("ROE", "ratio", "ROE"),
    ("Face Value", "ratio", "Face Value"),
    ("Sales (Latest Qtr)", "quarterly", "Sales"),
    ("Operating Profit (Latest Qtr)", "quarterly", "Operating Profit"),
    ("Net Profit (Latest Qtr)", "quarterly", "Net Profit"),
    ("Promoter Holding", "shareholding", "Promoter"),
    ("FII Holding", "shareholding", "FII"),
    ("DII Holding", "shareholding", "DII"),
    ("Public Holding", "shareholding", "Public"),
    ("Government Holding", "shareholding", "Government"),
    ("Others Holding", "shareholding", "Others"),
    ("Pros", "pros_cons", "pros"),
    ("Cons", "pros_cons", "cons"),
]
