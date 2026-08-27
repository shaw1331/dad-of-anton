# DOA-111: Governance & safety rails — human gate, auth, kill switch, audit, framing

- **Type:** Task (governance)
- **Priority:** P1 within epic DOA-100 (M3; auth pieces pulled earlier if endpoints ship earlier)
- **Component:** backend, frontend, docs
- **Depends on:** DOA-106 (nomination flow), DOA-109 (status/audit tables), DOA-110 (surface)

## Problem

An autonomous loop that spends compute, calls external APIs (scraper, prices, optionally an LLM), and produces investment-flavored output needs explicit brakes and accountability: who approved what, how do we stop it *now*, what can the loop never do by itself, and how is the output framed so it isn't mistaken for advice. Cheap to build now; expensive to retrofit after an incident.

## Principles (product policy, enforced by this ticket)

1. **The loop nominates; humans promote.** No code path moves a strategy to `approved` without a human action recorded with reason (DOA-106 selection policy already stops at `candidate_for_review`).
2. **Every state-changing action has an actor and a reason** (already structured in DOA-109's `strategy_status`).
3. **One switch stops everything**, and it fails safe (loop halted > loop running unsupervised).
4. **Research framing everywhere:** persistent UI banner + report footer: educational research, not investment advice, past performance ≠ future results. Non-removable by config.

## Decision 1 — Write-path authentication

The API is currently wide open (localhost CORS is the only "protection"). Write endpoints (approve/kill/pause, workflow trigger) need auth; read endpoints arguably too once real research accumulates.

**A. Static bearer token (env-configured, single user)** — *recommended for v1*
- ✅ Matches reality (N=1 user); ~30 lines (FastAPI dependency checking `Authorization` against `Settings.ASIL_ADMIN_TOKEN`); no session infra; frontend stores it once.
- ❌ No identity granularity ("changed_by" = 'owner' constant); rotation is manual; token in browser storage (acceptable for personal deployment on private network; documented).

**B. Supabase Auth (email magic link) + JWT verification**
- ✅ Real identities for `changed_by`; Supabase already in the stack; ready for a second user.
- ❌ Meaningful integration work (JWT middleware, frontend auth flows, session refresh) for a single-user tool today; auth bugs are the most expensive kind.

**C. Network-level only (VPN/localhost, no app auth).**
- ✅ Zero code. ❌ One misconfigured port-forward = anyone can approve strategies and trigger workflows; indefensible once DOA-110's write endpoints exist.

*Decision: A now; the auth dependency is written as a FastAPI `Depends` so swapping to B later touches one module. Trigger endpoint (`POST /workflows/{name}/trigger`) moves behind the same token — it's a compute-spending endpoint.*

## Decision 2 — Kill switch semantics

**A. DB flag (`system_settings.loop_enabled`) checked at generation start** — *recommended core*
- ✅ Survives restarts; togglable from UI/SQL; scheduler + overlap guard already read DB.
- ❌ Doesn't stop a generation mid-flight (up to 30 min of residual run — acceptable given budget caps).

**B. In-memory flag + cancellation of the running asyncio task.**
- ✅ Instant stop. ❌ Lost on restart (dangerous default-on failure mode if flag defaulted wrong); cancelling mid-evaluation risks partial writes (mitigated by idempotency, but why court it).

**C. Ops-level only (stop the server).**
- ✅ Always available as the last resort (and documented as such). ❌ Stops the API and UI too — you lose the ability to *see* state exactly when worried.

*Decision: A, plus C documented as the hard stop. The flag check also gates the LLM proposer and any future external-spend task individually (`llm_proposer_enabled`), so cost centers can be shut off independently.*

## Decision 3 — Audit depth

**A. Rely on DOA-109's `strategy_status` + `generations.notes`** — covers strategy lifecycle.
**B. Dedicated append-only `audit_log` (actor, action, entity, before/after, at)** for *all* privileged actions (status changes, schedule toggles, kill switch, token-authed triggers) — *recommended*: one generic table + a `record_audit()` helper called from the auth'd endpoints; trivial now, impossible to reconstruct later. ❌ of A alone: schedule toggles and kill-switch flips would be unlogged — precisely the actions you want history for.

## Decision 4 — External-spend budget enforcement point

Budgets exist in DOA-106 (generation caps). Governance adds the *monthly* meter: `spend_meters` table (llm_tokens, evals, scrape_requests per calendar month) incremented by the respective tasks; generation start checks meters vs `Settings` caps; breach → loop auto-pauses (flag flips, audit-logged, UI banner). Alternative (trust per-generation caps × schedule arithmetic) rejected: config drift between cap and cadence is exactly how runaway spend happens.

## Steps of completion

1. `ASIL_ADMIN_TOKEN` setting (+ schema/env example, generation instructions in README); `require_admin` dependency; applied to all write endpoints incl. workflow trigger. 401 vs 403 semantics tested.
2. `system_settings` migration (`loop_enabled`, `llm_proposer_enabled` rows) + generation-start / proposer gates + UI toggle (DOA-110 loop monitor).
3. `audit_log` migration + `record_audit()` + wired into every privileged endpoint; read endpoint `GET /api/v1/asil/audit?limit=` (token-gated).
4. `spend_meters` migration + task increments + generation-start check + auto-pause on breach.
5. Disclaimer banner component (frontend) + report footer text (backend caveats block, extends DOA-107's contract).
6. Runbook `docs/asil-runbook.md`: how to pause, hard-stop, rotate token, raise budgets, and what "stagnated" means.

## Acceptance criteria

- [ ] All write endpoints return 401 without the token, and every 2xx write produces an `audit_log` row with actor + before/after.
- [ ] Flipping `loop_enabled=false` prevents the next scheduled generation (skip logged + visible in UI) without affecting the API.
- [ ] Breaching a monthly meter in a test auto-pauses the loop and shows the UI banner.
- [ ] No code path sets `strategy_status='approved'` with `changed_by='loop'` (test asserts).
- [ ] Disclaimer renders on every page and in every exported/report view.
