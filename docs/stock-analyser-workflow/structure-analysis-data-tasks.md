# TASK-029: Structure Analysis Data Task & Strategy-Based Formatters

## Overview

Introduce a data structuring layer between data collection/analysis tasks and the final `AnalyzeStocksTask`. Currently, raw JSON from `ScrapeStocksTask` and `AnalyzeNewsTask` is passed directly, which produces unstructured LLM input. This task formats data into strategy-specific Markdown prompts.

## Architecture

```
backend/app/stock_analyser/
├── formatters/
│   ├── __init__.py               # Factory + exports
│   ├── base.py                   # BaseStockFormatter ABC
│   ├── momentum_formatter.py     # MomentumStrategy format
│   └── value_formatter.py        # ValueInvestingStrategy format (placeholder)
└── tasks/
    └── structure_analysis_data.py  # StructureAnalysisDataTask
```

### Formatter Factory

```python
# formatters/__init__.py
_registry: dict[str, type[BaseStockFormatter]] = {}

def get_formatter(strategy: str) -> BaseStockFormatter:
    return _registry[strategy]()

def register_formatter(strategy: str, cls: type[BaseStockFormatter]):
    _registry[strategy] = cls
```

Each formatter module self-registers on import:
```python
# momentum_formatter.py
from app.stock_analyser.formatters import register_formatter

class MomentumFormatter(BaseStockFormatter):
    ...

register_formatter("momentum", MomentumFormatter)
```

### BaseStockFormatter ABC

```python
# formatters/base.py
from abc import ABC, abstractmethod

class BaseStockFormatter(ABC):
    @abstractmethod
    def format(self, stock_data: dict, analyzed_news: list[dict], meta: dict) -> str:
        """Return structured Markdown string for the LLM."""
```

`meta` contains: `ticker`, `company_name`, `sector`, `industry`, `analysis_timeframe`, `data_as_of`.

### StructureAnalysisDataTask

```python
# tasks/structure_analysis_data.py
class StructureAnalysisDataTask:
    name = "structure_analysis_data"

    def run(self, ctx):
        strategy = ctx.get_input("strategy")
        formatter = get_formatter(strategy)

        stocks_output = ctx.get_output("scrape_stocks")
        news_output = ctx.get_output("analyze_news")

        structured = {}
        for ticker, stock_data in stocks_output["stocks"].items():
            news = news_output["analyses"].get(ticker, [])
            meta = stock_data["meta"]  # company, sector, etc.
            structured[ticker] = formatter.format(stock_data, news, meta)

        ctx.set_output(self.name, {"structured": structured})
```

### Workflow Update

```python
# workflow.py
tasks=[
    ScrapeStocksTask,
    ScrapeNewsTask,
    AnalyzeNewsTask,
    StructureAnalysisDataTask,  # NEW
    AnalyzeStocksTask,
]
```

## MomentumFormatter Output Template

The `MomentumFormatter.format()` method produces the Markdown structure defined in the user requirements:

1. **# STOCK** — company name, ticker, sector, industry, timeframe, date
2. **# TECHNICAL DATA** — Price, Moving Averages, Momentum Indicators, Volume, Relative Strength, Breakout/Support/Resistance, Volatility
3. **# FUNDAMENTAL CONTEXT** — Valuation & Profitability, Latest Financials
4. **# RECENT NEWS** — Iterates over `analyzed_news` list, rendering each with ID, source, date, sentiment, impact, summary, reasoning
5. **# ANALYSIS REQUIREMENTS** — Fixed instructions for the momentum strategy

### Field Mapping

| Template Field | Source Key |
|---|---|
| Current Price | `stock_data["price"]["current"]` |
| EMA20/50/200 | `stock_data["moving_averages"]["ema20"]`, etc. |
| RSI(14) | `stock_data["momentum"]["rsi"]` |
| Market Cap | `stock_data["fundamentals"]["market_cap"]` |
| Sales / EPS | `stock_data["fundamentals"]["financials"]["sales"]` |
| News sentiment | `analyzed_news[i]["sentiment"]` |
| News summary | `analyzed_news[i]["summary"]` |

Missing fields render as `N/A` or `NOT_AVAILABLE`.

## Tasks

### TASK-029-01: Create `formatters/__init__.py`
- [ ] Implement `get_formatter(strategy)` function
- [ ] Implement `register_formatter(strategy, cls)` function

### TASK-029-02: Create `formatters/base.py`
- [ ] Define `BaseStockFormatter` ABC with `format(stock_data, analyzed_news, meta) -> str`

### TASK-029-03: Create `formatters/momentum_formatter.py`
- [ ] Implement `MomentumFormatter` following the template
- [ ] Self-register with `register_formatter("momentum", MomentumFormatter)`
- [ ] Handle missing fields gracefully (`N/A`)

### TASK-029-04: Create `formatters/value_formatter.py` (placeholder)
- [ ] Minimal `ValueInvestingFormatter` — return raw JSON for now (to be expanded later)
- [ ] Self-register with `register_formatter("value_investing", ValueInvestingFormatter)`

### TASK-029-05: Create `tasks/structure_analysis_data.py`
- [ ] Implement `StructureAnalysisDataTask` with `name = "structure_analysis_data"`
- [ ] Read strategy from `ctx.get_input("strategy")`
- [ ] Fetch outputs from `scrape_stocks` and `analyze_news`
- [ ] Call formatter per ticker and set output

### TASK-029-06: Update `workflow.py`
- [ ] Import `StructureAnalysisDataTask`
- [ ] Add it to the tasks list after `AnalyzeNewsTask`

### TASK-029-07: Import formatters in `__init__.py`
- [ ] Create `app/stock_analyser/formatters/__init__.py` with factory
- [ ] Import all formatter modules in `app/stock_analyser/tasks/__init__.py` or at task execution to trigger registration

## Acceptance Criteria

- `StructureAnalysisDataTask` is registered in the workflow and executes in the correct order.
- `get_formatter("momentum")` returns a `MomentumFormatter` instance.
- `MomentumFormatter.format(...)` produces the exact Markdown template defined in the requirements.
- Missing fields do not crash the formatter; they render as `N/A`.
- `AnalyzeStocksTask` receives structured Markdown from `structure_analysis_data` output.

## Dependencies

- `ScrapeStocksTask` output schema: `{"stocks": {ticker: {...}}}`
- `AnalyzeNewsTask` output schema: `{"analyses": {ticker: [article, ...]}}`
- Workflow input `strategy`: `str` (default `"value_investing"`)
