# News Analysis Feature - Task Breakdown

## Epic: News Analysis in Stock Analyser Workflow

---

## Phase 1: Foundation

### TASK-019: Add `NewsImpact` Enum + `AnalyzedNewsArticle` Model ✓

**Description:**
Add the news impact grading enum and the output model for analyzed news articles to `backend/app/ai/models.py`.

**Implementation:**
```python
class NewsImpact(str, Enum):
    """Grades news articles by potential market impact."""
    CRITICAL = "critical"   # M&A, regulatory action, fraud, bankruptcy
    HIGH = "high"           # Earnings surprises, guidance changes, CEO changes
    MEDIUM = "medium"       # Sector trends, analyst upgrades/downgrades
    LOW = "low"             # Routine announcements, minor updates

class AnalyzedNewsArticle(BaseModel):
    ticker: str
    news_id: str
    url: str
    source: str
    pub_date: datetime
    raw_summary: str
    detailed_summary: str
    impact: NewsImpact
    impact_reasoning: str
    trader_sentiment: str  # "bullish" | "bearish" | "neutral"

class NewsAnalysisResult(BaseModel):
    articles: list[AnalyzedNewsArticle]
    ticker: str
    total_articles: int
    impact_distribution: dict[str, int]
```

**Acceptance Criteria:**
- [x] File updated at `backend/app/ai/models.py`
- [x] `NewsImpact` inherits from `str, Enum`
- [x] All fields have proper type hints
- [x] `AnalyzedNewsArticle` uses Pydantic BaseModel

---

### TASK-020: Add `trafilatura` to `requirements.txt` ✓

**Description:**
Add the trafilatura library to `backend/requirements.txt` for open-source article content extraction. No API key required.

**Implementation:**

In `backend/requirements.txt`, add:
```
trafilatura>=1.12.0
```

**Acceptance Criteria:**
- [x] `trafilatura` added with version constraint
- [x] No API key needed (open-source)
- [x] Run `pip install -r requirements.txt` to install

---

## Phase 2: LangGraph Agent

### TASK-021: Create `ai/news_agent.py` — NewsAnalysisAgent

**Description:**
Create `backend/app/ai/news_agent.py` with the LangGraph agent for news analysis. This agent fetches full article content via trafilatura, then uses the LLM to summarize, grade, and determine sentiment.

**Implementation:**

```python
class NewsAnalysisState(TypedDict):
    ticker: str
    articles: list[dict]
    analyzed_articles: list[dict]
    system_prompt: str

class NewsAnalysisAgent(AgentGraph):
    name = "news_analysis"

    def __init__(self, llm: BaseChatModel, output_model: type[BaseModel]) -> None:
        self.llm = llm
        self.output_model = output_model
        self._graph = self._build_graph()

    def _build_graph(self):
        # Tool: extract_news_content (trafilatura)
        # Node 1: fetch_content (calls trafilatura tool for each article URL)
        # Node 2: analyze (LLM summarizes + grades + determines sentiment)
        # Edge: fetch_content → analyze → END
        ...

    def run(self, input_data: dict[str, Any]) -> AgentResult:
        # Invokes graph with ticker, articles, system_prompt
        ...
```

Key implementation details:
- Use `@tool` decorator for trafilatura extraction function
- Use `ToolNode` from LangGraph for the fetch_content node
- Single LLM call in `analyze` node (not per-article)
- Parse structured output as `NewsAnalysisResult`

**Acceptance Criteria:**
- [x] File created at `backend/app/ai/news_agent.py`
- [x] Extends `AgentGraph` interface
- [x] Uses `StateGraph` from LangGraph
- [x] Includes trafilatura tool as LangChain `@tool`
- [x] Registered with `AgentFactory` at module level
- [x] Handles trafilatura errors gracefully (returns raw summary as fallback)

---

### TASK-022: Register NewsAnalysisAgent in `ai/factory.py`

**Description:**
The `NewsAnalysisAgent` self-registers via `AgentFactory.register("news_analysis", NewsAnalysisAgent)` at module import time (same pattern as `StockAnalysisAgent`). No changes needed to `factory.py` itself — just ensure the module is imported.

**Implementation:**
- Add import in `backend/app/ai/__init__.py`:
  ```python
  import app.ai.news_agent  # noqa: F401
  ```

**Acceptance Criteria:**
- [x] `news_agent` module is imported on app startup
- [x] `AgentFactory.get("news_analysis")` returns a `NewsAnalysisAgent` instance
- [x] No duplicate registrations

---

## Phase 3: Workflow Tasks

### TASK-023: Create `stock_analyser/tasks/scrape_news.py` — ScrapeNewsTask

**Description:**
Create `backend/app/stock_analyser/tasks/scrape_news.py` with a task that fetches news articles for all stocks using `GrowwNewsScraper`.

**Implementation:**

```python
class ScrapeNewsTask:
    """Scrapes news articles for all stocks using GrowwNewsScraper."""

    name = "scrape_news"

    def run(self, ctx: Any) -> None:
        # Check if news is enabled
        enable_news = ctx.get_input("enable_news")
        if not enable_news:
            ctx.set_output(self.name, {"news": {}, "total_articles": 0})
            return

        # Read stocks from previous task
        stocks = ctx.get_output("scrape_stocks")["stocks"]
        lookback_days = ctx.get_input("news_lookback_days") or 15

        scraper = GrowwNewsScraper()
        all_news = {}

        for stock in stocks:
            ticker = stock.get("ticker", "")
            result = scraper.get_news(ticker, lookback_days)
            if result.success:
                all_news[ticker] = [a.model_dump(mode="json") for a in result.data]
            else:
                logger.warning("No news for %s: %s", ticker, result.error)
                all_news[ticker] = []

        ctx.set_output(self.name, {
            "news": all_news,
            "total_articles": sum(len(v) for v in all_news.values()),
        })
```

**Acceptance Criteria:**
- [x] File created at `backend/app/stock_analyser/tasks/scrape_news.py`
- [x] Reads `enable_news` input, skips if false
- [x] Reads stocks from `ctx.get_output("scrape_stocks")`
- [x] Uses `GrowwNewsScraper.get_news()` per ticker
- [x] Handles individual ticker failures gracefully
- [x] Stores results in `ctx.set_output()`

---

### TASK-024: Create `stock_analyser/tasks/analyze_news.py` — AnalyzeNewsTask

**Description:**
Create `backend/app/stock_analyser/tasks/analyze_news.py` with a task that processes news articles through the `NewsAnalysisAgent` LangGraph.

**Implementation:**

```python
class AnalyzeNewsTask:
    """Analyzes news articles using the NewsAnalysisAgent LangGraph."""

    name = "analyze_news"

    NEWS_SYSTEM_PROMPT = """You are a financial news analyst for the Indian stock market.
    Analyze the provided news articles and for each one:
    1. Generate a detailed 2-3 paragraph summary
    2. Grade the impact (CRITICAL, HIGH, MEDIUM, LOW)
    3. Determine trader sentiment (bullish, bearish, neutral)

    Impact grading guide:
    - CRITICAL: M&A, regulatory action, fraud, bankruptcy, major legal issues
    - HIGH: Earnings surprises, guidance changes, CEO/CFO changes, large contracts
    - MEDIUM: Sector trends, analyst upgrades/downgrades, moderate news
    - LOW: Routine announcements, minor updates, routine disclosures"""

    def run(self, ctx: Any) -> None:
        enable_news = ctx.get_input("enable_news")
        if not enable_news:
            ctx.set_output(self.name, {"analyses": {}, "total_analyzed": 0})
            return

        news_output = ctx.get_output("scrape_news")
        if not news_output:
            raise Exception("No news data found. Run ScrapeNewsTask first.")

        news = news_output["news"]
        graph = AgentFactory.get("news_analysis", output_model=NewsAnalysisResult)

        all_analyses = {}
        for ticker, articles in news.items():
            if not articles:
                all_analyses[ticker] = []
                continue

            logger.info("Analyzing %d news articles for %s", len(articles), ticker)
            result = graph.run({
                "ticker": ticker,
                "articles": articles,
                "system_prompt": self.NEWS_SYSTEM_PROMPT,
            })

            if result.success:
                all_analyses[ticker] = result.data["articles"]
            else:
                logger.error("News analysis failed for %s: %s", ticker, result.error)
                all_analyses[ticker] = []

        ctx.set_output(self.name, {
            "analyses": all_analyses,
            "total_analyzed": sum(len(v) for v in all_analyses.values()),
        })
```

**Acceptance Criteria:**
- [x] File created at `backend/app/stock_analyser/tasks/analyze_news.py`
- [x] Reads `enable_news` input, skips if false
- [x] Reads news from `ctx.get_output("scrape_news")`
- [x] Uses `AgentFactory.get("news_analysis")` to get the graph
- [x] Processes all tickers, handles failures gracefully
- [x] Stores results in `ctx.set_output()`

---

## Phase 4: Integration

### TASK-025: Update `stock_analyser/tasks/__init__.py` — Export New Tasks

**Description:**
Update `backend/app/stock_analyser/tasks/__init__.py` to export the new `ScrapeNewsTask` and `AnalyzeNewsTask`.

**Implementation:**
```python
__all__ = ["AnalyzeNewsTask", "AnalyzeStocksTask", "ScrapeNewsTask", "ScrapeStocksTask"]

def __getattr__(name: str):
    if name == "ScrapeNewsTask":
        from app.stock_analyser.tasks.scrape_news import ScrapeNewsTask
        return ScrapeNewsTask
    if name == "AnalyzeNewsTask":
        from app.stock_analyser.tasks.analyze_news import AnalyzeNewsTask
        return AnalyzeNewsTask
    # ... existing entries ...
```

**Acceptance Criteria:**
- [x] `ScrapeNewsTask` and `AnalyzeNewsTask` are importable
- [x] Lazy import pattern maintained (no circular imports)

---

### TASK-026: Update `stock_analyser/workflow.py` — Add Tasks + Input Fields

**Description:**
Update `backend/app/stock_analyser/workflow.py` to include the new tasks and add `enable_news` and `news_lookback_days` input fields.

**Implementation:**
```python
from app.stock_analyser.tasks import (
    AnalyzeNewsTask,
    AnalyzeStocksTask,
    ScrapeNewsTask,
    ScrapeStocksTask,
)

STOCK_ANALYSER_WORKFLOW = BaseWorkflowConfig(
    name="stock_analyser",
    description="Scrapes and analyzes stocks for a given index",
    input_fields=[
        # ... existing fields ...
        InputField(
            name="enable_news",
            type="bool",
            label="Enable News Analysis",
            description="Scrape and analyze news for each stock (uses trafilatura)",
            required=False,
            default=False,
        ),
        InputField(
            name="news_lookback_days",
            type="int",
            label="News Lookback Days",
            description="How many days back to look for news articles",
            required=False,
            default=15,
        ),
    ],
    tasks=[ScrapeStocksTask, ScrapeNewsTask, AnalyzeNewsTask, AnalyzeStocksTask],
)
```

**Acceptance Criteria:**
- [x] New tasks added to `tasks` list in correct order
- [x] `enable_news` input field with boolean type
- [x] `news_lookback_days` input field with integer type
- [x] Import statements updated

---

## Phase 5: Dependencies

### TASK-027: Add `trafilatura` to `requirements.txt`

**Description:**
Add the trafilatura library to `backend/requirements.txt` for open-source article content extraction.

**Implementation:**
Add to `requirements.txt`:
```
trafilatura>=1.12.0
```

**Acceptance Criteria:**
- [x] `trafilatura` added with version constraint
- [x] Run `pip install -r requirements.txt` to install

---

## Phase 6: Testing

### TASK-028: Unit Test — NewsAnalysisAgent

**Description:**
Write unit tests for `NewsAnalysisAgent` with mocked trafilatura client and LLM responses.

**Test cases:**
1. Agent processes articles correctly with valid trafilatura response
2. Agent handles trafilatura failure gracefully (falls back to raw summary)
3. Agent handles LLM parse failure (structured output fails)
4. Agent returns empty list when no articles provided

**Acceptance Criteria:**
- [ ] Test file created at `backend/tests/test_news_agent.py`
- [ ] All 4 test cases pass
- [ ] trafilatura client is mocked (no real API calls)
- [ ] LLM is mocked (no real inference)

---

### TASK-029: Integration Test — Trigger Workflow with News Enabled

**Description:**
Manually test the full workflow with `enable_news=true` to verify end-to-end flow.

**Steps:**
1. Start backend: `uvicorn app.main:app --reload`
2. Ensure `TAVILY_API_KEY` is set in `.env`
3. Trigger: `POST /api/v1/workflows/stock_analyser/trigger` with:
   ```json
   {
       "index": "SMALLCAP50",
       "num_stocks": 2,
       "enable_news": true,
       "news_lookback_days": 7
   }
   ```
4. Verify workflow completes with all 4 tasks
5. Check news articles are scraped and analyzed

**Acceptance Criteria:**
- [ ] Workflow triggers successfully
- [ ] `ScrapeNewsTask` fetches articles
- [ ] `AnalyzeNewsTask` processes articles with impact grades
- [ ] Output contains `detailed_summary`, `impact`, `trader_sentiment`

---

## Task Dependencies

```
TASK-019 ─────────────────────────────────────┐
TASK-020 ─────────────────────────────────────┤
                                              ▼
                                        TASK-021 → TASK-022
                                              │
                                              ▼
                                        TASK-023 ──→ TASK-024
                                              │         │
                                              ▼         ▼
                                        TASK-025 ←─────┘
                                              │
                                              ▼
                                        TASK-026
                                              │
                                              ▼
                                        TASK-027
                                              │
                                              ▼
                                        TASK-028 → TASK-029
```

---

## Estimated Time

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1: Foundation | 2 tasks | 30 mins |
| Phase 2: LangGraph Agent | 2 tasks | 2-3 hours |
| Phase 3: Workflow Tasks | 2 tasks | 1-2 hours |
| Phase 4: Integration | 2 tasks | 30 mins |
| Phase 5: Dependencies | 1 task | 5 mins |
| Phase 6: Testing | 2 tasks | 1-2 hours |
| **Total** | **11 tasks** | **5-8 hours** |

---

## Notes

- **trafilatura**: Free, open-source, no API key. Best-in-class article extraction.
- **Groww rate limits**: Existing scraper handles delays. ~75s for 50 tickers.
- **Fallback behavior**: If trafilatura fails, uses Groww's raw summary as `detailed_summary`.
- **Future enhancements**:
  - Pass news context to `AnalyzeStocksTask` for richer stock analysis
  - Persist `AnalyzedNewsArticle` in database for historical tracking
  - Add news filtering by impact level (only analyze HIGH/CRITICAL)
