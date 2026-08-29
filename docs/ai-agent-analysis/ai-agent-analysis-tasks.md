# AI Agent Analysis - Task Breakdown

## Epic: AI Agent Analysis

---

## Phase 1: AI Module (Foundation)

### TASK-001: Create `ai/exceptions.py` — Custom Exceptions

**Description:**
Create `backend/app/ai/exceptions.py` with custom exception classes for the AI module.

**Implementation:**
- `AnalysisError(Exception)` — Base exception for ai module
- `GraphError(AnalysisError)` — Raised when graph execution fails
- `ConfigError(AnalysisError)` — Raised when there is a configuration error

**Acceptance Criteria:**
- [x] File created at `backend/app/ai/exceptions.py`
- [x] All exceptions inherit from `AnalysisError`
- [x] Exceptions have descriptive error messages

---

### TASK-002: Create `ai/models.py` — AgentResult and AgentConfig DTOs

**Description:**
Create `backend/app/ai/models.py` with generic return types and configuration models.

**Implementation:**
- `AgentResult[T]` — Generic result wrapper (success, data, error, graph_name)
- `AgentConfig` — LLM provider configuration (provider, model, temperature, timeout)

**Acceptance Criteria:**
- [x] File created at `backend/app/ai/models.py`
- [x] `AgentResult[T]` is Generic and type-safe
- [x] All DTOs use Pydantic BaseModel
- [x] All DTOs have proper type hints

---

### TASK-003: Create `ai/interfaces.py` — AgentGraph ABC

**Description:**
Create `backend/app/ai/interfaces.py` with abstract base class for agent graphs.

**Implementation:**
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

**Acceptance Criteria:**
- [x] File created at `backend/app/ai/interfaces.py`
- [x] `AgentGraph` is abstract (cannot be instantiated)
- [x] All methods have proper type hints
- [x] Methods raise `NotImplementedError` if not overridden

---

### TASK-004: Create `ai/factory.py` — AgentFactory

**Description:**
Create `backend/app/ai/factory.py` with the factory class for agent graphs. The factory uses LangChain's `init_chat_model` to create a provider-agnostic LLM based on config settings.

**Implementation:**
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
        
        Raises:
            ConfigError: If no graph is registered for the name.
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

**Acceptance Criteria:**
- [x] File created at `backend/app/ai/factory.py`
- [x] Factory has class methods for registration and retrieval
- [x] Uses `init_chat_model` for provider-agnostic LLM creation
- [x] Reads `LLM_PROVIDER`, `LLM_MODEL`, `LLM_TEMPERATURE` from settings
- [x] Raises `ConfigError` if graph name not registered

---

### TASK-005: Create `ai/graph.py` — LangGraph Stock Analysis Agent

**Description:**
Create `backend/app/ai/graph.py` with the LangGraph graph implementation for stock analysis. Uses **LangGraph's `StateGraph`** for the workflow graph and **LangChain's `BaseChatModel`** for provider-agnostic LLM injection.

**Implementation:**
```python
from typing import TypedDict, Any
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
import json

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
            messages = [
                SystemMessage(content=state["system_prompt"]),
                HumanMessage(content=state["analysis_prompt"]),
            ]
            response = self.llm.invoke(messages)
            
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

**Acceptance Criteria:**
- [x] File created at `backend/app/ai/graph.py`
- [x] `StockAnalysisAgent` accepts `BaseChatModel` via constructor (dependency injection)
- [x] Uses LangGraph's `StateGraph` to define the workflow graph
- [x] Graph compiles successfully
- [x] `analyze_node` calls LLM with system_prompt + analysis_prompt
- [x] Response parsing handles valid JSON
- [x] Response parsing handles invalid JSON gracefully (returns raw text)
- [x] `StockAnalysisAgent` implements `AgentGraph` interface
- [x] `StockAnalysisAgent.name` returns `"stock_analysis"`

---

### TASK-006: Create `ai/__init__.py` — Public API Exports

**Description:**
Create `backend/app/ai/__init__.py` with module exports.

**Implementation:**
- Export `AgentFactory`
- Export `StockAnalysisAgent` from `graph.py`
- Export all DTOs from `models.py`
- Export all exceptions from `exceptions.py`
- Export `AgentGraph` interface

**Acceptance Criteria:**
- [x] File created at `backend/app/ai/__init__.py`
- [x] All public symbols are importable from `app.ai`

---

## Phase 2: Analysis Module (Strategy)

### TASK-007: Create `stock_analyser/analysis/interfaces.py` — AnalysisStrategy ABC

**Description:**
Create `backend/app/stock_analyser/analysis/interfaces.py` with abstract base class for analysis strategies.

**Implementation:**
```python
from abc import ABC, abstractmethod

class AnalysisStrategy(ABC):
    """Domain-specific analysis strategy (prompts)."""

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this strategy."""
        ...

    @abstractmethod
    def get_analysis_prompt(self, stock_data: dict) -> str:
        """Return the analysis prompt for a specific stock."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the strategy name."""
        ...
```

**Acceptance Criteria:**
- [ ] File created at `backend/app/stock_analyser/analysis/interfaces.py`
- [ ] `AnalysisStrategy` is abstract (cannot be instantiated)
- [ ] All methods have proper type hints

---

### TASK-008: Create `stock_analyser/analysis/factory.py` — AnalysisFactory

**Description:**
Create `backend/app/stock_analyser/analysis/factory.py` with the factory class for analysis strategies.

**Implementation:**
```python
from app.scraper.exceptions import ConfigError

class AnalysisFactory:
    _strategies: dict[str, type[AnalysisStrategy]] = {}

    @classmethod
    def register(cls, name: str, strategy_cls: type[AnalysisStrategy]) -> None:
        """Register an AnalysisStrategy implementation."""
        cls._strategies[name] = strategy_cls

    @classmethod
    def get(cls, name: str = "value_investing") -> AnalysisStrategy:
        """Get an AnalysisStrategy instance by name.
        
        Raises:
            ConfigError: If no strategy is registered for the name.
        """
        strategy_cls = cls._strategies.get(name)
        if strategy_cls is None:
            available = list(cls._strategies.keys())
            raise ConfigError(
                f"No AnalysisStrategy registered for '{name}'. "
                f"Available strategies: {available}"
            )
        return strategy_cls()
```

**Acceptance Criteria:**
- [ ] File created at `backend/app/stock_analyser/analysis/factory.py`
- [ ] Factory has class methods for registration and retrieval
- [ ] Raises `ConfigError` if strategy name not registered
- [ ] Default strategy is `"value_investing"`

---

### TASK-009: Create `stock_analyser/analysis/prompts/base.py` — Shared Prompt Utilities

**Description:**
Create `backend/app/stock_analyser/analysis/prompts/base.py` with shared prompt formatting utilities.

**Implementation:**
- `format_stock_summary(stock_data: dict) -> str` — Format stock data into readable summary
- `format_financial_ratios(stock_data: dict) -> str` — Format ratios section
- `format_quarterly_results(stock_data: dict) -> str` — Format quarterly data
- `format_shareholding(stock_data: dict) -> str` — Format shareholding pattern
- `format_pros_cons(stock_data: dict) -> str` — Format pros and cons lists

**Acceptance Criteria:**
- [ ] File created at `backend/app/stock_analyser/analysis/prompts/base.py`
- [ ] All formatters handle missing data gracefully
- [ ] Output is readable and well-structured

---

### TASK-010: Create `stock_analyser/analysis/prompts/value_investing.py` — Value Investing Strategy

**Description:**
Create `backend/app/stock_analyser/analysis/prompts/value_investing.py` with value investing analysis strategy.

**Implementation:**
```python
class ValueInvestingStrategy(AnalysisStrategy):
    name = "value_investing"

    def get_system_prompt(self) -> str:
        return """You are a value investing analyst following the principles of Benjamin Graham and Warren Buffett.
        
Your task is to analyze stocks based on intrinsic value, financial health, and margin of safety.

Focus on:
- Financial strength (low debt, consistent earnings)
- Valuation metrics (P/E, P/B, EV/EBITDA relative to peers)
- Earnings quality and consistency
- Competitive moat and business quality
- Margin of safety (current price vs intrinsic value)

Output a JSON object with:
{
  "recommendation": "BUY" | "HOLD" | "SELL",
  "confidence": 0.0-1.0,
  "reasoning": "detailed analysis...",
  "key_factors": ["factor1", "factor2", ...],
  "risks": ["risk1", "risk2", ...]
}"""

    def get_analysis_prompt(self, stock_data: dict) -> str:
        summary = format_stock_summary(stock_data)
        return f"""Analyze this stock for value investing potential:

{summary}

Provide your analysis as a JSON object with the following fields:
- recommendation: "BUY", "HOLD", or "SELL"
- confidence: A number between 0.0 and 1.0
- reasoning: Detailed analysis (2-3 paragraphs)
- key_factors: List of 3-5 key factors influencing your decision
- risks: List of 2-3 risks to consider"""
```

**Acceptance Criteria:**
- [ ] File created at `backend/app/stock_analyser/analysis/prompts/value_investing.py`
- [ ] System prompt defines the analyst persona and output format
- [ ] Analysis prompt includes formatted stock data
- [ ] Prompt requests structured JSON output
- [ ] Class implements `AnalysisStrategy` interface

---

### TASK-011: Create `stock_analyser/analysis/prompts/momentum.py` — Momentum Strategy

**Description:**
Create `backend/app/stock_analyser/analysis/prompts/momentum.py` with momentum trading analysis strategy.

**Implementation:**
```python
class MomentumStrategy(AnalysisStrategy):
    name = "momentum"

    def get_system_prompt(self) -> str:
        return """You are a momentum trading analyst specializing in trend-following strategies.

Your task is to analyze stocks based on price momentum, volume, and technical indicators.

Focus on:
- Price trend direction and strength
- Volume patterns (increasing/decreasing)
- Relative strength vs market/sector
- Moving average alignment
- Breakout/breakdown patterns

Output a JSON object with:
{
  "recommendation": "BUY" | "HOLD" | "SELL",
  "confidence": 0.0-1.0,
  "reasoning": "detailed analysis...",
  "key_factors": ["factor1", "factor2", ...],
  "risks": ["risk1", "risk2", ...]
}"""

    def get_analysis_prompt(self, stock_data: dict) -> str:
        summary = format_stock_summary(stock_data)
        return f"""Analyze this stock for momentum trading potential:

{summary}

Provide your analysis as a JSON object with the following fields:
- recommendation: "BUY", "HOLD", or "SELL"
- confidence: A number between 0.0 and 1.0
- reasoning: Detailed analysis (2-3 paragraphs)
- key_factors: List of 3-5 key factors influencing your decision
- risks: List of 2-3 risks to consider"""
```

**Acceptance Criteria:**
- [ ] File created at `backend/app/stock_analyser/analysis/prompts/momentum.py`
- [ ] System prompt defines momentum analyst persona
- [ ] Analysis prompt includes formatted stock data
- [ ] Prompt requests structured JSON output
- [ ] Class implements `AnalysisStrategy` interface

---

### TASK-012: Create `stock_analyser/analysis/prompts/__init__.py` — Auto-Register Strategies

**Description:**
Create `backend/app/stock_analyser/analysis/prompts/__init__.py` with auto-registration.

**Implementation:**
```python
from app.stock_analyser.analysis.factory import AnalysisFactory
from app.stock_analyser.analysis.prompts.value_investing import ValueInvestingStrategy
from app.stock_analyser.analysis.prompts.momentum import MomentumStrategy

AnalysisFactory.register("value_investing", ValueInvestingStrategy)
AnalysisFactory.register("momentum", MomentumStrategy)
```

**Acceptance Criteria:**
- [ ] File created at `backend/app/stock_analyser/analysis/prompts/__init__.py`
- [ ] Both strategies are registered when module is imported
- [ ] No duplicate registrations

---

### TASK-013: Create `stock_analyser/analysis/__init__.py` — Public API Exports

**Description:**
Create `backend/app/stock_analyser/analysis/__init__.py` with module exports.

**Implementation:**
- Export `AnalysisFactory`
- Export `AnalysisStrategy` interface

**Acceptance Criteria:**
- [ ] File created at `backend/app/stock_analyser/analysis/__init__.py`
- [ ] All public symbols are importable from `app.stock_analyser.analysis`

---

## Phase 3: Task Integration

### TASK-014: Create `stock_analyser/tasks/analyze_stocks.py` — AnalyzeStocksTask

**Description:**
Create `backend/app/stock_analyser/tasks/analyze_stocks.py` with the new workflow task.

**Implementation:**
```python
from app.ai.factory import AgentFactory
from app.stock_analyser.analysis.factory import AnalysisFactory
from app.workflow.base_workflow_task import BaseWorkflowTask

class AnalyzeStocksTask(BaseWorkflowTask):
    name = "analyze_stocks"

    def __init__(self, strategy: str = "value_investing", agent: str = "stock_analysis") -> None:
        self.strategy = strategy
        self.agent = agent

    def run(self, ctx: BaseWorkflowContext) -> None:
        # 1. Read scrape_stocks output from context
        scrape_output = ctx.get_output("scrape_stocks")
        if not scrape_output:
            raise Exception("No scraped stocks found. Run ScrapeStocksTask first.")
        
        stocks = scrape_output["stocks"]
        index = scrape_output["index"]

        # 2. Get strategy from analysis factory
        strategy = AnalysisFactory.get(self.strategy)

        # 3. Get agent graph from ai factory (creates LLM with configured provider)
        graph = AgentFactory.get(self.agent)

        # 4. Analyze each stock
        analyses = []
        for stock in stocks:
            result = graph.run({
                "stock_data": stock,
                "system_prompt": strategy.get_system_prompt(),
                "analysis_prompt": strategy.get_analysis_prompt(stock),
            })
            
            if result.success:
                analyses.append(result.data)
            else:
                # Log error but continue with other stocks
                analyses.append({
                    "ticker": stock.get("ticker", "UNKNOWN"),
                    "error": result.error,
                })

        # 5. Set output on context
        ctx.set_output(self.name, {
            "index": index,
            "strategy": self.strategy,
            "analyses": analyses,
            "total_analyzed": len(analyses),
        })
```

**Acceptance Criteria:**
- [ ] File created at `backend/app/stock_analyser/tasks/analyze_stocks.py`
- [ ] Task reads from `ctx.get_output("scrape_stocks")`
- [ ] Task uses `AnalysisFactory` to get strategy
- [ ] Task uses `AgentFactory` to get agent graph (LLM created automatically)
- [ ] Task handles individual stock failures gracefully
- [ ] Task sets output via `ctx.set_output()`
- [ ] Task extends `BaseWorkflowTask`

---

### TASK-015: Update `stock_analyser/tasks/__init__.py` — Export AnalyzeStocksTask

**Description:**
Update `backend/app/stock_analyser/tasks/__init__.py` to export the new task.

**Implementation:**
```python
__all__ = ["ScrapeStocksTask", "AnalyzeStocksTask"]

def __getattr__(name: str):
    if name == "ScrapeStocksTask":
        from app.stock_analyser.tasks.scrape_stocks import ScrapeStocksTask
        return ScrapeStocksTask
    if name == "AnalyzeStocksTask":
        from app.stock_analyser.tasks.analyze_stocks import AnalyzeStocksTask
        return AnalyzeStocksTask
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

**Acceptance Criteria:**
- [ ] File updated at `backend/app/stock_analyser/tasks/__init__.py`
- [ ] `AnalyzeStocksTask` is importable from `app.stock_analyser.tasks`
- [ ] Lazy import pattern is maintained

---

### TASK-016: Update `stock_analyser/workflow.py` — Add Task + Strategy Input

**Description:**
Update `backend/app/stock_analyser/workflow.py` to include `AnalyzeStocksTask` and add strategy input field.

**Implementation:**
```python
from app.stock_analyser.tasks import AnalyzeStocksTask, ScrapeStocksTask
from app.workflow.base_workflow_config import BaseWorkflowConfig, InputField
from app.workflow.workflow_orchestrator_v1.workflow_registry import WORKFLOWS

STOCK_ANALYSER_WORKFLOW = BaseWorkflowConfig(
    name="stock_analyser",
    description="Scrapes and analyzes stocks for a given index",
    input_fields=[
        InputField(
            name="index",
            type="str",
            label="Stock Index",
            description="The stock index to analyze (e.g. NIFTY50, SENSEX)",
            required=True,
        ),
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

WORKFLOWS["stock_analyser"] = STOCK_ANALYSER_WORKFLOW
```

**Acceptance Criteria:**
- [ ] File updated at `backend/app/stock_analyser/workflow.py`
- [ ] `AnalyzeStocksTask` is in tasks list after `ScrapeStocksTask`
- [ ] `strategy` InputField is added with default value
- [ ] Workflow description is updated

---

## Phase 4: Configuration

### TASK-017: Update `backend/requirements.txt` — Add Dependencies

**Description:**
Update `backend/requirements.txt` with LangGraph and LangChain dependencies. LangGraph provides the workflow graph engine; LangChain provides provider-agnostic LLM integration.

**Implementation:**
Add:
```
langgraph>=0.2.0           # Graph workflow engine (StateGraph, nodes, edges)
langchain-core>=0.3.0      # Core LangChain (BaseChatModel, messages)
langchain-ollama>=0.3.0    # Ollama provider (default, local, free)
langchain-groq>=0.2.0      # Groq provider (free tier, fast)
langchain-openai>=0.2.0    # OpenAI provider (optional, paid)
```

**Acceptance Criteria:**
- [ ] File updated at `backend/requirements.txt`
- [ ] All dependencies are added with version constraints
- [ ] `langgraph` is included for graph workflow engine
- [ ] `langchain-core` is included for BaseChatModel interface
- [ ] At least one provider package is included (langchain-ollama by default)
- [ ] Run `pip install -r requirements.txt` to install

---

### TASK-018: Update `backend/app/core/config.py` — Add LLM Settings

**Description:**
Update `backend/app/core/config.py` with LLM provider configuration settings.

**Implementation:**
Add to `Settings` class:
```python
# LLM Provider Configuration
LLM_PROVIDER: str = "ollama"           # ollama, groq, openai, google_genai, etc.
LLM_MODEL: str = "llama3"              # Model name for the chosen provider
LLM_TEMPERATURE: float = 0.3           # Temperature for generation
LLM_TIMEOUT: int = 120                 # Timeout in seconds
```

**Acceptance Criteria:**
- [ ] File updated at `backend/app/core/config.py`
- [ ] Settings have sensible defaults (Ollama/llama3)
- [ ] Settings are loaded from environment variables
- [ ] `LLM_PROVIDER` supports all LangChain providers

---

### TASK-019: Update `backend/.env.example` — Add LLM Env Vars

**Description:**
Update `backend/.env.example` with LLM provider environment variables.

**Implementation:**
Add:
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

**Acceptance Criteria:**
- [ ] File updated at `backend/.env.example`
- [ ] Variables match `config.py` settings
- [ ] Default values are documented
- [ ] Provider-specific keys are commented out (optional)

---

## Task Dependencies

```
TASK-001 → TASK-002 → TASK-003 → TASK-004 → TASK-005 → TASK-006
                                                    ↓
TASK-007 → TASK-008 → TASK-009 → TASK-010 ─┐
                              TASK-011 ─────┤
                                            ↓
                                    TASK-012 → TASK-013
                                                    ↓
                              TASK-014 → TASK-015 → TASK-016
                                                    ↓
                              TASK-017 → TASK-018 → TASK-019
```

---

## Estimated Time

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1: AI Module (Foundation) | 6 tasks | 2-2.5 hours |
| Phase 2: Analysis Module (Strategy) | 7 tasks | 2-2.5 hours |
| Phase 3: Task Integration | 3 tasks | 1-1.5 hours |
| Phase 4: Configuration | 3 tasks | 30 mins |
| **Total** | **19 tasks** | **5.5-7 hours** |

---

## Notes

- **Provider flexibility**: Switch between Ollama (local, free), Groq (free tier, fast), OpenAI (paid), or any LangChain-supported provider by changing env vars
- **No per-provider code**: Single graph implementation works with all providers via `init_chat_model`
- **Ollama for development**: Default to Ollama for local development (free, unlimited, no API key)
- **Groq for testing**: Free tier with 30 RPM, very fast inference for quick tests
- **Inference time**: Expect 10-30 seconds per stock depending on model and provider
- **Batch processing**: Start with sequential processing; add parallelism later if needed
- **Error handling**: Individual stock failures should not fail entire workflow
