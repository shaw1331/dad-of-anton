# News Analysis Feature - Implementation Plan

## Overview

Add news scraping and AI-powered news analysis to the Stock Analysis Workflow. The feature fetches news articles from Groww for each stock, uses **trafilatura** (open-source) to extract full article content, generates detailed summaries via LLM, and grades each article by market impact.

## Architecture

### Updated Workflow Flow

```
User Input: INDEX + strategy + enable_news
        │
        ▼
┌─────────────────────────┐
│ ScrapeStocksTask        │  (existing)
│ - Fetches stock list    │
│ - Scrapes technicals    │
└─────────────────────────┘
        │
        ▼  ctx.output["scrape_stocks"]
┌─────────────────────────┐
│ ScrapeNewsTask          │  (NEW)
│ - Reads stock list      │
│ - GrowwNewsScraper      │
│   per ticker            │
└─────────────────────────┘
        │
        ▼  ctx.output["scrape_news"]
┌─────────────────────────┐
│ AnalyzeNewsTask         │  (NEW)
│ - NewsAnalysisAgent     │
│   LangGraph             │
│ - fetch_content → summarize    │
│   → grade               │
└─────────────────────────┘
        │
        ▼  ctx.output["analyze_news"]
┌─────────────────────────┐
│ AnalyzeStocksTask       │  (existing)
│ - StockAnalysisAgent    │
│ - Can optionally read   │
│   news context          │
└─────────────────────────┘
```

### Module Structure

```
backend/app/
├── ai/
│   ├── models.py                 # MODIFY: Add NewsImpact enum, AnalyzedNewsArticle
│   ├── news_agent.py             # CREATE: NewsAnalysisAgent LangGraph
│   └── factory.py                # MODIFY: Register "news_analysis" agent
│
├── scraper/
│   └── groww_scraper/            # EXISTING: Already implemented
│       ├── scraper.py            #   GrowwNewsScraper (used by ScrapeNewsTask)
│       └── models.py             #   NewsArticle model
│
├── stock_analyser/
│   ├── tasks/
│   │   ├── __init__.py           # MODIFY: Export new tasks
│   │   ├── scrape_news.py        # CREATE: ScrapeNewsTask
│   │   └── analyze_news.py       # CREATE: AnalyzeNewsTask
│   └── workflow.py               # MODIFY: Add tasks + enable_news input
│
└── core/
    └── config.py                 # MODIFY: Add TAVILY_API_KEY
```

---

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| News source | Groww API (existing scraper) | Already implemented, free, reliable |
| Web content extraction | trafilatura | Open-source, best-in-class article extraction, no API key |
| Agent pattern | Separate LangGraph | Follows existing `StockAnalysisAgent` pattern |
| Grading approach | LLM-based with enum | Consistent with existing structured output pattern |
| Task split | 2 tasks (scrape + analyze) | Separation of concerns, allows reuse |
| Config toggle | `enable_news` input field | Optional, doesn't break existing workflows |
| LLM provider | Same Ollama/LangChain setup | No new provider config needed |

---

## Core Types

### `ai/models.py` — New Types

```python
from enum import Enum

class NewsImpact(str, Enum):
    """Grades news articles by potential market impact."""
    CRITICAL = "critical"   # M&A, regulatory action, fraud, bankruptcy
    HIGH = "high"           # Earnings surprises, guidance changes, CEO changes
    MEDIUM = "medium"       # Sector trends, analyst upgrades/downgrades
    LOW = "low"             # Routine announcements, minor updates

class AnalyzedNewsArticle(BaseModel):
    """A news article processed by the NewsAnalysisAgent."""
    ticker: str
    news_id: str
    url: str
    source: str
    pub_date: datetime
    raw_summary: str               # From Groww
    detailed_summary: str          # From AI (via trafilatura content extraction)
    impact: NewsImpact
    impact_reasoning: str          # Why this grade
    trader_sentiment: str          # "bullish" | "bearish" | "neutral"

class NewsAnalysisResult(BaseModel):
    """Output of the NewsAnalysisAgent for a single article."""
    articles: list[AnalyzedNewsArticle]
    ticker: str
    total_articles: int
    impact_distribution: dict[str, int]  # {"critical": 1, "high": 2, ...}
```

---

## NewsAnalysisAgent LangGraph

### Graph Topology

```
START → fetch_content → analyze → END
```

- **fetch_content**: Uses trafilatura to extract full article content from the news URL
- **analyze**: LLM generates detailed summary, grades impact, determines sentiment

### State

```python
class NewsAnalysisState(TypedDict):
    ticker: str
    articles: list[dict]           # Raw articles from Groww
    analyzed_articles: list[dict]  # Processed results
    system_prompt: str
```

### Why only 2 nodes?

The original plan had 4 nodes (fetch → summarize → grade → format), but this creates unnecessary LLM calls per article. Instead:

1. **fetch_content**: Tool node that extracts content from URLs via trafilatura (no LLM call)
2. **analyze**: Single LLM call that summarizes + grades + determines sentiment in one pass

This is more efficient (1 LLM call per batch vs 3) and follows the same pattern as `StockAnalysisAgent`.

---

## ScrapeNewsTask

### Input (from workflow context)
- Reads `ctx.get_output("scrape_stocks")` → list of stock dicts with `ticker` field

### Logic
```python
class ScrapeNewsTask:
    name = "scrape_news"

    def run(self, ctx):
        stocks = ctx.get_output("scrape_stocks")["stocks"]
        lookback_days = ctx.get_input("news_lookback_days") or 15

        scraper = GrowwNewsScraper()
        all_news = {}

        for stock in stocks:
            ticker = stock["ticker"]
            result = scraper.get_news(ticker, lookback_days)
            if result.success:
                all_news[ticker] = [article.model_dump() for article in result.data]
            else:
                all_news[ticker] = []

        ctx.set_output(self.name, {
            "news": all_news,
            "total_articles": sum(len(v) for v in all_news.values()),
        })
```

### Output
```python
{
    "news": {
        "RELIANCE": [NewsArticle, ...],
        "TCS": [NewsArticle, ...],
        ...
    },
    "total_articles": 45,
}
```

---

## AnalyzeNewsTask

### Input
- Reads `ctx.get_output("scrape_news")` → news dict per ticker
- Reads `ctx.get_output("scrape_stocks")` → stock list (for ticker context)

### Logic
```python
class AnalyzeNewsTask:
    name = "analyze_news"

    def run(self, ctx):
        news_output = ctx.get_output("scrape_news")
        news = news_output["news"]

        graph = AgentFactory.get("news_analysis", output_model=NewsAnalysisResult)

        all_analyses = {}
        for ticker, articles in news.items():
            if not articles:
                all_analyses[ticker] = []
                continue

            result = graph.run({
                "ticker": ticker,
                "articles": articles,
                "system_prompt": NEWS_SYSTEM_PROMPT,
            })

            if result.success:
                all_analyses[ticker] = result.data["articles"]
            else:
                all_analyses[ticker] = []

        ctx.set_output(self.name, {
            "analyses": all_analyses,
            "total_analyzed": sum(len(v) for v in all_analyses.values()),
        })
```

### Output
```python
{
    "analyses": {
        "RELIANCE": [AnalyzedNewsArticle, ...],
        "TCS": [AnalyzedNewsArticle, ...],
        ...
    },
    "total_analyzed": 45,
}
```

---

## Dependencies

### New packages (add to `requirements.txt`)

```
trafilatura>=1.12.0
```

### Existing packages used (no changes)

```
langgraph>=0.2.0
langchain>=0.3.0
langchain-core>=0.3.0
```

---

## Integration with Existing AnalyzeStocksTask

The `AnalyzeStocksTask` can optionally read news context to improve analysis. This is a future enhancement — the initial implementation keeps the tasks independent.

**Future enhancement**: Pass news summaries as additional context in the analysis prompt:
```python
# In AnalyzeStocksTask (future)
news_output = ctx.get_output("analyze_news")
stock_news = news_output["analyses"].get(stock["ticker"], [])
news_context = format_news_for_prompt(stock_news)
```

---

## Updated Workflow Config

```python
STOCK_ANALYSER_WORKFLOW = BaseWorkflowConfig(
    name="stock_analyser",
    description="Scrapes and analyzes stocks for a given index",
    input_fields=[
        InputField(name="index", type="str", required=True),
        InputField(name="strategy", type="str", required=False, default="value_investing"),
        InputField(name="num_stocks", type="int", required=False, default=None),
        InputField(name="selection_criteria", type="str", required=False, default="all",
                   choices=["top", "bottom", "random", "all"]),
        InputField(name="enable_news", type="bool", required=False, default=False,
                   label="Enable News Analysis",
                   description="Scrape and analyze news for each stock (uses trafilatura)"),
        InputField(name="news_lookback_days", type="int", required=False, default=15,
                   label="News Lookback Days",
                   description="How many days back to look for news articles"),
    ],
    tasks=[ScrapeStocksTask, ScrapeNewsTask, AnalyzeNewsTask, AnalyzeStocksTask],
)
```

---

## Error Handling

| Scenario | Handling |
|----------|----------|
| Groww API fails for one ticker | Skip ticker, continue with others, log warning |
| trafilatura fails | Fall back to Groww summary only, mark `detailed_summary` as empty |
| LLM fails to parse structured output | Retry once, then store raw response with error flag |
| `enable_news=false` | `ScrapeNewsTask` and `AnalyzeNewsTask` skip execution |
| No articles found for ticker | Empty list in output, no error |

---

## Implementation Order

### Phase 1: Foundation (2 tasks)
1. Add `NewsImpact` enum + `AnalyzedNewsArticle` model to `ai/models.py`
2. Add `TAVILY_API_KEY` to `core/config.py` + `.env.example`

### Phase 2: LangGraph Agent (2 tasks)
3. Create `ai/news_agent.py` — `NewsAnalysisAgent` with trafilatura tool
4. Register agent in `ai/factory.py`

### Phase 3: Workflow Tasks (2 tasks)
5. Create `stock_analyser/tasks/scrape_news.py` — `ScrapeNewsTask`
6. Create `stock_analyser/tasks/analyze_news.py` — `AnalyzeNewsTask`

### Phase 4: Integration (2 tasks)
7. Update `stock_analyser/tasks/__init__.py` — Export new tasks
8. Update `stock_analyser/workflow.py` — Add tasks + input fields

### Phase 5: Dependencies & Config (1 task)
9. Add `trafilatura` to `requirements.txt`

### Phase 6: Testing (2 tasks)
10. Unit test: `NewsAnalysisAgent` with mock trafilatura
11. Integration test: Trigger workflow with `enable_news=true`

---

## Trafilatura Integration Details

### Why trafilatura?

| Feature | trafilatura | Tavily | Direct HTTP + BeautifulSoup |
|---------|-------------|--------|-----------------------------|
| Content extraction | Best-in-class | Structured, clean | Raw HTML parsing |
| Anti-bot handling | Built-in | Built-in | Manual |
| Cost | Free, open-source | Free tier (1000/mo) | Free |
| API key required | No | Yes | No |
| Metadata extraction | Yes (author, date, etc.) | Partial | No |

### Usage

```python
import trafilatura

# Extract content from a URL
downloaded = trafilatura.fetch_url(news_url)
content = trafilatura.extract(downloaded)  # Clean text content
```

### LangChain Tool Wrapper

```python
from langchain_core.tools import tool
import trafilatura

@tool
def extract_news_content(url: str) -> str:
    """Extract full article content from a news URL."""
    downloaded = trafilatura.fetch_url(url)
    if downloaded:
        return trafilatura.extract(downloaded) or ""
    return ""
```

---

## Sample Workflow Run

```
Input: {
    "index": "NIFTY50",
    "strategy": "value_investing",
    "enable_news": true,
    "news_lookback_days": 15
}

Task 1: ScrapeStocksTask
  - ScreenerIndexScraper.get_stocks("NIFTY50") → 50 stocks
  - ScreenerStockScraper.get_multiple(tickers) → 50 StockDTOs
  - Output: { "index": "NIFTY50", "stocks": [...] }

Task 2: ScrapeNewsTask
  - GrowwNewsScraper.get_news("RELIANCE", 15) → 3 articles
  - GrowwNewsScraper.get_news("TCS", 15) → 5 articles
  - ... (50 tickers)
  - Output: { "news": { "RELIANCE": [...], ... }, "total_articles": 187 }

Task 3: AnalyzeNewsTask
  - NewsAnalysisAgent.run({ ticker: "RELIANCE", articles: [...] })
    → fetch_content (trafilatura) → analyze (LLM)
    → 3 AnalyzedNewsArticle with impact grades
  - ... (all tickers)
  - Output: { "analyses": { "RELIANCE": [...], ... }, "total_analyzed": 187 }

Task 4: AnalyzeStocksTask
  - StockAnalysisAgent per stock (existing)
  - Output: { "analyses": [...], "total_analyzed": 50 }
```

---

## Notes

- **trafilatura**: Free, open-source, no API key. Best-in-class article extraction.
- **Rate limiting**: Groww API has rate limits. The existing `GrowwNewsScraper` handles delays.
- **Caching**: Consider caching trafilatura results to avoid re-fetching the same URLs.
- **Future**: Could add a database table for `analyzed_news` to persist results across runs.
