# DOA-102: ASIL price & returns data source — pick one and build the ingest

- **Type:** Task (platform / build-vs-buy decision)
- **Priority:** P0 within epic DOA-100 (M0)
- **Component:** backend/db, new ingest job
- **Depends on:** DOA-101 (shares `scrape_runs` pattern and ticker universe)

## Problem

Backtesting (DOA-104) needs **daily historical prices** (ideally adjusted for splits/bonuses/dividends) for every ticker in the universe, going back ≥5 years. The screener scraper captures only *current* price / 52-week high-low — useless for historical simulation. Without a price series there is no evaluation, and without evaluation there is no loop. This is the single biggest external dependency of the epic.

## Requirements

1. Daily OHLCV (close is the hard requirement) for ~350 NSE tickers, ≥5y history, updatable daily.
2. Corporate-action adjustment (splits/bonuses) — unadjusted series silently fabricates ±50% "returns".
3. Ticker join key compatible with screener tickers (screener slug ≈ NSE symbol for most; mapping table for exceptions).
4. Licensing that permits internal research use.

## Approaches

### A. NSE bhavcopy (official daily EOD files, free)
Download the official daily EOD archive; NSE publishes every trading day.

- ✅ Authoritative, free, complete for NSE; no per-ticker rate limits (one file per day covers everything).
- ✅ Bulk historical backfill possible (years of daily files).
- ❌ **Unadjusted** — must also ingest corporate-action files and build adjustment logic ourselves (real, error-prone work; this is where most home-grown backtests go wrong).
- ❌ NSE has repeatedly changed URLs/formats and added bot protection; scraper maintenance burden is nontrivial.
- ❌ Symbol changes/delistings need manual curation.

### B. `yfinance` (Yahoo Finance, free, unofficial)
`{ticker}.NS` symbols; adjusted closes built in.

- ✅ Adjusted prices out of the box (`Adj Close`) — kills the hardest problem in A.
- ✅ 5–20y history in one call per ticker; trivial Python integration; zero cost.
- ✅ Good-enough coverage for NSE large/mid/small-cap names in our indexes.
- ❌ Unofficial API: breaks a few times a year, can be rate-limited/blocked; not a licensing-clean source for anything commercial.
- ❌ Data quality is "usually fine": occasional bad ticks, missing days, silent symbol mismatches — needs sanity checks.
- ❌ ~350 sequential requests per backfill; needs the same politeness machinery as the screener scraper (reuse `utils.get_page` patterns).

### C. Paid API (e.g. EOD Historical Data, Tiingo, Polygon-equivalents with NSE coverage)
- ✅ SLA, support, clean adjusted data, corporate actions included; one integration, done.
- ✅ Licensing clarity if this ever becomes more than personal research.
- ❌ Cost (typically $30–80/mo for NSE EOD) for a single-user experimental product; procurement friction.
- ❌ Vendor lock-in shapes the schema if we're careless (mitigate: land vendor data into *our* schema, never query vendor live from the loop).

### D. Build price history from our own daily screener snapshots ("Current Price" metric)
- ✅ Zero new dependencies.
- ❌ History starts today; a meaningful backtest window arrives in ~2027. Non-starter as the primary source; useful only as a cross-check on other sources.

**Recommendation:** **B (yfinance) for M0/M1**, wrapped behind our own `prices` table so nothing downstream knows the source; **decide on C at M2 exit** using observed breakage rate and whether the product graduates beyond personal research. A is the fallback if Yahoo blocks us — and its adjustment problem is why it isn't first choice. D is a validation signal only.

## Schema (new migration)

```sql
CREATE TABLE prices (
    ticker text NOT NULL,
    trade_date date NOT NULL,
    close numeric NOT NULL,          -- adjusted
    close_unadjusted numeric,
    volume bigint,
    source text NOT NULL DEFAULT 'yfinance',
    ingested_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (ticker, trade_date)
);

CREATE TABLE ticker_aliases (
    screener_ticker text PRIMARY KEY,   -- from index_constituents
    price_symbol text NOT NULL,         -- e.g. 'RELIANCE.NS'
    note text
);
```

- PK `(ticker, trade_date)` → idempotent re-ingest, natural join with `fundamentals_snapshots(as_of)`.
- `source` column keeps the door open for switching vendors without a migration.

## Steps of completion

1. Migration above; RLS locked (service key only).
2. `app/asil/price_ingest.py`: backfill mode (5y, all tickers from `index_constituents`) and daily mode (yesterday only), with retry/backoff and per-ticker failure isolation (one bad ticker ≠ failed run).
3. Auto-populate `ticker_aliases` with the `.NS` default; log unresolved tickers for manual mapping.
4. Data-quality gates: no negative/zero closes; day-over-day move >40% flags the ticker for review (likely unhandled corporate action); gaps vs NSE trading calendar reported.
5. `IngestPricesTask` workflow task + `daily_data` workflow = [ScrapeImport (DOA-101), IngestPrices] — becomes the loop's heartbeat.
6. Cross-check job: screener "Current Price" snapshot vs same-day close within 2% for ≥95% of tickers, else alert.

## Acceptance criteria

- [ ] ≥95% of universe tickers have ≥5y of daily closes after backfill; the remainder are listed in an exceptions report.
- [ ] Re-running ingest for the same window changes no row counts.
- [ ] A known historical split (pick one from the universe) shows a smooth adjusted series and a visible jump in `close_unadjusted`.
- [ ] Daily mode completes < 15 min and marks failures per-ticker, not per-run.

## Open questions

- Is delisted-stock history (true survivorship-bias handling) required for v1? *PM stance: no — universe = current index membership PIT-tracked going forward (DOA-101); document the residual bias in every backtest report (DOA-107).*
