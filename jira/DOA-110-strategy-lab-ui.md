# DOA-110: Strategy Lab UI — leaderboard, strategy detail, loop monitor, review queue

- **Type:** Task (product surface)
- **Priority:** P1 within epic DOA-100 (M3)
- **Component:** frontend, backend/api
- **Depends on:** DOA-109 (queries), DOA-107 (caveats/gate data), DOA-111 (actions/auth), DOA-008 (env-based API URL)

## Problem

The loop's output is invisible today. The product needs a surface where the owner can (a) trust-check a strategy in under a minute, (b) watch the loop work, and (c) act — approve, reject, kill. Per the epic's honesty principle: **numbers never render without their caveats**, and LLM-origin narratives never render above measured performance.

## Scope decision — what the UI is (and isn't) in v1

Considered three product shapes:

**A. Read-only dashboard (leaderboard + detail), actions via API/CLI only.**
- ✅ Smallest build; zero write-path auth to get wrong on the web surface.
- ❌ The review queue (DOA-111's human gate) is the *product moment* — hiding it in curl kills adoption; metric "owner reviews weekly" (DOA-100 §5) would fail.

**B. Dashboard + actions (approve/reject/kill, pause loop) — *recommended*.**
- ✅ Completes the human-in-the-loop; single-user auth is tractable (DOA-111 token).
- ❌ Write endpoints on the web surface → auth becomes a real requirement (accepted; DOA-111 owns it).

**C. Full strategy editor (compose specs in a form, run ad-hoc backtests).**
- ✅ Power-user delight; helps seed the population manually.
- ❌ Doubles the surface (form validation mirroring DOA-103, ad-hoc eval queue, result polling); the loop is supposed to write strategies, not the human. **Defer to v1.1** — a "clone spec JSON to clipboard + trigger manual eval" escape hatch covers 80% of the need meanwhile.

## Pages (v1)

1. **Leaderboard `/strategies`** — ranked by validation fitness; columns: rank, english summary (truncated), origin badge, validation Sharpe (with bootstrap CI once available), excess CAGR, max DD, turnover, gate-status chips (✅/❌ per hard gate), status (survivor/candidate/approved). Filters: status, origin, window. Sort is server-side (DOA-109 `leaderboard()`).
2. **Strategy detail `/strategies/[hash]`** — spec rendered as the deterministic English summary + raw JSON toggle; equity curve vs benchmark (train/val shaded differently, holdout marked if burned); **caveats block always visible above the fold** (window, trials N, survivorship note, costs — verbatim from DOA-107's report contract); gate checklist with actual values vs thresholds; sensitivity heat-strip (±10% jiggle results); lineage tree (parents/children, clickable); status history with actors.
3. **Loop monitor `/loop`** — generations table (id, time, candidates, evals spent, best fitness sparkline over generations, status incl. `failed:budget`, stagnation flag banner); current schedule (from DOA-108 `schedules`) with **pause/resume toggle**; live view of the running generation via existing `GET /workflows/runs/{id}` polling.
4. **Review queue `/review`** — strategies in `candidate_for_review`; side-by-side compare (up to 3); approve/reject with mandatory reason (writes `strategy_status` via DOA-111 endpoints); kill switch for `approved` strategies.

## Approach notes (frontend)

- **Charting:** one small pinned lib (e.g. `recharts`) vs hand-rolled SVG. Recharts: ✅ equity curves/sparklines in hours, ❌ +1 dep. Hand-rolled: inverse. *Decision: recharts, pinned exact version (org rule: no floating deps).*
- **Data fetching:** server components hitting the backend API (URL via `NEXT_PUBLIC_API_URL`, DOA-008) with client-side polling only on `/loop`. No Supabase-direct reads from the browser — RLS is locked (DOA-009) and the API is the single contract.
- **State:** none beyond URL params + polling; no Redux/Zustand until proven needed.

## New backend endpoints (thin, over DOA-109 queries)

```
GET  /api/v1/asil/strategies?status=&origin=&limit=&offset=   (leaderboard)
GET  /api/v1/asil/strategies/{hash}                            (detail + evals + lineage)
GET  /api/v1/asil/generations?limit=                           (loop monitor)
POST /api/v1/asil/strategies/{hash}/status                     (approve|reject|kill — auth per DOA-111)
POST /api/v1/asil/schedules/{name}/toggle                      (pause/resume — auth per DOA-111)
```

Pagination and error semantics follow DOA-007's conventions (bounded limits, honest 404 vs 500).

## Steps of completion

1. Backend endpoints + response models (read paths first; write paths land with DOA-111's auth middleware).
2. Leaderboard page with gate chips and caveats tooltip → detail page with curve + caveats block + gate checklist.
3. Loop monitor with generation history + schedule toggle (toggle disabled until DOA-111 lands).
4. Review queue with reason-required actions.
5. Empty states everywhere ("no generations yet — loop starts at 02:00") — day-one experience matters for a system that starts empty.
6. Playwright smoke: leaderboard renders synthetic fixtures; detail shows caveats block; approve flow round-trips a status change.

## Acceptance criteria

- [ ] Owner can go from leaderboard → detail → approve in ≤3 clicks, and the approval reason is visible in status history afterward.
- [ ] No performance number renders anywhere without its caveats block/tooltip (checked in Playwright by asserting the block exists on every metrics view).
- [ ] LLM-origin strategies show their rationale *below* measured metrics, badged as generated text.
- [ ] `/loop` reflects a running generation within one polling interval (≤5 s) and shows `failed:budget` distinctly.
- [ ] UI works with the backend on a non-localhost URL (env-driven, no hardcodes).
