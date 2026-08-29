# AI Agent Analysis - Implementation Plan

## Overview

Add AI-powered stock analysis to the Stock Analyser workflow using **LangGraph + LangChain** together:
- **LangGraph** (`StateGraph`) — Builds the agent workflow as a graph with nodes, edges, and state management
- **LangChain** (`init_chat_model`) — Creates the LLM via a provider-agnostic interface

A new `AnalyzeStocksTask` runs after `ScrapeStocksTask`, taking scraped stock data and producing BUY/HOLD/SELL recommendations with confidence levels.

Different analysis strategies (Value Investing, Momentum) use different prompts, following an Adapter + Factory pattern consistent with the existing scraper layer.

LLM providers are abstracted via LangChain's `init_chat_model` — switch between Ollama, Groq, OpenAI, or any supported provider by changing a single config string. No per-provider code needed.

---

## Architecture

### Module Structure

```
backend/app/
├── ai/                             # NEW — Reusable AI graph layer (mirrors scraper/)
│   ├── __init__.py                 # Public API
│   ├── exceptions.py               # AnalysisError, GraphError, ConfigError
│   ├── interfaces.py               # AgentGraph ABC
│   ├── factory.py                  # AgentFactory (creates graphs with configured LLM)
│   ├── models.py                   # AgentResult[T], AgentConfig
│   └── graph.py                    # LangGraph graph definition (provider-agnostic)
│
├── stock_analyser/                 # existing — domain module
│   ├── tasks/
│   │   ├── scrape_stocks.py        # existing
│   │   └── analyze_stocks.py       # NEW — bridges ai module + analysis strategies
│   ├── analysis/                   # NEW — strategy + prompting (domain-specific)
│   │   ├── __init__.py
│   │   ├── interfaces.py           # AnalysisStrategy ABC
│   │   ├── factory.py              # AnalysisFactory
│   │   └── prompts/
│   │       ├── __init__.py
│   │       ├── base.py             # Shared prompt utilities
│   │       ├── value_investing.py  # Value investing strategy
│   │       └── momentum.py         # Momentum strategy
│   └── workflow.py                 # MODIFIED — add AnalyzeStocksTask + strategy input
│
├── scraper/                        # existing — unchanged
└── workflow/                       # existing — unchanged
```

### Three Separation of Concerns

| Module | Responsibility | Reusable? |
|--------|---------------|-----------|
| `ai/` | LangGraph graph definitions, provider-agnostic LLM integration | Yes — any workflow can use it |
| `stock_analyser/analysis/` | Domain-specific prompts and strategies | No — tied to stock analysis domain |
| `stock_analyser/tasks/analyze_stocks.py` | Glue: reads context, calls strategy + agent, sets output | No — task-specific |

---

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Workflow engine | **LangGraph** (`StateGraph`) | Stateful graph with nodes, edges, checkpointing, expandable |
| LLM provider | **LangChain** (`init_chat_model`) | Switch providers via env var, no code changes |
| Default provider | Ollama (local) | Free, unlimited, no API key needed |
| AI module pattern | AgentGraph ABC + Factory (mirrors scraper/) | Consistent with existing codebase patterns |
| Strategy location | Inside `stock_analyser/analysis/` | Prompts are domain-specific, not reusable |
| Agent graph location | Inside `ai/graph.py` | Single file, provider-agnostic |
| Sync vs Async | Sync | Matches existing `BaseWorkflowTask.run()` pattern |
| Graph complexity | Single node, expandable | Start simple; LangGraph makes adding nodes trivial |
| Output format | Structured Pydantic models | Type-safe, validated LLM output |

### How LangGraph + LangChain Work Together

```
┌─────────────────────────────────────────────────────────────────┐
│  LangGraph (StateGraph)                                        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ START       │───▶│ analyze     │───▶│ END         │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                          │                                     │
│                          ▼                                     │
│                   ┌─────────────┐                              │
│                   │ LLM.invoke()│ ◀── LangChain BaseChatModel  │
│                   └─────────────┘                              │
│                          │                                     │
│                          ▼                                     │
│                   ┌─────────────┐                              │
│                   │ Parse JSON  │                              │
│                   └─────────────┘                              │
└─────────────────────────────────────────────────────────────────┘

LLM created via:
  init_chat_model("ollama:llama3")  → ChatOllama
  init_chat_model("groq:llama-3.3") → ChatGroq
  init_chat_model("openai:gpt-4o")  → ChatOpenAI
```

---

## LLM Provider Abstraction

### How It Works

LangChain provides `init_chat_model` which returns a `BaseChatModel` regardless of provider:

```python
from langchain.chat_models import init_chat_model

# All three return the same BaseChatModel interface:
llm = init_chat_model("ollama:llama3", temperature=0)        # Local, free, unlimited
llm = init_chat_model("groq:llama-3.3-70b-versatile", ...)  # Free tier, very fast
llm = init_chat_model("openai:gpt-4o", ...)                  # Paid, best quality
```

### Supported Free Providers

| Provider | Package | Free Models | Limits | Best For |
|----------|---------|-------------|--------|----------|
| **Ollama** (local) | `langchain-ollama` | All open models | Unlimited | Full control, no API key |
| **Ollama Cloud** | `langchain-ollama` | Qwen, GPT-OSS, DeepSeek | 1 concurrent, 5hr sessions | Cloud-hosted open models |
| **Groq** | `langchain-groq` | Llama 3.3, Llama 4, GPT-OSS | 30 RPM / 1000 RPD | Very fast inference |
| **OpenRouter** | `langchain-openrouter` | ~23 `:free` routes | 20 RPM / 50 RPD | Model variety |
| **Google Gemini** | `langchain-google-genai` | Gemini 2.5 Flash | Generous | Frontier-class quality |
| **HuggingFace** | `langchain-huggingface` | DeepSeek, Kimi, Qwen3 | $0.10/mo credit | Open models |
| **Cerebras** | (OpenAI-compat) | Qwen3 235B | 5 RPM | Fast inference |
| **Mistral** | `langchain-mistralai` | Large 3, Codestral | Free experimentation | Code analysis |

### Configuration

Switch providers by changing two env vars — zero code changes:

```bash
# .env — Ollama (default, local, free)
LLM_PROVIDER=ollama
LLM_MODEL=llama3

# .env — Groq (free tier, very fast)
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
GROQ_API_KEY=gsk_...

# .env — OpenAI (paid, best quality)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-...
```

---

## Core Types

### `ai/models.py`

```python
from typing import Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class AgentResult(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: str | None = None
    graph_name: str

class AgentConfig(BaseModel):
    provider: str = "ollama"
    model: str = "llama3"
    temperature: float = 0.3
    timeout: int = 120
```

### `ai/interfaces.py`

```python
from abc import ABC, abstractmethod
from typing import Any
from app.ai.models import AgentResult

class AgentGraph(ABC):
    """Base interface for all LangGraph graph implementations."""

    @abstractmethod
    def run(self, input_data: dict[str, Any]) -> AgentResult:
        """Execute the graph with input data and return result."""
        ...

    @property
    @abstractmethod
    def name(self) -> str: ...
```

### `ai/factory.py`

```python
from langchain.chat_models import init_chat_model

class AgentFactory:
    _graphs: dict[str, type[AgentGraph]] = {}

    @classmethod
    def register(cls, name: str, graph_cls: type[AgentGraph]) -> None:
        """Register an AgentGraph implementation."""
        cls._graphs[name] = graph_cls

    @classmethod
    def get(cls, name: str) -> AgentGraph:
        """Get an AgentGraph instance with configured LLM.
        
        Uses init_chat_model to create provider-agnostic LLM.
        Provider/model configured via LLM_PROVIDER and LLM_MODEL env vars.
        """
        from app.core.config import settings
        
        llm = init_chat_model(
            model=settings.LLM_MODEL,
            model_provider=settings.LLM_PROVIDER,
            temperature=settings.LLM_TEMPERATURE,
        )
        
        graph_cls = cls._graphs.get(name)
        if graph_cls is None:
            raise ConfigError(f"No graph registered for '{name}'")
        
        return graph_cls(llm=llm)
```

### `ai/exceptions.py`

```python
class AnalysisError(Exception):
    """Base exception for ai module."""

class GraphError(AnalysisError):
    """Raised when graph execution fails."""

class ConfigError(AnalysisError):
    """Raised when there is a configuration error."""
```

### `stock_analyser/analysis/interfaces.py`

```python
class AnalysisStrategy(ABC):
    """Domain-specific analysis strategy (prompts)."""

    @abstractmethod
    def get_system_prompt(self) -> str: ...

    @abstractmethod
    def get_analysis_prompt(self, stock_data: dict) -> str: ...

    @property
    @abstractmethod
    def name(self) -> str: ...
```

### `stock_analyser/analysis/factory.py`

```python
class AnalysisFactory:
    _strategies: dict[str, type[AnalysisStrategy]] = {}

    @classmethod
    def register(cls, name: str, strategy_cls: type[AnalysisStrategy]) -> None: ...

    @classmethod
    def get(cls, name: str = "value_investing") -> AnalysisStrategy: ...
```

---

## Data Flow

```
Workflow Trigger: { "index": "NIFTY50", "strategy": "value_investing" }
  │
  ├─ Task 1: ScrapeStocksTask
  │    ├─ IndexScraper.get_stocks("NIFTY50")
  │    ├─ StockScraper.get_multiple(tickers)
  │    └─ ctx.set_output("scrape_stocks", { "index": "NIFTY50", "stocks": [...] })
  │
  └─ Task 2: AnalyzeStocksTask
       ├─ ctx.get_output("scrape_stocks") → stocks list
       │
       ├─ AnalysisFactory.get("value_investing") → ValueInvestingStrategy
       │    ├─ .get_system_prompt() → "You are a value investing analyst..."
       │    └─ .get_analysis_prompt(stock) → "Analyze RELIANCE for value..."
       │
       ├─ AgentFactory.get("stock_analysis")
       │    ├─ init_chat_model(model="llama3", model_provider="ollama")
       │    └─ StockAnalysisAgent(llm=llm)
       │         └─ LangGraph: [START] → analyze_node → [END]
       │              └─ Calls LLM → Parses structured JSON
       │
       └─ ctx.set_output("analyze_stocks", {
            "index": "NIFTY50",
            "strategy": "value_investing",
            "analyses": [
              { "ticker": "RELIANCE", "recommendation": "BUY", "confidence": 0.85, ... },
              ...
            ]
          })
```

---

## LangGraph Graph Design

All graphs use LangGraph's `StateGraph` with typed state. The LLM is injected via LangChain's `BaseChatModel`.

### Initial: Single Node (`ai/graph.py`)

```python
from typing import TypedDict, Any
from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph, END

class StockAnalysisState(TypedDict):
    stock_data: dict
    system_prompt: str
    analysis_prompt: str
    raw_response: str
    parsed_analysis: dict | None

class StockAnalysisAgent(AgentGraph):
    name = "stock_analysis"

    def __init__(self, llm: BaseChatModel) -> None:
        self.llm = llm
        self._graph = self._build_graph()

    def _build_graph(self):
        def analyze_node(state: StockAnalysisState) -> dict:
            # 1. Call LLM with system_prompt + analysis_prompt
            from langchain_core.messages import SystemMessage, HumanMessage
            messages = [
                SystemMessage(content=state["system_prompt"]),
                HumanMessage(content=state["analysis_prompt"]),
            ]
            response = self.llm.invoke(messages)
            
            # 2. Parse JSON response
            import json
            try:
                parsed = json.loads(response.content)
            except json.JSONDecodeError:
                parsed = None
            
            return {
                "raw_response": response.content,
                "parsed_analysis": parsed,
            }

        graph = StateGraph(StockAnalysisState)
        graph.add_node("analyze", analyze_node)
        graph.set_entry_point("analyze")
        graph.add_edge("analyze", END)
        return graph.compile()

    def run(self, input_data: dict[str, Any]) -> AgentResult:
        initial_state = {
            "stock_data": input_data["stock_data"],
            "system_prompt": input_data["system_prompt"],
            "analysis_prompt": input_data["analysis_prompt"],
            "raw_response": "",
            "parsed_analysis": None,
        }
        
        result = self._graph.invoke(initial_state)
        
        return AgentResult(
            success=result["parsed_analysis"] is not None,
            data=result["parsed_analysis"] or {"raw": result["raw_response"]},
            error=None if result["parsed_analysis"] else "Failed to parse LLM response",
            graph_name=self.name,
        )
```

### Future: Multi-Node Expansion (LangGraph)

Adding new nodes is trivial with LangGraph:

```python
# Current: single node
graph = StateGraph(StockAnalysisState)
graph.add_node("analyze", analyze_node)
graph.set_entry_point("analyze")
graph.add_edge("analyze", END)

# Future: multi-node pipeline
graph = StateGraph(StockAnalysisState)
graph.add_node("analyze", analyze_node)
graph.add_node("review", review_node)
graph.add_node("aggregate", aggregate_node)
graph.set_entry_point("analyze")
graph.add_edge("analyze", "review")
graph.add_conditional_edges("review", quality_check)  # branching
graph.add_edge("aggregate", END)
```

LangGraph benefits:
- **State persistence** — checkpointing between nodes
- **Conditional edges** — branch based on analysis quality
- **Human-in-the-loop** — pause for review before final output
- **Streaming** — stream node outputs as they complete

---

## Concrete Strategies

### Value Investing (`analysis/prompts/value_investing.py`)

- **System**: "You are a value investing analyst. Evaluate stocks based on intrinsic value, financial health, and margin of safety."
- **Prompt**: Sends stock ratios (P/E, ROE, debt), quarterly results, shareholding patterns, pros/cons
- **Output**: BUY if undervalued with strong fundamentals, HOLD if fairly priced, SELL if overvalued

### Momentum (`analysis/prompts/momentum.py`)

- **System**: "You are a momentum trading analyst. Evaluate stocks based on price trends, volume, and technical indicators."
- **Prompt**: Sends price data, volume, technical indicators (if available)
- **Output**: BUY if strong upward momentum, HOLD if neutral, SELL if downward trend

---

## Configuration

### `requirements.txt` additions

```
langgraph>=0.2.0
langchain-core>=0.3.0
langchain-ollama>=0.3.0       # Ollama provider (default)
langchain-groq>=0.2.0         # Groq provider (free tier)
langchain-openai>=0.2.0       # OpenAI provider (optional)
```

### `app/core/config.py` additions

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # LLM Provider Configuration
    LLM_PROVIDER: str = "ollama"           # ollama, groq, openai, google_genai, etc.
    LLM_MODEL: str = "llama3"              # Model name for the chosen provider
    LLM_TEMPERATURE: float = 0.3           # Temperature for generation
    LLM_TIMEOUT: int = 120                 # Timeout in seconds
```

### `.env.example` additions

```bash
# LLM Provider Configuration
# Options: ollama, groq, openai, google_genai, anthropic, openrouter
LLM_PROVIDER=ollama
LLM_MODEL=llama3
LLM_TEMPERATURE=0.3

# Provider-specific API keys (only needed if using that provider)
# OLLAMA_BASE_URL=http://localhost:11434   # Only for remote Ollama
# GROQ_API_KEY=gsk_...                     # If using Groq
# OPENAI_API_KEY=sk-...                    # If using OpenAI
# GOOGLE_API_KEY=...                       # If using Google Gemini
```

---

## Workflow Integration

### `stock_analyser/workflow.py`

```python
STOCK_ANALYSER_WORKFLOW = BaseWorkflowConfig(
    name="stock_analyser",
    description="Scrapes and analyzes stocks for a given index",
    input_fields=[
        InputField(name="index", type="str", label="Stock Index", required=True),
        InputField(
            name="strategy",
            type="str",
            label="Analysis Strategy",
            description="Analysis strategy to use (value_investing, momentum)",
            required=False,
            default="value_investing",
        ),
    ],
    tasks=[ScrapeStocksTask, AnalyzeStocksTask],
)
```

---

## Implementation Order

### Phase 1: AI Module (Foundation)

| Step | File | Description |
|------|------|-------------|
| 1 | `ai/exceptions.py` | Custom exceptions |
| 2 | `ai/models.py` | AgentResult, AgentConfig DTOs |
| 3 | `ai/interfaces.py` | AgentGraph ABC |
| 4 | `ai/factory.py` | AgentFactory with init_chat_model |
| 5 | `ai/graph.py` | LangGraph stock analysis agent |
| 6 | `ai/__init__.py` | Public API exports |

### Phase 2: Analysis Module (Strategy)

| Step | File | Description |
|------|------|-------------|
| 7 | `analysis/interfaces.py` | AnalysisStrategy ABC |
| 8 | `analysis/factory.py` | AnalysisFactory |
| 9 | `analysis/prompts/base.py` | Shared prompt utilities |
| 10 | `analysis/prompts/value_investing.py` | Value investing strategy |
| 11 | `analysis/prompts/momentum.py` | Momentum strategy |
| 12 | `analysis/prompts/__init__.py` | Auto-register strategies |
| 13 | `analysis/__init__.py` | Public API exports |

### Phase 3: Task Integration

| Step | File | Description |
|------|------|-------------|
| 14 | `stock_analyser/tasks/analyze_stocks.py` | AnalyzeStocksTask |
| 15 | `stock_analyser/tasks/__init__.py` | Export AnalyzeStocksTask |
| 16 | `stock_analyser/workflow.py` | Add task + strategy input |

### Phase 4: Configuration

| Step | File | Description |
|------|------|-------------|
| 17 | `requirements.txt` | Add LangGraph + LangChain dependencies |
| 18 | `app/core/config.py` | Add LLM settings |
| 19 | `.env.example` | Add LLM env vars |

---

## Future Extensibility

| What | How |
|------|-----|
| Add new strategy | Create prompt file in `analysis/prompts/`, register in `__init__.py` |
| Add new agent graph | Create class in `ai/graph.py`, implement `AgentGraph`, register in factory |
| Use agent in another workflow | `AgentFactory.get("stock_analysis")` from any task |
| Switch LLM provider | Change `LLM_PROVIDER` and `LLM_MODEL` env vars |
| Add new LLM provider | `pip install langchain-{provider}`, add to env vars |
| Add graph complexity | Add nodes to `StockAnalysisAgent._build_graph()` |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM provider unavailable | All analysis tasks fail | Clear error message, check health before workflow |
| LLM output not valid JSON | Parsing fails | Retry logic, fallback to raw text output |
| Slow inference (50 stocks) | Workflow takes long time | Start with batch size config, add progress tracking |
| Model hallucination | Incorrect recommendations | Structured output schema, confidence threshold |
| Ollama not running | Local provider fails | Document setup, provide fallback provider option |
