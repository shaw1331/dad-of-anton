# Token Tracking Plan

## Goal

Show LLM token usage per task card on `/workflows/[runId]`.

Acceptance: `analyze_stocks` and `analyze_news` task cards show
`Tokens: {in} in / {out} out | {model} | {duration_s}s` when
`task.output.token_usage` is present. Other task cards unchanged.
No DB migration. No `factory.py` edits.

## Stop condition

Work is done when all of these are true:

- Files listed below exist/match the contracts
- `tests/test_usage.py` four cases pass
- `test_analyze_news_disabled` still asserts exact
  `{"analyses": {}, "total_analyzed": 0}`
- Run-detail card renders `token_usage` after timestamps
- `git diff` does **not** include `factory.py` or any SQL migration

If this is already implemented on `feat/token-tracking`, **do not rewrite**.
Diff against this plan, fix gaps, stop.

## Where to work

- Branch: `feat/token-tracking`
- Worktree (if present): `../dad-of-anton-token-tracking`
- Do **not** implement on `main` or `feat/trades-dashboard`
- Backend and frontend are both in scope; commit them **separately**
  (`feat(backend): ...` then `feat(frontend): ...`) per `AGENTS.md`

That branch already has `AgentAudit` (model, latency, prompts, citations).
Extend it. Do not add a second tracking system.

## Why not a callback handler

Do **not** create `TokenTrackingHandler` or `get_last()`.

- Class-level last-result dict races across concurrent workflow runs
- `with_structured_output().invoke()` returns a Pydantic model, not `LLMResult`
- `llm.callbacks = [...]` often does not follow the structured wrapper

## Approach

1. Same invoke that parses structured output also returns token counts
2. Store counts on each `AgentAudit`
3. Roll audits into `task.output.token_usage` (existing JSON column, no migration)
4. Frontend reads that object on the task card

Use `with_structured_output(..., include_raw=True)` and read
`AIMessage.usage_metadata`. Fallback: `response_metadata["token_usage"]`
or `response_metadata["usage"]`. Missing data is `0`.

Ollama often omits usage. Card may show `0 in / 0 out`. That is OK.
Do not estimate tokens.

## Data shape (`task.output.token_usage`)

```json
{
  "input_tokens": 142,
  "output_tokens": 67,
  "total_tokens": 209,
  "model": "llama3",
  "duration_s": 1.2,
  "calls": 3
}
```

- `duration_s` = `round(sum(audit.latency_ms) / 1000, 1)`
- `calls` = number of audits rolled up
- `model` = first audit's `model`, or `null` if no audits
- Empty audit list still returns zeros + `model: null` + `calls: 0`

## Backend data flow

```
AgentFactory.get()                # unchanged; plain LLM, no callbacks
invoke_structured(...)
  include_raw=True
  parsed + tokens_from_message(raw)
build_audit(..., input_tokens, output_tokens, total_tokens)
  AgentResult.audits
task.run()
  collect AgentAudit objects from each graph.run()
  ctx.set_output(..., token_usage=rollup_token_usage(audits))
GET /workflows/runs/{id}
  task.output.token_usage
```

---

## File contracts

### 1. Create `backend/app/ai/usage.py`

```python
def tokens_from_message(message: Any) -> tuple[int, int, int]:
    # 1) message.usage_metadata
    #    keys: input_tokens, output_tokens, total_tokens
    # 2) else message.response_metadata["token_usage"] or ["usage"]
    #    keys: input_tokens/prompt_tokens, output_tokens/completion_tokens
    # 3) total_tokens = meta.total_tokens or input+output
    # 4) missing message or missing keys → (0, 0, 0)
    # return (input_tokens, output_tokens, total_tokens) as ints

def invoke_structured(
    llm: BaseChatModel,
    output_model: type[BaseModel],
    messages: list,
) -> tuple[BaseModel | None, tuple[int, int, int]]:
    bound = llm.with_structured_output(output_model, include_raw=True)
    out = bound.invoke(messages)
    if isinstance(out, dict):
        parsed = out.get("parsed")
        return parsed, tokens_from_message(out.get("raw"))
    if isinstance(out, output_model):
        return out, (0, 0, 0)
    return None, (0, 0, 0)

def rollup_token_usage(audits: list[AgentAudit]) -> dict[str, Any]:
    # empty → {input_tokens:0, output_tokens:0, total_tokens:0,
    #           model: None, duration_s: 0.0, calls: 0}
    # else sum token fields + latency_ms, model=audits[0].model
```

Do not import this from `factory.py`.

### 2. Create `backend/tests/test_usage.py`

No live LLM. Use `types.SimpleNamespace`.

| Test | Input | Expected |
|---|---|---|
| usage_metadata | `{input_tokens:10, output_tokens:4, total_tokens:14}` | `(10, 4, 14)` |
| openai fallback | `usage_metadata=None`, `response_metadata.token_usage={prompt_tokens:8, completion_tokens:2}` | `(8, 2, 10)` |
| missing | empty namespace | `(0, 0, 0)` |
| rollup | two `AgentAudit`s: (100/20/120, 1200ms) + (50/10/60, 800ms), model `llama3` | `{input_tokens:150, output_tokens:30, total_tokens:180, model:"llama3", duration_s:2.0, calls:2}` |

`AgentAudit` construction needs the existing required fields
(`agent_name`, `provider`, `model`, `temperature`, `prompt_version`,
`schema_version`, `latency_ms`, `system_prompt`, `analysis_prompt`)
plus the three token fields.

Run (from `backend/`, venv python):

```
python -m pytest tests/test_usage.py -q
```

If pytest is missing:

```
python -c "from tests.test_usage import *; test_tokens_from_usage_metadata(); test_tokens_from_openai_style_response_metadata(); test_tokens_missing_are_zero(); test_rollup_sums_audits(); print('ok')"
```

Set `PYTHONPATH` to the `backend/` directory.

### 3. Modify `backend/app/ai/models.py` — class `AgentAudit`

Add after `latency_ms: int`:

```python
input_tokens: int = 0
output_tokens: int = 0
total_tokens: int = 0
```

Keep `retry_count` and the rest as they are.

### 4. Modify `backend/app/ai/audit.py` — `build_audit`

Add kwargs with defaults `0`: `input_tokens`, `output_tokens`, `total_tokens`.
Pass them through to `AgentAudit(...)`.
Do not change citation extraction.

### 5. Modify `backend/app/ai/graph.py` — `StockAnalysisAgent`

`StockAnalysisState` TypedDict: add `input_tokens: int`, `output_tokens: int`,
`total_tokens: int`.

`initial_state` in `run()`: those three keys start at `0`.

In `analyze_node`, delete the local `structured_llm = self.llm.with_structured_output(...)`.
Replace invoke with:

```python
parsed, (input_tokens, output_tokens, total_tokens) = invoke_structured(
    self.llm, self.output_model, messages
)
return {
    "raw_response": parsed.model_dump_json() if parsed else "",
    "parsed_analysis": parsed,
    "input_tokens": input_tokens,
    "output_tokens": output_tokens,
    "total_tokens": total_tokens,
}
```

Success `build_audit` in `run()`: pass
`result.get("input_tokens", 0)` and the out/total keys.
Exception path: leave tokens at default 0.

### 6. Modify `backend/app/ai/news_agent.py` — `NewsAnalysisAgent`

Change `_analyze_single` to return `tuple[dict, tuple[int, int, int]]`.

```python
parsed, tokens = invoke_structured(self.llm, AnalyzedNewsArticle, messages)
if parsed is None:
    raise ValueError("Failed to parse news analysis")
return parsed.model_dump(), tokens
```

Caller:

```python
result, (input_tokens, output_tokens, total_tokens) = self._analyze_single(...)
# success build_audit gets those three kwargs
```

Failed article `except`: `build_audit` without token kwargs (zeros).
Do not abort the whole ticker loop.

### 7. Modify `backend/app/stock_analyser/tasks/analyze_stocks.py`

```python
audits = []  # list[AgentAudit]
# inside the existing try, after graph.run():
audits.extend(result.audits)
# keep per-analysis "audits": [audit.model_dump() for audit in result.audits]
ctx.set_output(self.name, {
    ...,  # existing keys: index, strategy, analyses, total_analyzed
    "token_usage": rollup_token_usage(audits),
})
```

Always set `token_usage` on the success path of this task (even if all
invokes failed and audits is empty). Outer `except Exception` per stock
does not add audits; that is OK.

### 8. Modify `backend/app/stock_analyser/tasks/analyze_news.py`

Keep dumped dict audits on output (`audits: list[dict]`).
Also keep `audit_models: list[AgentAudit]` for rollup.

```python
audit_models.extend(result.audits)
audits.extend(audit.model_dump() for audit in result.audits)
# set_output:
"audits": audits,
"token_usage": rollup_token_usage(audit_models),
```

**Do not** add `token_usage` when `enable_news` is false.

Existing test must still pass:

```python
assert output == {"analyses": {}, "total_analyzed": 0}
```

### 9. Modify `frontend/app/components/WorkflowRunDetail.tsx`

Insert **after** the `completed_at` paragraph, **before** `task.error`:

```tsx
{task.output?.token_usage && (
  <p className="text-xs text-muted-foreground">
    Tokens: {task.output.token_usage.input_tokens} in /{" "}
    {task.output.token_usage.output_tokens} out
    {task.output.token_usage.model
      ? ` | ${task.output.token_usage.model}`
      : ""}
    {task.output.token_usage.duration_s != null
      ? ` | ${task.output.token_usage.duration_s}s`
      : ""}
  </p>
)}
```

No new TypeScript type required (`output` is already `Record<string, any>`).
Do not restyle the card. Do not show a tokens line when `token_usage` is absent
(scrape tasks).

---

## Do not touch

- `backend/app/ai/factory.py`
- Any file under `backend/supabase/migrations/`
- Scrape tasks (`scrape_stocks`, `scrape_news`, `scrape_tradingview`, …)
- Trades page / workflows copy from other branches
- Estimating tokens, charts, DB columns, per-invoke UI

## Verify

1. `tests/test_usage.py` — four cases pass
2. `tests/test_analyze_news_task.py::test_analyze_news_disabled` — exact equality
3. `python -c "from app.ai.graph import StockAnalysisAgent; from app.ai.news_agent import NewsAnalysisAgent; from app.stock_analyser.tasks.analyze_stocks import AnalyzeStocksTask; from app.stock_analyser.tasks.analyze_news import AnalyzeNewsTask"`
   from `backend/` with `PYTHONPATH=.`
4. UI: open a completed run that includes `analyze_stocks` or `analyze_news`.
   Token line under timestamps. Scrape cards have no token line.

No live LLM test is required for this slice.

## Out of scope

- Token usage DB column
- Historical analytics / charts
- Per-invoke UI (audits already hold per-call counts; card shows the task total)
- Estimating tokens when the provider sends none
