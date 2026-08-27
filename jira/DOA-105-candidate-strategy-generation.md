# DOA-105: Candidate strategy generation — where new strategies come from

- **Type:** Task (core loop stage)
- **Priority:** P0 within epic DOA-100 (M2)
- **Component:** backend
- **Depends on:** DOA-103 (StrategySpec is the genome), DOA-104 (fitness), DOA-109 (dedup via strategy_hash)

## Problem

Stage 1 and stage 5 of the loop: produce *new* `StrategySpec`s worth evaluating — initially from nothing (cold start), then from the scored population (improvement). The generator must respect the eval budget (DOA-106), never resubmit a hash already tried, and produce specs diverse enough that the guardrails (DOA-107) have something honest to select from.

## Approaches (these compose — the question is sequencing, not either/or)

### A. Seeded templates + parameter grid/random search
Hand-write ~6 archetype templates (value, quality, growth, dividend, momentum-of-fundamentals, low-leverage) with parameter ranges; generation = sample the ranges (random search, not full grid).

- ✅ Cold-start solution; instant, free, fully explainable candidates.
- ✅ Random search is embarrassingly effective per unit of complexity (well-documented vs grid).
- ✅ Templates encode domain sanity (no "rank by Face Value" nonsense), which raises the floor of the whole loop.
- ❌ Can never leave the template subspace — it optimizes, doesn't invent.
- ❌ Grid dimensionality discipline needed: ranges × steps explode fast; hence random sampling with a per-generation cap.

### B. Evolutionary / genetic algorithm over the DSL — *the core "improving" mechanism*
Population = top-K scored specs; operators: **mutate** (nudge a threshold ±20%, swap a metric within its category, reweight, change top_n), **crossover** (filters from parent 1, ranking from parent 2), **immigrate** (fresh Option-A randoms each generation to keep diversity).

- ✅ Directly implements "improving loop" — measurable generation-over-generation lift; no gradient/formal model needed; operators on a JSON DSL are ~200 lines.
- ✅ Naturally incremental and resumable (population lives in DB, DOA-109 lineage = parent hashes).
- ✅ Diversity controls (immigration, niche penalties) are simple knobs.
- ❌ **The overfitting engine.** Evolution optimizes the fitness function you give it, including its noise — DOA-107's validation-split fitness and complexity penalty are *mandatory* companions, not nice-to-haves.
- ❌ Hyperparameters of its own (population size, mutation rate) — pragmatic defaults (pop 40, top-10 survive, 25% immigration), tuned later by evidence.

### C. Bayesian optimization (Optuna/TPE) over template parameters
- ✅ More sample-efficient than random search *within a continuous template's parameters*; Optuna is a light, pinned dep.
- ✅ Good fit for "polish the champion": fine-tune the best archetype's thresholds with ~100 evals.
- ❌ Doesn't handle structural search (which metrics, how many filters) well — categorical/conditional spaces blunt its advantage.
- ❌ Another framework + storage to operate; overlaps heavily with what B already gives.

### D. LLM-proposed strategies (Claude generates/critiques specs)
Prompt with: DSL schema, metric catalog, current leaderboard + *failed* strategy summaries; ask for N novel specs (JSON only, validated by DOA-103 — the DSL makes this safe).

- ✅ Injects genuinely new *structure* (metric combinations, hypotheses) that A–C can't reach; can also write the "why this might work" rationale, which the UI wants anyway.
- ✅ Safety is already solved by the representation choice: worst case is invalid JSON → validation error.
- ❌ Ongoing API cost + a secret in the backend; nondeterminism complicates "reproduce generation 12".
- ❌ Plausible-sounding ≠ good: LLM candidates must enter the same evaluation gauntlet with zero privilege; risk of narrative bias (owner trusts the well-worded strategy over the better-scoring one — UI must lead with numbers).
- ❌ Failure modes need handling: retry-on-invalid, cap tokens, degrade gracefully to B when the API is down.

**Recommendation & sequencing:** **A ships with M2 day one (cold start), B ships with M2 as the improvement mechanism** — the epic's name is Option B. **C: defer** — adopt only if evidence shows random+evolution wastes budget on threshold-polishing (Optuna then slots in as a "refine champion" operator inside B). **D: behind a feature flag, off by default**, decided by the owner (epic open question #3); when enabled it contributes ≤20% of each generation's candidates so cost and narrative risk stay bounded.

## Design

- `app/asil/generation/` — `templates.py` (A), `operators.py` (B: mutate/crossover/immigrate), `llm_proposer.py` (D, flag-gated).
- `GenerateCandidatesTask(BaseWorkflowTask)`: input = generation number + budget; reads population from DOA-109; emits candidate specs (deduped by `strategy_hash` against *all* history, including failed — never re-test known losers unless data window changed).
- Determinism: A and B use a seeded RNG (seed = generation number) so a generation is reproducible; D's outputs are stored verbatim so reruns replay rather than re-ask.
- Every candidate records `origin` (`template|mutation|crossover|immigration|llm`) and parent hashes → the UI's lineage view and the PM's "which generator earns its budget?" analysis (see metrics).

## Metrics (to judge the generators themselves)

Per origin type, per month: candidates produced, % passing validation gates (DOA-107), % reaching leaderboard top-20. *A generator that never places in the top-20 gets its budget share cut — this table is the PM's steering wheel for the epic.*

## Steps of completion

1. Six archetype templates with documented ranges (finance rationale in docstrings).
2. Mutation/crossover/immigration operators + property tests (output always validates; mutation changes exactly one semantic field; crossover parents both recorded).
3. Dedup against `strategies` table by hash; collision metric logged.
4. `GenerateCandidatesTask` + seeded-RNG reproducibility test (same generation twice → same candidate set).
5. Flag-gated LLM proposer with schema-validated retry (≤2), token cap, and offline fallback to B.

## Acceptance criteria

- [ ] Generation 0 (cold start) produces ≥40 valid, distinct specs across ≥5 archetypes.
- [ ] Given a scored population, one generation step produces a candidate set with ≥30% mutations, ≥20% immigrants, 0 hash repeats vs history.
- [ ] Re-running generation N with the same population reproduces the identical candidate set (LLM contributions replayed from store).
- [ ] Origin metrics land in DOA-109 tables and are queryable per generation.
