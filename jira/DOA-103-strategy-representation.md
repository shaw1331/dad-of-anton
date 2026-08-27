# DOA-103: Strategy representation — the contract every other ASIL ticket depends on

- **Type:** Task (design + implementation)
- **Priority:** P0 within epic DOA-100 (M1)
- **Component:** backend
- **Depends on:** DOA-101/102 (defines what fields a strategy may reference)

## Problem

"Strategy" must be a first-class, storable, diffable, *machine-generable* artifact. The representation decides everything downstream: what the generator (DOA-105) can mutate, what the evaluator (DOA-104) can execute, what the UI (DOA-110) can render, and how safely third-party/LLM-produced strategies can run. This is the highest-leverage design decision in the epic — choose wrong and the loop is either too weak to find anything or too dangerous to automate.

## Approaches

### A. Declarative JSON DSL (filters + weighted rank + portfolio params) — *recommended*

```json
{
  "universe": ["LMIDCAP250"],
  "filters": [
    {"metric": "ROCE", "op": ">", "value": 15},
    {"metric": "Promoter Holding", "op": ">=", "value": 50}
  ],
  "ranking": [
    {"metric": "ROCE", "direction": "desc", "weight": 0.6},
    {"metric": "Net Profit (Latest Qtr)", "transform": "yoy_growth", "direction": "desc", "weight": 0.4}
  ],
  "portfolio": {"top_n": 15, "weighting": "equal", "rebalance": "monthly"}
}
```

- ✅ **Safe by construction** — no code execution; an LLM or mutation operator can emit arbitrary JSON and the worst case is a validation error. This is what makes full automation (M2) tenable.
- ✅ Trivially mutable (change a threshold, swap a metric, reweight) — genetic operators become dict edits.
- ✅ Storable/diffable/renderable: Pydantic model → JSONB column → UI form, one schema everywhere.
- ✅ Enumerable search space → the guardrails ticket (DOA-107) can *count* hypotheses tested, which multiple-testing corrections require.
- ❌ Expressiveness ceiling: no cross-sectional logic beyond what the DSL encodes (e.g. "sector-neutral", "if market drawdown > X, go to cash" need explicit DSL extensions).
- ❌ DSL design debt: every new capability = schema version bump + evaluator support (mitigate with `schema_version` field from day one).

### B. Python plugin classes (`BaseStrategy.select(date, data) -> portfolio`)
- ✅ Unlimited expressiveness; comfortable for a human quant.
- ✅ No DSL to design; the evaluator just calls a method.
- ❌ **Auto-generation becomes code generation** — mutating Python safely is hard; LLM-written code executing in-process is an RCE-by-design (sandboxing = its own project).
- ❌ Not diffable/renderable for the UI beyond "here's source code"; lineage and dedup (has the loop tried this before?) become string comparisons.
- ❌ A buggy strategy can corrupt the process (infinite loop inside the orchestrator's event loop, memory blowup).

### C. SQL/expression strings (strategy = a SQL query over the snapshot tables)
- ✅ Powerful filtering/ranking for free; Postgres does the heavy lifting.
- ❌ SQL injection surface *by design* if generated; sandboxing SQL semantics (cost limits, no writes) is subtle.
- ❌ Mutation/crossover on SQL text is brittle; equality/dedup nearly impossible.
- ❌ Backtest loop needs per-date execution → N queries per evaluation, slow and chatty.

### D. Hybrid: DSL core (A) + named, hand-written Python "factor transforms" registry
Transforms like `yoy_growth`, `rank_zscore`, `sector_relative` are vetted Python functions the DSL can *reference by name* but never define.

- ✅ Keeps A's safety while punching through its expressiveness ceiling exactly where needed.
- ✅ New power = a human PR (reviewed code), not a loop mutation — right trust boundary.
- ❌ Two-tier system to document; transform registry becomes a bottleneck if the loop "wants" new transforms often.

**Recommendation:** **A now, formalized as D** (the `transform` field in the example is already the registry hook). B is rejected for automation safety; C rejected for injection + dedup. Revisit B only for human-authored "reference strategies" used to benchmark the loop.

## Design details (decided here, consumed by 104/105/109)

1. **Pydantic model `StrategySpec`** (`app/asil/strategy_spec.py`) with `schema_version: int = 1`; strict validation: metrics must exist in a `KNOWN_METRICS` enum derived from `config.py` labels; weights sum to 1 ± ε; `top_n` ∈ [5, 50]; ops whitelist `> >= < <= between`.
2. **Canonical hash**: `strategy_hash = sha256(canonical_json(spec))` — dedup key so the loop never re-evaluates an identical spec (stored in DOA-109's tables).
3. **Complexity score**: `n_filters + n_rank_terms` — consumed by DOA-107 as an overfitting penalty and by DOA-105 as a mutation budget.
4. **Human-readable rendering**: deterministic English summary generated from the spec (for UI and audit) — part of this ticket, not the UI's job.

## Steps of completion

1. Write an ADR (docs/adr/) capturing the A-vs-B-vs-C decision above — future contributors will ask.
2. Implement `StrategySpec` + validation + canonical hash + complexity + `to_english()`; 100% branch coverage on validation (this is the safety boundary).
3. Implement the transform registry with the two launch transforms: `yoy_growth`, `identity`; document the PR process for adding one.
4. Fixture pack: 5 realistic specs (value, quality, growth, dividend, garbage-that-must-fail-validation) used by DOA-104/105 tests.

## Acceptance criteria

- [ ] Any dict from an untrusted source either becomes a valid `StrategySpec` or raises a structured validation error — no other outcome (fuzz test with 1k random dicts).
- [ ] Same spec, different key order / float formatting → identical `strategy_hash`.
- [ ] `to_english()` of the value fixture reads as a correct sentence (golden test).
- [ ] Referencing an unknown metric or transform is a validation error naming the field.
