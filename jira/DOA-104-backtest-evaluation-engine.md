# DOA-104: Strategy evaluation engine — honest, fast, deterministic backtests

- **Type:** Task (core engine)
- **Priority:** P0 within epic DOA-100 (M1)
- **Component:** backend
- **Depends on:** DOA-101 (fundamentals PIT), DOA-102 (prices), DOA-103 (StrategySpec)

## Problem

The loop's fitness function. Given a `StrategySpec` and a date window, simulate the strategy's portfolio decisions using **only data knowable at each decision date**, and return a scored result. It must be: *honest* (no look-ahead, costs modeled), *fast* (hundreds of evals/day on one box), and *deterministic* (same inputs → bit-identical outputs, or the loop's selection stage is noise).

## Approaches

### A. Build a minimal vectorized rank-rebalance simulator (pandas/numpy) — *recommended*
Our strategies are exactly one shape (filter → rank → top-N → periodic rebalance). Simulate that shape and nothing else: load PIT fundamentals + prices into DataFrames, loop over rebalance dates (≈60 for 5y monthly), vectorize within each date.

- ✅ Small (est. 300–500 lines), fully understood, auditable — when a number looks wrong we can read every line that produced it. For a product whose whole value is *trustworthy* numbers, this matters more than features.
- ✅ Fast: 60 rebalance dates × 350 tickers is trivial; easily <1 s per eval → thousands/day.
- ✅ Zero new heavyweight deps (pandas+numpy only); fits the "no extra infra" ethos of the repo.
- ❌ We own every correctness bug (adjustment handling, calendar alignment, cost model) — mitigated by the validation harness below.
- ❌ If v2 strategies need path-dependent logic (stop-losses, volatility targeting), the simple engine grows or gets replaced.

### B. Adopt a backtesting library (vectorbt / backtrader / bt / zipline-reloaded)
- ✅ Cost models, calendars, metrics, plotting for free; battle-tested against classes of bugs we'd otherwise rediscover.
- ✅ vectorbt in particular is extremely fast for parameter sweeps.
- ❌ All are signal/price-series-first; **fundamentals-ranking rebalance portfolios are an awkward fit** — we'd write nearly as much adapter code as Option A's whole engine.
- ❌ Heavy deps (numba etc.), library-specific mental model, some are semi-maintained; debugging *their* internals when a number looks off is worse than debugging ours.
- ❌ Determinism and PIT discipline are still *our* responsibility — the library doesn't know our data model, so the hard part isn't outsourced anyway.

### C. SQL-native backtest (do rank/filter per date in Postgres, Python only aggregates)
- ✅ No data shipping; Supabase does the joins.
- ❌ 60+ round-trips per evaluation × hundreds of evals = hammering the shared DB the API also uses; latency-bound, not compute-bound.
- ❌ Transforms (yoy_growth etc., DOA-103 registry) would need SQL twins — two implementations to keep equal.

**Recommendation:** **A**, with the explicit exit criterion: if v2 requires path-dependent strategies, evaluate vectorbt *then* with real requirements. C rejected (wrong bottleneck). The engine loads snapshots once per generation and evaluates many specs against the same in-memory panel — the loop's dominant cost becomes candidate count, not I/O.

## Non-negotiable correctness rules (each is a test)

1. **PIT rule:** a decision at rebalance date D uses the latest snapshot with `as_of < D` (strictly before) and trades at the first available close ≥ D. Fundamentals `as_of` newer than D must be invisible even if loaded.
2. **Universe rule:** candidates at D = index constituents as of the latest membership snapshot before D.
3. **Missing data rule:** ticker missing a filtered/ranked metric at D is *excluded*, never imputed silently; exclusion counts are reported per rebalance.
4. **Cost model:** flat default 0.25% per side (configurable) + optional slippage bps; **turnover is always reported** so cost sensitivity is visible.
5. **Determinism:** ties in ranking broken by ticker lexicographic order; no RNG anywhere; result includes an input-data fingerprint (max `as_of`, price row count) so identical evals are provably identical.

## Output contract (`EvaluationResult`, stored by DOA-109)

Per evaluation: window, spec hash, data fingerprint; equity curve (monthly); **metrics:** CAGR, volatility, Sharpe, Sortino, max drawdown, Calmar, avg turnover, win rate vs benchmark, benchmark-relative CAGR (benchmark = equal-weight universe — computed by the same engine, same costs, so comparisons are apples-to-apples); **diagnostics:** avg portfolio size, exclusion counts, months with <top_n candidates.

## Validation harness (how we trust it — part of this ticket, not optional)

- **Golden test:** hand-compute a 3-ticker, 3-month toy case in a spreadsheet; engine must match to the rupee.
- **Null strategy test:** rank by a random-but-fixed key → benchmark-like performance; consistent large outperformance = engine bug.
- **Cost monotonicity:** raising costs never raises net CAGR.
- **Look-ahead tripwire:** shift all fundamentals `as_of` forward 1 year; a previously good strategy must degrade toward null — if not, PIT is leaking.

## Steps of completion

1. `app/asil/engine/` — data loader (panel builder), simulator, metrics, benchmark; pure functions, no DB writes.
2. `EvaluationResult` Pydantic model + persistence via DOA-109 repo.
3. `EvaluateStrategyTask` workflow task (parameterized with spec hash + window) for orchestrator integration.
4. Validation harness above as pytest suite.
5. Performance check: 100 evaluations of the fixture specs over 5y in <2 min on the dev laptop.

## Acceptance criteria

- [ ] All four validation-harness tests pass.
- [ ] Two runs of the same eval produce byte-identical `EvaluationResult` JSON.
- [ ] Benchmark and strategies share one code path (grep: no separate benchmark simulator).
- [ ] Every metric in the output contract is populated for the value-strategy fixture over 2021-2026.
