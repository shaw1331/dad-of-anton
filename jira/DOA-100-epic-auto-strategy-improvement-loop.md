# DOA-100 [EPIC]: Auto Strategy Improvement Loop (ASIL)

- **Type:** Epic / PRD
- **Priority:** P0 (product direction)
- **Component:** all (scraper → backend → frontend)
- **Child tickets:** DOA-101 … DOA-111
- **Status:** Proposed — needs owner sign-off on scope cuts in §6

## 1. Vision

Today the repo has three disconnected pieces: a scraper that dumps screener.in fundamentals to CSVs, a generic workflow orchestrator that runs toy tasks, and a frontend that shows a health check. ASIL connects them into one product:

> **A system that continuously invents, evaluates, and improves stock-screening strategies over Indian equities — automatically — and surfaces a ranked, evidence-backed leaderboard a human can act on.**

The "loop" is the product. One iteration ("generation") looks like:

```
        ┌──────────────────────────────────────────────────────────┐
        │                                                          ▼
   [1] GENERATE candidates ──▶ [2] EVALUATE (backtest) ──▶ [3] SCORE & RANK
        ▲                                                          │
        │                                                          ▼
   [5] MUTATE / REFINE  ◀──── [4] SELECT survivors + record learnings
```

Each numbered stage is a workflow task on the existing orchestrator; a generation is a workflow run; the loop is generations chained over time. Humans never write strategies by hand after M1 — they seed, approve, and kill.

## 2. Why now / why us

- The scraper already collects the exact factor inputs (P/E, ROCE, ROE, promoter holding, quarterly sales/profit growth…) that classical factor strategies are built from.
- The orchestrator was built for multi-step background jobs and is idle — this is its first real workload.
- Strategy research done manually is slow and biased toward ideas someone already had; a loop explores the space systematically and keeps an audit trail.

## 3. What a "strategy" is (v1 scope)

A **ranking + filter rule set over fundamentals, rebalanced periodically**. Example: *"Universe = LMIDCAP250; filter ROCE > 15 and Promoter Holding > 50; rank by composite(0.6·ROCE_rank + 0.4·earnings_growth_rank); hold top 15; rebalance monthly; equal weight."* Explicitly **out of scope for v1**: intraday/technical signals, derivatives, live order execution, real money. ASIL ends at a recommended portfolio + evidence.

## 4. Users & jobs-to-be-done

| User | Job |
|---|---|
| Owner/investor (primary, N=1 today) | "Show me strategies that would have worked, with honest statistics, and keep making them better without my time." |
| Reviewer | "Let me see *why* a strategy scores well, its lineage, and veto it." |
| The loop itself (system user) | "Give me clean data, a strategy contract, a scoring function, and a budget." |

## 5. Success metrics

- **North star:** count of strategies that pass the out-of-sample holdout gate (DOA-107) per month.
- Loop throughput: candidate strategies evaluated per day (target ≥ 200 after M2).
- Data freshness: scrape → queryable in Supabase ≤ 24 h (DOA-101).
- Integrity: 0 evaluations using data newer than the simulated decision date (look-ahead bias, DOA-104/107).
- Adoption: owner reviews leaderboard ≥ 1×/week (DOA-110 analytics).

## 6. Milestones (scope cuts happen here, not inside child tickets)

| Milestone | Delivers | Child tickets |
|---|---|---|
| **M0 — Data foundation** | Scraped fundamentals + prices in Supabase, point-in-time correct | DOA-101, DOA-102 |
| **M1 — Manual strategy, honest backtest** | Define one strategy in the chosen representation, evaluate it end-to-end, see result in DB | DOA-103, DOA-104, DOA-109, DOA-108 (data passing only) |
| **M2 — The loop** | Generate → evaluate → select → mutate runs unattended on a schedule with budget caps | DOA-105, DOA-106, DOA-107, DOA-108 (scheduling) |
| **M3 — Product surface** | Leaderboard UI, strategy detail, approve/kill, audit | DOA-110, DOA-111 |

Dependency on the existing backlog: the orchestrator hardening tickets **DOA-005, DOA-006, DOA-014 are prerequisites for M1** (the loop cannot run on an orchestrator that blocks the event loop, strands runs, and can't parameterize tasks). DOA-001/009 (config + RLS) are prerequisites for storing anything valuable.

## 7. Top-level architecture decision — where does the loop live?

Considered three shapes; child tickets assume **Option B**.

**Option A — one giant long-running workflow run** (a single `run_workflow` that loops for days).
- ✅ Zero new infrastructure; trivially matches current orchestrator.
- ❌ A deploy/crash kills the whole loop (BackgroundTasks are in-process, not persistent); one run row = useless progress granularity; impossible to parallelize evaluations; violates the orchestrator's own model (bounded task list).

**Option B — one workflow run per generation, chained by a scheduler** *(recommended)*.
- ✅ Each generation is small, resumable, observable with the existing `workflow_runs` UI-to-be; crash loses at most one generation; parallel evaluation possible inside a generation (DOA-108); budget caps are natural (N generations/day).
- ❌ Needs a scheduler (DOA-108) and generation state handed between runs via DB (DOA-109) — two new platform features.

**Option C — separate dedicated service (Celery/Temporal/Prefect) for the loop.**
- ✅ Industrial-strength retries, scheduling, distributed workers off the shelf.
- ❌ Abandons the in-house orchestrator this repo just built (sunk but real learning value); heavy ops for a single-user product; Redis/queue infra contradicts the plan doc's explicit "no Redis/Celery" decision. Revisit only if Option B hits scale limits (>10k evals/day).

## 8. Risks (owned at epic level)

1. **Overfitting is the product-killer.** A loop that optimizes backtest Sharpe will happily produce garbage that looks brilliant. Mitigation is a *dedicated ticket with teeth* (DOA-107) whose gates are non-overridable by the loop itself.
2. **Data quality ceiling.** Screener snapshots start "now"; deep history needs DOA-102's price source and accepting fundamentals history limits (§ in DOA-101). The loop's claims must state their data window honestly.
3. **screener.in ToS / rate limits.** Scraper stays polite (existing delays) and volume grows only with index count, not with loop iterations (loop reads our DB, never screener).
4. **Cost/runaway compute.** Budgets enforced by DOA-106/111 (max evals per day, hard kill switch).
5. **This is not investment advice.** Product copy and UI must frame outputs as research (DOA-110/111).

## 9. Open questions for the owner

1. Confirm v1 asset universe = the three configured indexes only?
2. Rebalance frequencies to support in v1 (proposal: monthly only)?
3. Is LLM-based strategy generation (DOA-105 Option D) in or out for M2? It changes cost profile materially.
4. Any real-money follow-on planned? (Affects how strict DOA-111 must be from day one.)
