# Stock Analyser Workflow - Implementation Plan

## Overview

Build a workflow to analyze a stock INDEX by:
1. Scraping all stocks in the INDEX
2. Scraping technical analysis for each stock
3. Storing the scraped data in the database
4. Analyzing the stocks and generating recommendations

## Architecture

### Module Structure

```
backend/app/
├── stock_analyser/                 # Domain module
│   ├── __init__.py                 # Exports WORKFLOWS
│   ├── workflow.py                 # Workflow definition + registry
│   └── tasks/                      # Individual workflow tasks
│       ├── __init__.py             # Task exports
│       └── scrape_stocks.py        # ScrapeStocksTask (fetches all stock data)
│
├── scraper/                        # Scraper module (adapter/factory pattern)
│   ├── __init__.py                 # Exports ScraperFactory, auto-registers adapters
│   ├── models.py                   # Generic DTOs (ScraperResult[T], StockDTO, etc.)
│   ├── interfaces.py               # Abstract base classes (IndexScraper, StockScraper)
│   ├── factory.py                  # ScraperFactory
│   ├── config.py                   # Shared config (timeouts, retries)
│   ├── exceptions.py               # Custom exceptions (ScraperError, NotFoundError)
│   └── screener_scraper/           # Screener.in adapter (source-specific)
│       ├── __init__.py             # Auto-registers adapters on import
│       ├── config.py               # Screener-specific config (BASE_URL, INDEXES)
│       ├── http.py                 # Session management (from screener_scraper/utils.py)
│       ├── mappers.py              # HTML → DTO parsing (from scrape_companies.py)
│       ├── index_scraper.py        # ScreenerIndexScraper
│       └── stock_scraper.py        # ScreenerStockScraper
│
└── workflow/                       # Workflow engine (existing)
    ├── __init__.py
    ├── base_workflow_config.py     # BaseWorkflowConfig, InputField
    ├── base_workflow_task.py       # BaseWorkflowTask ABC
    ├── base_workflow_context.py    # BaseWorkflowContext
    └── workflow_orchestrator_v1/   # Orchestrator + registry
```

---

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Scraper pattern | Adapter + Factory | Supports multiple data sources (screener.in, Yahoo Finance, etc.) |
| Return type | Generic `ScraperResult[T]` | Type-safe results with error handling |
| Sync vs Async | Sync | Workflow runs in thread pool; keep simplicity |
| Source selection | Parameter in WorkflowTask | Flexible, configurable per workflow run |
| Rate limiting | Built-in to adapter | Respects screener.in limits (1.5s delay) |
| Data storage | PostgreSQL via Supabase | Already used in workflow engine |

---

## Core Types

### `scraper/models.py`

```python
from typing import Generic, TypeVar
from datetime import datetime

T = TypeVar("T")

class ScraperResult(Generic[T]):
    success: bool
    data: T | None
    error: str | None
    source: str  # "screener", "yahoo", etc.

class IndexDTO:
    name: str
    slug: str
    stocks: list[StockSummaryDTO]

class StockSummaryDTO:
    ticker: str
    name: str
    url: str

class StockDTO:
    ticker: str
    name: str
    sector: str | None
    industry: str | None
    ratios: dict[str, str]      # Market Cap, P/E, ROE, etc.
    quarterly: dict[str, str]   # Latest quarter values
    shareholding: dict[str, str]
    pros: list[str]
    cons: list[str]
    scraped_at: datetime
```

### `scraper/interfaces.py`

```python
from abc import ABC, abstractmethod
from app.scraper.models import ScraperResult, StockSummaryDTO, StockDTO

class IndexScraper(ABC):
    @abstractmethod
    def get_stocks(self, index_name: str) -> ScraperResult[list[StockSummaryDTO]]: ...

class StockScraper(ABC):
    @abstractmethod
    def get_technical_data(self, ticker: str) -> ScraperResult[StockDTO]: ...
    
    @abstractmethod
    def get_multiple(self, tickers: list[str]) -> ScraperResult[list[StockDTO]]: ...
```

### `scraper/factory.py`

```python
class ScraperFactory:
    _index_scrapers: dict[str, type[IndexScraper]] = {}
    _stock_scrapers: dict[str, type[StockScraper]] = {}

    @classmethod
    def register_index_scraper(cls, source: str, scraper_cls: type[IndexScraper]) -> None: ...
    
    @classmethod
    def register_stock_scraper(cls, source: str, scraper_cls: type[StockScraper]) -> None: ...

    @classmethod
    def get_index_scraper(cls, source: str = "screener") -> IndexScraper: ...
    
    @classmethod
    def get_stock_scraper(cls, source: str = "screener") -> StockScraper: ...
```

---

## Workflow Flow

```
User Input: INDEX (e.g., "NIFTY50")
        │
        ▼
┌─────────────────────────┐
│ ScrapeStocksTask        │
│ - index: str            │
│ - source: str           │  ← from WorkflowTask config
└─────────────────────────┘
        │
        ├──► ScraperFactory.get_index_scraper(source)
        │         │
        │         ▼
        │    IndexScraper.get_stocks(index)
        │         │
        │         ▼
        │    list[StockSummaryDTO]  (ticker, name, url)
        │
        ├──► ScraperFactory.get_stock_scraper(source)
        │         │
        │         ▼
        │    StockScraper.get_multiple(tickers)
        │         │
        │         ▼
        │    list[StockDTO]  (full stock data)
        │
        └──► ctx.set_output("stocks", stocks_data)
                    │
                    ▼
        Next task receives stocks via ctx.get_output("stocks")
```

---

## Screener.in Adapter

### `screener_scraper/index_scraper.py`

Wraps `screener_scraper/scrape_indexes.py`:
```python
class ScreenerIndexScraper(IndexScraper):
    def get_stocks(self, index_name: str) -> ScraperResult[list[StockSummaryDTO]]:
        # Calls scrape_index() → maps to StockSummaryDTO
```

### `screener_scraper/stock_scraper.py`

Wraps `screener_scraper/scrape_companies.py`:
```python
class ScreenerStockScraper(StockScraper):
    def get_technical_data(self, ticker: str) -> ScraperResult[StockDTO]:
        # Calls scrape_company() → maps to StockDTO via mappers
```

### `screener_scraper/mappers.py`

Extracted from `scrape_companies.py`:
- `map_ratios(soup) -> dict`
- `map_quarterly(soup) -> dict`
- `map_shareholding(soup) -> dict`
- `map_pros_cons(soup) -> tuple[list, list]`
- `map_company_page(soup, ticker) -> StockDTO`

### `screener_scraper/config.py`

```python
BASE_URL = "https://www.screener.in"
INDEXES = {
    "SMALLCAP50": "SMALLCAP50",
    "LMIDCAP250": "LMIDCAP250",
    "NIF500MO50": "NIF500MO50",
}
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
```

### `screener_scraper/http.py`

Session management (from `utils.py`):
```python
session = requests.Session()
session.headers.update(HEADERS)

def get_page(url: str) -> BeautifulSoup | None: ...
```

---

## Dependencies

Add to `backend/requirements.txt`:
```
beautifulsoup4>=4.12.0
requests>=2.31.0
lxml>=4.9.0
```

---

## Integration with Workflow

### `stock_analyser/workflow.py`

```python
from app.stock_analyser.tasks.scrape_stocks import ScrapeStocksTask
from app.workflow.base_workflow_config import BaseWorkflowConfig, InputField
from app.workflow.workflow_orchestrator_v1.workflow_registry import WORKFLOWS

STOCK_ANALYSER_WORKFLOW = BaseWorkflowConfig(
    name="stock_analyser",
    description="Scrapes stocks and technical analysis for a given index",
    input_fields=[
        InputField(
            name="index",
            type="str",
            label="Stock Index",
            description="The stock index to analyze (e.g. NIFTY50, SENSEX)",
            required=True,
        ),
    ],
    tasks=[ScrapeStocksTask],
)

WORKFLOWS["stock_analyser"] = STOCK_ANALYSER_WORKFLOW
```

### `stock_analyser/tasks/scrape_stocks.py`

```python
from app.scraper.factory import ScraperFactory
from app.workflow.base_workflow_task import BaseWorkflowTask

class ScrapeStocksTask(BaseWorkflowTask):
    name = "scrape_stocks"

    def run(self, ctx: BaseWorkflowContext) -> None:
        index = ctx.get_input("index")
        
        # Get index scraper
        index_scraper = ScraperFactory.get_index_scraper("screener")
        stocks_result = index_scraper.get_stocks(index)
        
        if not stocks_result.success:
            raise Exception(stocks_result.error)
        
        # Get stock scraper
        stock_scraper = ScraperFactory.get_stock_scraper("screener")
        tickers = [s.ticker for s in stocks_result.data]
        technical_result = stock_scraper.get_multiple(tickers)
        
        if not technical_result.success:
            raise Exception(technical_result.error)
        
        ctx.set_output(self.name, {
            "index": index,
            "stocks": technical_result.data,
        })
```

---

## Implementation Order

### Phase 1: Scraper Module (Foundation)
1. Create `scraper/models.py` - DTOs
2. Create `scraper/interfaces.py` - Abstract base classes
3. Create `scraper/exceptions.py` - Custom exceptions
4. Create `scraper/config.py` - Shared config
5. Create `scraper/factory.py` - ScraperFactory
6. Create `scraper/__init__.py` - Exports

### Phase 2: Screener.in Adapter
7. Create `screener_scraper/config.py` - Source-specific config
8. Create `screener_scraper/http.py` - Session management
9. Create `screener_scraper/mappers.py` - HTML → DTO parsing
10. Create `screener_scraper/index_scraper.py` - IndexScraper adapter
11. Create `screener_scraper/stock_scraper.py` - StockScraper adapter
12. Create `screener_scraper/__init__.py` - Auto-register adapters

### Phase 3: Stock Analyser Workflow
13. Update `stock_analyser/tasks/scrape_stocks.py` - Integrate with ScraperFactory
14. Update `stock_analyser/workflow.py` - Fix workflow config
15. Update `workflow/workflow_orchestrator_v1/__init__.py` - Register stock_analyser

### Phase 4: News Analysis Feature
16. See [news-analysis-plan.md](./news-analysis-plan.md) and [news-analysis-tasks.md](./news-analysis-tasks.md)
    - Add `NewsImpact` enum + `AnalyzedNewsArticle` model
    - Create `NewsAnalysisAgent` LangGraph (trafilatura + LLM)
    - Create `ScrapeNewsTask` + `AnalyzeNewsTask`
    - Add `enable_news` toggle to workflow

### Phase 5: Testing & Integration
17. Manual test: Trigger workflow via API
18. Verify database storage
19. Verify frontend displays results

---

## Database Schema

### `scraped_stocks` table

| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid (PK) | Auto-generated |
| `ticker` | text | Stock ticker (e.g., "RELIANCE") |
| `name` | text | Company name |
| `index_name` | text | Source index (e.g., "NIFTY50") |
| `sector` | text | Sector (optional) |
| `industry` | text | Industry (optional) |
| `ratios` | jsonb | Market Cap, P/E, ROE, etc. |
| `quarterly` | jsonb | Latest quarter values |
| `shareholding` | jsonb | Promoter, FII, DII, etc. |
| `pros` | jsonb | List of pros |
| `cons` | jsonb | List of cons |
| `source` | text | Data source (e.g., "screener") |
| `workflow_run_id` | uuid (FK) | References workflow_runs.id |
| `scraped_at` | timestamptz | When scraped |
| `created_at` | timestamptz | Auto |

### `stock_analyser_recommendations` table

| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid (PK) | Auto-generated |
| `scraped_stock_id` | uuid (FK) | References scraped_stocks.id |
| `recommendation` | text | BUY, SELL, HOLD |
| `confidence` | float | 0.0 - 1.0 |
| `reasoning` | text | Analysis reasoning |
| `analyzed_at` | timestamptz | When analyzed |
| `created_at` | timestamptz | Auto |

---

## Sample Workflow Run

```
Input: { "index": "NIFTY50", "enable_news": true }

Task 1: ScrapeStocksTask
  - IndexScraper.get_stocks("NIFTY50") → 50 stocks
  - StockScraper.get_multiple(tickers) → 50 StockDTOs
  - Output: { "index": "NIFTY50", "stocks": [StockDTO, ...] }

Task 2: ScrapeNewsTask (new)
  - GrowwNewsScraper.get_news(ticker, lookback_days) per stock
  - Output: { "news": { "RELIANCE": [...], ... }, "total_articles": 187 }

Task 3: AnalyzeNewsTask (new)
  - NewsAnalysisAgent per ticker (trafilatura + LLM)
  - Output: { "analyses": { "RELIANCE": [...], ... }, "total_analyzed": 187 }

Task 4: AnalyzeStocksTask
  - Reads stocks from ctx.get_output("scrape_stocks")
  - Generates recommendations
  - Stores in stock_analyser_recommendations
```

---

## Notes

- **Scraping is slow**: Screener.in rate limits (1.5s delay). Expect ~75s for 50 stocks.
- **Resumability**: Should support resuming interrupted scrapes (skip already-scraped tickers).
- **Error handling**: Individual stock failures should not fail entire workflow.
- **Caching**: Consider caching scraped data for re-analysis without re-scraping.