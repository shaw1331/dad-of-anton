# jira/ — Improvement backlog for dad-of-anton

Generated from a full index of the repository on 2026-08-27 (commit `0d2c319`). Each ticket is self-contained: problem, steps of completion, before/after, and the exact change as a `+`/`-` diff.

**Executing agents: read [AGENT-HARNESS.md](AGENT-HARNESS.md) first — it has the repo map, DO/DON'T rules, verification commands, and the required landing order.**

## Tickets

| ID | Title | Type | Priority | Component |
|---|---|---|---|---|
| [DOA-001](DOA-001-supabase-client-fail-fast.md) | Fail fast when Supabase is not configured (`None`-client crash) | Bug | **P0** | backend/core |
| [DOA-005](DOA-005-nonblocking-db-calls-in-async-runner.md) | Sync Supabase calls block the event loop in `run_workflow` | Bug | **P0** | backend/workflow |
| [DOA-006](DOA-006-orchestrator-crash-safety.md) | Runs can get stuck in `running` forever; ABC signature wrong | Bug | **P0** | backend/workflow |
| [DOA-002](DOA-002-dependency-injection-single-orchestrator.md) | Remove dead orchestrator singleton; wire routes via `Depends` | Refactor | P1 | backend/api |
| [DOA-003](DOA-003-status-enums.md) | Replace free-string statuses with enums | Hardening | P1 | backend/workflow |
| [DOA-004](DOA-004-timezone-aware-timestamps.md) | Timezone-aware timestamps; drop deprecated `datetime.utcnow` | Bug | P1 | backend/models |
| [DOA-007](DOA-007-api-error-handling-and-pagination.md) | Bare-except 404 masking, unbounded `/runs`, duplicate health | Bug | P1 | backend/api |
| [DOA-008](DOA-008-frontend-config-and-env-safety.md) | Configurable API URL; crash-safe Supabase env handling | Bug | P1 | frontend |
| [DOA-009](DOA-009-lock-down-rls-service-role-key.md) | Lock down wide-open RLS; use service-role key server-side | Security | P1 | backend/db |
| [DOA-010](DOA-010-backend-test-suite.md) | Add backend pytest suite (orchestrator + routes) | Tests | P1 | backend/tests |
| [DOA-014](DOA-014-parameterized-workflow-tasks.md) | Workflow configs can't parameterize tasks; sample sleeps 60 s | Design gap | P1 | backend/workflow |
| [DOA-011](DOA-011-start-sh-hardening.md) | `start.sh`: clean shutdown, fail-fast, no orphan processes | DevEx | P2 | tooling |
| [DOA-012](DOA-012-scraper-retry-semantics.md) | Scraper: honor `Retry-After`; don't save partial index CSVs | Data quality | P2 | screener_scraper |
| [DOA-013](DOA-013-settings-modernization.md) | pydantic-settings v2 style; env-driven CORS | Tech debt | P2 | backend/core |

## Recommended landing order

1. **Independent, any time:** DOA-001, DOA-004, DOA-011, DOA-012, DOA-013
2. **Routes chain:** DOA-002 → DOA-007 → DOA-008
3. **Orchestrator cluster (same file — this order or one PR):** DOA-006 → DOA-014 → DOA-005 → DOA-003
4. **After the above:** DOA-009 (needs DOA-001), DOA-010 (needs DOA-002)

## Epic: Auto Strategy Improvement Loop (ASIL) — DOA-100 series

Product initiative connecting the scraper → orchestrator → frontend into one loop: generate stock-screening strategies from scraped fundamentals, backtest honestly, select survivors, mutate, repeat — with humans approving promotions. Start with the epic PRD; every child ticket carries full approach analysis with pros/cons.

| ID | Title | Milestone |
|---|---|---|
| [DOA-100](DOA-100-epic-auto-strategy-improvement-loop.md) | **EPIC/PRD** — vision, loop shape, milestones, risks, open questions | — |
| [DOA-101](DOA-101-data-foundation-supabase-snapshots.md) | Point-in-time fundamentals snapshots in Supabase (CSV importer vs direct-write vs full merge) | M0 |
| [DOA-102](DOA-102-price-history-data-source.md) | Price history source decision + ingest (bhavcopy vs yfinance vs paid vs self-built) | M0 |
| [DOA-103](DOA-103-strategy-representation.md) | Strategy representation contract (JSON DSL vs Python plugins vs SQL vs hybrid) | M1 |
| [DOA-104](DOA-104-backtest-evaluation-engine.md) | Backtest/evaluation engine (build minimal vs library vs SQL-native) + validation harness | M1 |
| [DOA-105](DOA-105-candidate-strategy-generation.md) | Candidate generation (templates/random vs genetic vs Bayesian vs LLM) | M2 |
| [DOA-106](DOA-106-improvement-loop-controller.md) | Loop controller — generations, selection policy, budgets, stagnation stop | M2 |
| [DOA-107](DOA-107-overfitting-guardrails.md) | Overfitting guardrails — splits, walk-forward, deflated Sharpe, holdout burn registry | M2 |
| [DOA-108](DOA-108-orchestrator-platform-upgrades.md) | Orchestrator upgrades — data passing, scheduling, retries, fan-out (per-capability options) | M1/M2 |
| [DOA-109](DOA-109-experiment-tracking-schema.md) | Experiment tracking schema — strategies, evaluations, generations, lineage, audit-grade constraints | M1 |
| [DOA-110](DOA-110-strategy-lab-ui.md) | Strategy Lab UI — leaderboard, detail with caveats, loop monitor, review queue | M3 |
| [DOA-111](DOA-111-governance-safety-rails.md) | Governance — auth, kill switch, audit log, spend meters, research-not-advice framing | M3 |

**Prerequisites from the maintenance backlog:** DOA-001, DOA-005, DOA-006, DOA-009, DOA-014 must land before M1 (the loop can't run on an orchestrator that blocks the event loop, strands runs, and can't parameterize tasks).

## Themes found during indexing

- **Reliability of the workflow runner** (DOA-005, DOA-006, DOA-014): the orchestrator is the core of the backend and currently blocks the event loop, can strand runs in `running`, and can't parameterize tasks.
- **Fail fast on misconfiguration** (DOA-001, DOA-008): both backend and frontend degrade into confusing runtime crashes when env vars are missing.
- **Contract tightening** (DOA-003, DOA-004, DOA-007): statuses, timestamps, and error semantics are currently looser than the DB schema implies.
- **Security** (DOA-009): the publishable anon key currently has full read/write/delete on workflow tables.
- **Safety net** (DOA-010): zero tests today; everything above should land with the suite in place or added alongside.
