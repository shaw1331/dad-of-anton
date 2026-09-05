# TASK-030: Trendlyne Scraper — Technical Indicators

## Overview

Build a Trendlyne scraper that provides the technical indicator data missing from Screener.in:
EMA/SMA, RSI, MACD, ADX, ATR, Support/Resistance, Price Returns, Volume, Beta.

Two data sources on Trendlyne:
1. **Search API** — `https://trendlyne.com/member/api/ac_snames/all/?term={ticker}&all-results=true` — resolves ticker → stock_id
2. **Technical Data** — `https://trendlyne.com/equity/second-part-lazy-load-v2/{stock_id}/` — HTML with all indicators

## Architecture

```
backend/app/scraper/trendlyne_scraper/
├── __init__.py           # Auto-register with ScraperFactory
├── config.py             # BASE_URL, HEADERS, constants
├── http.py               # HTTP client with retry/backoff
├── models.py             # TrendlyneStockData Pydantic model
├── mappers.py            # BeautifulSoup HTML parsing → StockDTO
└── stock_scraper.py      # TrendlyneStockScraper(StockScraper)
```

## Data Flow

```
ticker → Search API → stock_id
                    ↓
stock_id → second-part-lazy-load-v2 → HTML
                    ↓
HTML → BeautifulSoup parsing → TrendlyneStockData
                    ↓
TrendlyneStockData.model_dump() → StockDTO.data
```

## Confirmed URL Structure

| Stock | Stock ID | Ticker | Slug | Main Page URL | Technical Analysis URL |
|---|---|---|---|---|---|
| HDFC Bank | 533 | HDFCBANK | hdfc-bank-ltd | `https://trendlyne.com/equity/533/HDFCBANK/hdfc-bank-ltd/` | `https://trendlyne.com/equity/technical-analysis/HDFCBANK/533/hdfc-bank-ltd/` |
| ITC | 647 | ITC | itc-ltd | `https://trendlyne.com/equity/647/ITC/itc-ltd/` | `https://trendlyne.com/equity/technical-analysis/ITC/647/itc-ltd/` |

## Extracted Data Points

### From `second-part-lazy-load-v2` HTML:

| Section | Fields |
|---|---|
| **EMA** | ema_5, ema_10, ema_12, ema_20, ema_26, ema_50, ema_100, ema_200 |
| **SMA** | sma_5, sma_10, sma_20, sma_30, sma_50, sma_100, sma_150, sma_200 |
| **Momentum** | rsi, macd, macd_signal, adx, atr, mfi, cci, roc_21, roc_125, williams_r |
| **Support/Resistance** | pivot, r1, r2, r3, s1, s2, s3 |
| **Returns** | return_1m, return_3m, return_6m, return_1y |
| **Volume** | vol_day, vol_week, vol_month |
| **Beta** | beta_1m, beta_3m, beta_1y, beta_3y |

## Implementation Steps

### TASK-030-01: Create `trendlyne_scraper/config.py`
- [ ] `BASE_URL = "https://trendlyne.com"`
- [ ] `SEARCH_API = "/member/api/ac_snames/all/"`
- [ ] `TECHNICAL_API = "/equity/second-part-lazy-load-v2/{stock_id}/"`
- [ ] Headers with User-Agent, Accept, etc.
- [ ] `REQUEST_TIMEOUT = 30`, `MAX_RETRIES = 3`, `REQUEST_DELAY = 1.5`

### TASK-030-02: Create `trendlyne_scraper/http.py`
- [ ] `get_json(url)` — fetch JSON from search API
- [ ] `get_page(url)` — fetch HTML from technical endpoint
- [ ] Retry with exponential backoff (same pattern as screener_scraper)
- [ ] Rate limit handling (429 → 30s wait)

### TASK-030-03: Create `trendlyne_scraper/models.py`
- [ ] `TrendlyneStockData` Pydantic model with all technical fields
- [ ] Optional fields (not all stocks have all indicators)

### TASK-030-04: Create `trendlyne_scraper/mappers.py`
- [ ] `map_search_result(json_data) -> str` — extract stock_id from search API response
- [ ] `map_technicals(html, ticker, url) -> StockDTO` — parse HTML and build StockDTO
- [ ] Parse EMA/SMA sections (look for "EMA & SMA" heading, then extract values)
- [ ] Parse RSI, MACD, ADX, ATR sections (look for "Day RSI", "Day MACD", etc.)
- [ ] Parse Support/Resistance (look for "PIVOT", "First Resistance", etc.)
- [ ] Parse Returns (look for "Over 1 Month", "Over 3 Months", etc.)
- [ ] Parse Volume (look for "vol_day" or volume-related elements)
- [ ] Parse Beta (look for "1 Month", "1 Year" under Beta section)

### TASK-030-05: Create `trendlyne_scraper/stock_scraper.py`
- [ ] `TrendlyneStockScraper(StockScraper)` class
- [ ] `get_technical_data(ticker)` — search → get stock_id → fetch technicals → parse
- [ ] `get_multiple(tickers)` — iterate with REQUEST_DELAY between requests
- [ ] Handle missing data gracefully (return "N/A" or None)

### TASK-030-06: Create `trendlyne_scraper/__init__.py`
- [ ] Auto-register with ScraperFactory:
  ```python
  ScraperFactory.register_stock_scraper("trendlyne", TrendlyneStockScraper)
  ```

### TASK-030-07: Register in orchestrator
- [ ] Add `import app.scraper.trendlyne_scraper` to `backend/app/workflow/workflow_orchestrator_v1/__init__.py`

### TASK-030-08: Update ScrapeStocksTask (optional)
- [ ] Make `source` configurable via workflow input (currently hardcoded to `"screener"`)
- [ ] Or create a new `ScrapeTechnicalDataTask` that runs after `ScrapeStocksTask`

### TASK-030-09: Update MomentumFormatter
- [ ] Add technical data fields to `momentum_prompt.md` template
- [ ] Map TrendlyneStockData fields to template placeholders

## HTML Parsing Strategy

The Trendlyne HTML is structured with clear section headers. Key patterns:

### EMA Section
```html
<div>HDFC Bank EMA & SMA</div>
<!-- EMA values in table-like structure -->
<div>5 Day</div><div>710.2</div>  <!-- EMA -->
<div>20 Day</div><div>722.3</div> <!-- EMA -->
<div>50 Day</div><div>743.4</div> <!-- EMA -->
<div>200 Day</div><div>817.3</div> <!-- EMA -->
<!-- SMA values in similar structure -->
<div>5 Day</div><div>708.1</div>  <!-- SMA -->
```

### RSI/MACD Section
```html
<div>Day RSI</div><div>39.8</div>
<div>Day MACD</div><div>-11.7</div>
<div>Day MACD Signal Line</div><div>-11.9</div>
<div>Day ADX</div><div>27.3</div>
<div>Day ATR</div><div>12.3</div>
```

### Support/Resistance
```html
<div>712.32</div><div>PIVOT</div>
<div>First Resistance</div><div>716.3</div>
<div>Second Resistance</div><div>720.5</div>
<div>Third Resistance</div><div>724.4</div>
<div>First Support</div><div>708.1</div>
<div>Second Support</div><div>704.2</div>
<div>Third Support</div><div>700.0</div>
```

### Returns
```html
<div>-4.0%</div><div>Over 1 Month</div>
<div>-5.6%</div><div>Over 3 Months</div>
<div>-18.0%</div><div>Over 6 Months</div>
<div>-25.9%</div><div>Over 1 Year</div>
```

## Acceptance Criteria

- `TrendlyneStockScraper.get_technical_data("HDFCBANK")` returns a `StockDTO` with all technical fields populated
- `get_multiple(["HDFCBANK", "ITC", "RELIANCE"])` works with rate limiting
- Missing data fields return `None` or `"N/A"` (no crashes)
- The scraper registers with `ScraperFactory` and can be used via `source="trendlyne"`
- Import check: `python -c "from app.main import app; print('OK')"` passes

## Dependencies

- `requests` (already in requirements.txt)
- `beautifulsoup4` (already in requirements.txt)
- `pydantic` (already in requirements.txt)
