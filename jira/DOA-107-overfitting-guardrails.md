# DOA-107: Overfitting & validity guardrails — the gates the loop cannot override

- **Type:** Task (core integrity)
- **Priority:** P0 within epic DOA-100 (M2) — *the epic's #1 risk lives here*
- **Component:** backend
- **Depends on:** DOA-104 (engine provides windows/metrics), consumed by DOA-105/106

## Problem

An improvement loop pointed at backtest performance is an **overfitting machine**: with enough candidates, something will look brilliant on any fixed dataset by luck alone (multiple testing). If DOA-107 is weak, ASIL becomes a generator of confident garbage and the product's one asset — trust in its numbers — is gone. These gates must be structurally outside the loop's control: the generator/selector can *read* gate results, never configure them.

## Approaches (composable layers — recommendation is which to stack, not one-of)

### A. Temporal splits: train / validation / embargoed holdout — *mandatory layer*
Fixed calendar split, e.g. train 2021-2023, validation 2024-2025, **holdout 2026→ touched only at promotion time**, with a 1-month embargo gap between windows (fundamentals autocorrelation bleeds across boundaries).

- ✅ The single highest-value defense; cheap (engine already takes windows); universally understood.
- ✅ Selection on validation (per DOA-106) means training-window luck doesn't propagate.
- ❌ One fixed split = validation itself gets overfit as thousands of candidates are filtered on it (mitigated by layer B and by rotating the split yearly).
- ❌ Short history (5y) makes windows small; regime luck (one bull run) dominates — must be stated on every report.

### B. Walk-forward evaluation (rolling re-fit windows)
Evaluate as a sequence: select on 2y, trade forward 6m, roll; concatenate the forward segments into the reported curve.

- ✅ Closest to how the strategy would actually be used; produces many small out-of-sample segments instead of one; robust to single-regime luck.
- ❌ ~4-6× eval cost; more machinery (window bookkeeping); with monthly rebalance and 5y data, forward segments are few — statistical power is limited anyway.
- **Stack decision:** applied only at **promotion time** (dozens of candidates), not per-candidate in the loop (hundreds) — cost lands where it buys the most.

### C. Multiple-testing corrections: Deflated Sharpe Ratio / trials-aware thresholds
Track N = total distinct strategies ever evaluated (we have exact counts via `strategy_hash` — a luxury real quant shops fake); require the champion's Sharpe to clear the expected-max-of-N-random-trials benchmark (Bailey & López de Prado's DSR).

- ✅ Directly answers "is this better than the best of N coin flips?" — the precise failure mode of a loop; our exact trial count makes it rigorous rather than estimated.
- ❌ Formula subtleties (non-normality adjustments) — implement the standard published form, document assumptions, don't invent.
- ❌ Brutal at small sample sizes: may reject everything for the first year. *That is honest and acceptable* — the UI shows "not yet distinguishable from luck" rather than lying.

### D. Complexity penalty & parameter-sensitivity checks
Fitness −= λ·complexity (from DOA-103); plus a robustness probe at promotion: jiggle each numeric threshold ±10% — if performance collapses, the strategy is a data artifact.

- ✅ Cheap; attacks overfitting at its source (excess degrees of freedom); sensitivity check is extremely convincing in the UI (a flat neighborhood = real signal).
- ❌ λ is a judgment call (start: λ such that one extra filter must earn +0.05 validation Sharpe); sensitivity adds ~10 evals per promotion candidate (fine).

### E. Statistical resampling (bootstrap CIs on Sharpe, subsampled universes)
- ✅ Confidence intervals instead of point estimates; universe-subsample stability ("does it survive with a random 80% of tickers?") catches single-stock-driven results.
- ❌ 100-1000× eval multiplier if applied naively; block-bootstrap needed for autocorrelated returns (easy to get wrong and derive false confidence).
- **Stack decision:** bootstrap CI on the *final monthly return series* (cheap — resamples the output, not re-runs the engine) at promotion time; universe-subsample (10 draws) at promotion time only.

**Recommended stack:** **A + D in the loop for every candidate** (cheap, always-on); **B + C + E at the promotion gate** (expensive, applied to the few that matter). All thresholds live in code owned by this ticket, in a module the generation/selection code imports but cannot parameterize (enforced by review + a test asserting gate config is not reachable from loop config).

## Hard gates (v1 numbers — tune with evidence, change only via PR)

| Gate | Applied | Threshold |
|---|---|---|
| Min track: portfolio never < 60% of `top_n` filled | per candidate | hard fail |
| Validation Sharpe > benchmark Sharpe | per candidate | hard fail |
| Max drawdown ≤ 1.25 × benchmark's | per candidate | hard fail |
| Turnover ≤ 40%/month avg | per candidate | hard fail (cost realism) |
| Deflated Sharpe (trials-aware) > 0 with 95% conf | promotion | hard fail |
| Walk-forward: ≥60% of forward segments beat benchmark | promotion | hard fail |
| Sensitivity: no single ±10% param jiggle flips sign of excess return | promotion | hard fail |
| Holdout window: positive excess return | promotion (once; result recorded forever) | hard fail |

**Holdout discipline:** a strategy gets exactly **one** holdout evaluation, ever (recorded in DOA-109 with a uniqueness constraint). Failing candidates cannot be "tweaked and retried" against the same holdout — the tweak makes a new strategy whose holdout burn is also recorded. When the holdout window itself becomes stale (≥30% of its span used by promotions), it rolls forward and the event is logged — this is the mechanism that keeps the loop honest for years.

## Report honesty requirements (consumed by DOA-110)

Every displayed result must carry: data window + snapshot-history depth, trials count N to date, survivorship-bias disclaimer (universe = current constituents until DOA-102's open question is revisited), costs assumed, and the gate checklist with pass/fail. **No metric renders without its caveats block.** This is product policy, not a nice-to-have.

## Steps of completion

1. `app/asil/gates/` — split definitions, per-candidate gates, promotion gates; config frozen in code (not Settings/env — deliberate friction).
2. Deflated Sharpe implementation with unit tests against published worked examples.
3. Trials counter wired to DOA-109 (`SELECT count(*) FROM strategies` scoped per holdout epoch).
4. Holdout burn registry with DB uniqueness constraint (`strategy_hash, holdout_epoch`).
5. Sensitivity prober (±10% jiggle harness reusing DOA-104 engine).
6. Adversarial test: feed 500 random strategies over real data → **zero** must pass the promotion stack (this test failing means the gates leak).

## Acceptance criteria

- [ ] The 500-random-strategies adversarial test passes (0 promotions).
- [ ] A deliberately look-ahead-contaminated strategy (fixture from DOA-104's tripwire) fails validation gates.
- [ ] Attempting a second holdout eval for the same hash+epoch raises a DB constraint error.
- [ ] Gate thresholds are not importable/settable from `app/asil/generation/` or Settings (test asserts import graph).
- [ ] Every `EvaluationResult` rendered by the API includes the caveats block.
