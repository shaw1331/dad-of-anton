# Stock Analyser Workflow - Task Breakdown

## Epic: Stock Analyser Workflow

---

## Phase 1: Scraper Module (Foundation)

### TASK-001: Create `scraper/models.py` — Generic DTOs

**Description:**
Create `backend/app/scraper/models.py` with the generic return types and DTOs for the scraper module.

**Implementation:**
- `ScraperResult[T]` - Generic result wrapper (success, data, error, source)
- `IndexDTO` - Index information (name, slug, stocks)
- `StockSummaryDTO` - Stock summary (ticker, name, url)
- `StockDTO` - Full stock data (ratios, quarterly, shareholding, pros, cons)
- `TechnicalDataDTO` - Technical analysis data

**Acceptance Criteria:**
- [x] File created at `backend/app/scraper/models.py`
- [x] All DTOs use Pydantic BaseModel
- [x] `ScraperResult[T]` is Generic and type-safe
- [x] All DTOs have proper type hints

---

### TASK-002: Create `scraper/interfaces.py` — Abstract Base Classes

**Description:**
Create `backend/app/scraper/interfaces.py` with abstract base classes for scrapers.

**Implementation:**
- `IndexScraper(ABC)` - Abstract class for index scrapers
  - `get_stocks(index_name: str) -> ScraperResult[list[StockSummaryDTO]]`
- `StockScraper(ABC)` - Abstract class for stock scrapers
  - `get_technical_data(ticker: str) -> ScraperResult[StockDTO]`
  - `get_multiple(tickers: list[str]) -> ScraperResult[list[StockDTO]]`

**Acceptance Criteria:**
- [x] File created at `backend/app/scraper/interfaces.py`
- [x] Both classes are abstract (cannot be instantiated)
- [x] All methods have proper type hints
- [x] Methods raise `NotImplementedError` if not overridden

---

### TASK-003: Create `scraper/exceptions.py` — Custom Exceptions

**Description:**
Create `backend/app/scraper/exceptions.py` with custom exception classes.

**Implementation:**
- `ScraperError(Exception)` - Base scraper exception
- `RateLimitError(ScraperError)` - Rate limit exceeded
- `NotFoundError(ScraperError)` - Resource not found
- `ConfigError(ScraperError)` - Invalid configuration

**Acceptance Criteria:**
- [x] File created at `backend/app/scraper/exceptions.py`
- [x] All exceptions inherit from `ScraperError`
- [x] Exceptions have descriptive error messages

---

### TASK-004: Create `scraper/config.py` — Shared Configuration

**Description:**
Create `backend/app/scraper/config.py` with shared configuration.

**Implementation:**
- `REQUEST_TIMEOUT = 30`
- `MAX_RETRIES = 3`
- `REQUEST_DELAY = 1.5` (seconds between requests)

**Acceptance Criteria:**
- [x] File created at `backend/app/scraper/config.py`
- [x] Configuration values are constants
- [x] Values match screener_scraper/config.py where appropriate

---

### TASK-005: Create `scraper/factory.py` — ScraperFactory

**Description:**
Create `backend/app/scraper/factory.py` with the factory class.

**Implementation:**
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

**Acceptance Criteria:**
- [x] File created at `backend/app/scraper/factory.py`
- [x] Factory has class methods for registration and retrieval
- [x] Raises `ConfigError` if source not registered
- [x] Default source is "screener"

---

### TASK-006: Create `scraper/__init__.py` — Exports

**Description:**
Create `backend/app/scraper/__init__.py` with module exports.

**Implementation:**
- Export `ScraperFactory`
- Export all DTOs from `models.py`
- Export all exceptions from `exceptions.py`

**Acceptance Criteria:**
- [x] File created at `backend/app/scraper/__init__.py`
- [x] All public symbols are importable from `app.scraper`

---

## Phase 2: Screener.in Adapter

### TASK-007: Create `screener_scraper/config.py` — Source-Specific Config

**Description:**
Create `backend/app/scraper/screener_scraper/config.py` with Screener.in-specific configuration.

**Implementation:**
- `BASE_URL = "https://www.screener.in"`
- `INDEXES = { "SMALLCAP50": "SMALLCAP50", "LMIDCAP250": "LMIDCAP250", "NIF500MO50": "NIF500MO50" }`
- `HEADERS` - User-Agent and other request headers
- `COMPANY_DATA_POINTS` - Data points to scrape (from screener_scraper/config.py)

**Acceptance Criteria:**
- [x] File created at `backend/app/scraper/screener_scraper/config.py`
- [x] Config matches existing `screener_scraper/config.py`
- [x] All required constants are defined

---

### TASK-008: Create `screener_scraper/http.py` — Session Management

**Description:**
Create `backend/app/scraper/screener_scraper/http.py` with HTTP session management.

**Implementation:**
- Import `requests.Session` with headers
- `get_page(url: str) -> BeautifulSoup | None` - Fetch page with retries
- Handle rate limiting (429 status)
- Exponential backoff on failures

**Acceptance Criteria:**
- [x] File created at `backend/app/scraper/screener_scraper/http.py`
- [x] Session reuses TCP connections
- [x] Handles rate limiting gracefully
- [x] Implements exponential backoff

---

### TASK-009: Create `screener_scraper/mappers.py` — HTML → DTO Parsing

**Description:**
Create `backend/app/scraper/screener_scraper/mappers.py` with parsing logic extracted from `scrape_companies.py`.

**Implementation:**
- `map_ratios(soup: BeautifulSoup) -> dict[str, str]` - Extract from #top-ratios
- `map_quarterly(soup: BeautifulSoup) -> dict[str, str]` - Extract from #quarters
- `map_shareholding(soup: BeautifulSoup) -> dict[str, str]` - Extract from #shareholding
- `map_pros_cons(soup: BeautifulSoup) -> tuple[list[str], list[str]]` - Extract from #analysis
- `map_company_page(soup: BeautifulSoup, ticker: str) -> StockDTO` - Map all data

**Acceptance Criteria:**
- [x] File created at `backend/app/scraper/screener_scraper/mappers.py`
- [x] Mappers handle missing data gracefully
- [x] Returns empty strings/dicts for missing values
- [x] All mappers have proper type hints

---

### TASK-010: Create `screener_scraper/index_scraper.py` — IndexScraper Adapter

**Description:**
Create `backend/app/scraper/screener_scraper/index_scraper.py` implementing the IndexScraper interface.

**Implementation:**
```python
class ScreenerIndexScraper(IndexScraper):
    def __init__(self, config: ScreenerConfig | None = None):
        self.config = config or ScreenerConfig()
    
    def get_stocks(self, index_name: str) -> ScraperResult[list[StockSummaryDTO]]:
        # Scrape index page
        # Extract companies from HTML
        # Map to StockSummaryDTO
        # Return ScraperResult with list of stocks
```

**Acceptance Criteria:**
- [x] File created at `backend/app/scraper/screener_scraper/index_scraper.py`
- [x] Implements `IndexScraper` interface
- [x] Handles pagination (if multiple pages)
- [x] Returns `ScraperResult` with success/error status

---

### TASK-011: Create `screener_scraper/stock_scraper.py` — StockScraper Adapter

**Description:**
Create `backend/app/scraper/screener_scraper/stock_scraper.py` implementing the StockScraper interface.

**Implementation:**
```python
class ScreenerStockScraper(StockScraper):
    def __init__(self, config: ScreenerConfig | None = None):
        self.config = config or ScreenerConfig()
    
    def get_technical_data(self, ticker: str) -> ScraperResult[StockDTO]:
        # Scrape company page
        # Map to StockDTO using mappers
        # Return ScraperResult with StockDTO
    
    def get_multiple(self, tickers: list[str]) -> ScraperResult[list[StockDTO]]:
        # Iterate through tickers
        # Call get_technical_data for each
        # Handle individual failures gracefully
        # Return ScraperResult with list of StockDTOs
```

**Acceptance Criteria:**
- [x] File created at `backend/app/scraper/screener_scraper/stock_scraper.py`
- [x] Implements `StockScraper` interface
- [x] `get_multiple` handles individual stock failures
- [x] Respects rate limiting between requests
- [x] Returns `ScraperResult` with success/error status

---

### TASK-012: Create `screener_scraper/__init__.py` — Auto-Register Adapters

**Description:**
Create `backend/app/scraper/screener_scraper/__init__.py` with auto-registration.

**Implementation:**
- Import `ScraperFactory`
- Import `ScreenerIndexScraper`
- Import `ScreenerStockScraper`
- Auto-register adapters on import:
  ```python
  ScraperFactory.register_index_scraper("screener", ScreenerIndexScraper)
  ScraperFactory.register_stock_scraper("screener", ScreenerStockScraper)
  ```

**Acceptance Criteria:**
- [x] File created at `backend/app/scraper/screener_scraper/__init__.py`
- [x] Adapters are registered when module is imported
- [x] No duplicate registrations

---

## Phase 3: Stock Analyser Workflow

### TASK-013: Update `stock_analyser/tasks/scrape_stocks.py` — Integrate ScraperFactory

**Description:**
Update `backend/app/stock_analyser/tasks/scrape_stocks.py` to use the ScraperFactory.

**Implementation:**
- Import `ScraperFactory`
- Update `ScrapeStocksTask.run()`:
  1. Get index from `ctx.get_input("index")`
  2. Get `IndexScraper` from `ScraperFactory.get_index_scraper("screener")`
  3. Call `get_stocks(index)` to get list of stocks
  4. Get `StockScraper` from `ScraperFactory.get_stock_scraper("screener")`
  5. Call `get_multiple(tickers)` to get technical data
  6. Store results in `ctx.set_output()`

**Acceptance Criteria:**
- [x] File updated at `backend/app/stock_analyser/tasks/scrape_stocks.py`
- [x] Uses `ScraperFactory` to get scrapers
- [x] Handles `ScraperResult.success` / error cases
- [x] Stores stocks in context for next task

---

### TASK-014: Update `stock_analyser/workflow.py` — Fix Workflow Config

**Description:**
Update `backend/app/stock_analyser/workflow.py` to fix workflow registration.

**Implementation:**
- Import `ScrapeStocksTask` from tasks module
- Define `STOCK_ANALYSER_WORKFLOW` with proper `InputField`
- Register in `WORKFLOWS["stock_analyser"]`

**Acceptance Criteria:**
- [x] File updated at `backend/app/stock_analyser/workflow.py`
- [x] Workflow has proper `name`, `description`, `input_fields`
- [x] Tasks list includes `ScrapeStocksTask`
- [x] Registered in `WORKFLOWS`

---

### TASK-015: Update `workflow/workflow_orchestrator_v1/__init__.py` — Register Stock Analyser

**Description:**
Update `backend/app/workflow/workflow_orchestrator_v1/__init__.py` to import stock_analyser module.

**Implementation:**
- Add import: `import app.stock_analyser.workflow  # noqa: F401`

**Acceptance Criteria:**
- [x] File updated at `backend/app/workflow/workflow_orchestrator_v1/__init__.py`
- [x] Stock analyser workflow is registered on app startup
- [x] Workflow appears in `GET /workflows` endpoint

---

## Phase 4: Dependencies

### TASK-016: Update `backend/requirements.txt` — Add Dependencies

**Description:**
Update `backend/requirements.txt` with new dependencies.

**Implementation:**
Add:
```
beautifulsoup4>=4.12.0
requests>=2.31.0
lxml>=4.9.0
```

**Acceptance Criteria:**
- [x] File updated at `backend/requirements.txt`
- [x] All dependencies are added with version constraints
- [x] Run `pip install -r requirements.txt` to install

---

## Phase 5: Testing

### TASK-017: Manual Test — Trigger Workflow via API

**Description:**
Manually test the full workflow by triggering via API.

**Steps:**
1. Start backend server: `uvicorn app.main:app --reload`
2. Trigger workflow: `POST /api/v1/workflows/stock_analyser/trigger` with `{"index": "SMALLCAP50"}`
3. Verify workflow starts and shows in runs list
4. Wait for completion (expect ~75s for 50 stocks)
5. Check database for scraped data

**Acceptance Criteria:**
- [ ] Workflow can be triggered via API
- [ ] Workflow appears in runs list with status
- [ ] Stocks are scraped and stored in database
- [ ] Frontend shows workflow results

---

### TASK-018: Verify Frontend Displays Results

**Description:**
Verify that the frontend displays workflow results correctly.

**Steps:**
1. Start frontend dev server: `npm run dev`
2. Navigate to `/workflows`
3. Find stock_analyser workflow
4. Click to view run details
5. Verify stocks are displayed

**Acceptance Criteria:**
- [ ] Frontend shows stock_analyser workflow
- [ ] Run details show task progress
- [ ] Scraped stocks are displayed in UI

---

## Task Dependencies

```
TASK-001 → TASK-002 → TASK-005 → TASK-006
                    ↘
TASK-003           TASK-007 → TASK-008 → TASK-009 → TASK-010
                    ↘                                    ↘
TASK-004 → TASK-005 → TASK-012 → TASK-013 → TASK-014 → TASK-015
                                                          ↓
                                              TASK-016 → TASK-017 → TASK-018
```

---

## Estimated Time

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1: Scraper Module | 6 tasks | 2-3 hours |
| Phase 2: Screener.in Adapter | 6 tasks | 3-4 hours |
| Phase 3: Stock Analyser Workflow | 3 tasks | 1-2 hours |
| Phase 4: Dependencies | 1 task | 15 mins |
| Phase 5: Testing | 2 tasks | 1-2 hours |
| **Total** | **18 tasks** | **8-12 hours** |

---

## Notes

- **Scraping is slow**: Screener.in rate limits (1.5s delay). Expect ~75s for 50 stocks.
- **Resumability**: Consider adding resume capability for interrupted scrapes.
- **Error handling**: Individual stock failures should not fail entire workflow.
- **Caching**: Consider caching scraped data for re-analysis without re-scraping.