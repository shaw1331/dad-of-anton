---
name: stock-analyst
description: "Financial research analyst for NSE-listed stocks. Use when invoked as /stock-analyst <TICKER> or when the user asks for a stock analysis, research report, or buy/sell view on an Indian equity. Scrubs fundamentals (screener.in), technicals (yfinance), and recent news, then writes a dual-horizon research report with evidence-weighted directional verdicts."
---

# /stock-analyst

Produce a research note for one NSE stock with TWO verdicts — short-term (1–4 weeks, technicals-weighted) and long-term (3–12 months, fundamentals-weighted) — each with a score in [-100, +100], a confidence band, and explicit invalidation conditions.

**Honesty rules (non-negotiable):**
- Verdicts are **evidence-weighted directional biases, never predictions**. Never write "will rise/fall", "guaranteed", "definitely". Use "bias", "suggests", "evidence points to".
- Every number in the report comes **verbatim from the JSON files** — never recompute, never estimate a missing value. Missing data renders as "N/A — data unavailable".
- Every news claim carries a source URL.
- The Disclaimer section from `report_template.md` is mandatory and verbatim.

## Steps

Let `SKILL_DIR=.claude/skills/stock-analyst` (relative to repo root) and `PY=$SKILL_DIR/.venv/bin/python`. Run all scripts from `$SKILL_DIR/scripts/`.

### 1. Setup
- Uppercase the ticker (e.g. `reliance` → `RELIANCE`).
- If `$SKILL_DIR/.venv` doesn't exist: `python3 -m venv $SKILL_DIR/.venv && $SKILL_DIR/.venv/bin/pip install -r $SKILL_DIR/requirements.txt`.
- If the user asked for "fresh"/"latest" data, append `--fresh` to the fetch scripts below (otherwise same-day cached JSON in `analysis-out/<TICKER>/` is reused).

### 2. Fundamentals
Run `$PY fetch_fundamentals.py <TICKER>`.
- Exit 2 → **STOP.** Tell the user the ticker wasn't found on screener.in and to check the NSE symbol. Do not write a report.
- Exit 3 → continue; carry the printed WARNINGs into the report's Risks section.

### 3. Prices + technicals
Run `$PY fetch_prices.py <TICKER>`, then `$PY compute_technicals.py <TICKER>`.
- If prices exit 2 (no Yahoo data) → **fundamentals-only mode**: skip technicals, the short-term verdict will read "Insufficient data". Never invent price data.

### 4. News research (your judgment — the only non-scripted data step)
WebSearch, restricted to the **last 90 days**, using the company name from the fundamentals output:
1. `"<company name>" stock news`
2. `"<company name>" quarterly results`
3. `"<company name>" corporate actions dividend bonus split order win`

Classify each **material** finding and write `analysis-out/<TICKER>/news.json`:

```json
{"items": [{"headline": "...", "date": "YYYY-MM-DD", "source_url": "https://...",
            "direction": "bullish|bearish|neutral", "impact": 1,
            "horizon": "short|long|both", "rationale": "one line"}]}
```

- `impact`: 1 = minor, 2 = meaningful, 3 = major (results surprise, large order, regulatory action, M&A).
- Discard rumors, unattributed items, and anything older than 90 days. Nothing material → write `{"items": []}`. **Do not pad.**
- News is capped at ±15 score points by design — it colors the verdict, it cannot swamp measured data.

### 5. Score
Run `$PY score.py <TICKER>`. Read the printed verdicts and `analysis-out/<TICKER>/scores.json` (the `contributions` array is your evidence table).

### 6. Write the report
Create `reports/<TICKER>_<YYYY-MM-DD>.md` following `report_template.md` exactly (section order, verdict box, evidence tables from `contributions`, scoring appendix, verbatim disclaimer). Narrative interpretation (pros/cons context, peer commentary, news synthesis) is yours; all numbers are quoted from the JSONs.

### 7. Reply to the user
Report path + both verdict lines (verdict, score, confidence, invalidation) + top-3 drivers per horizon. Nothing else.

## Scoring model (mirror — source of truth is `scripts/score.py`; rationale in `references/evidence.md`)

| Signal | ST wt | LT wt | Signal | ST wt | LT wt |
|---|---|---|---|---|---|
| price vs SMA20 | 8 | 0 | P/E vs peer median (quality-gated) | 2 | 8 |
| price vs SMA50 | 6 | 2 | ROE | 1 | 8 |
| price vs SMA200 | 4 | 6 | ROCE | 1 | 8 |
| 50/200 cross state | 5 | 5 | sales growth 3y CAGR | 2 | 8 |
| RSI(14) conditional | 5 | 2 | profit growth 3y CAGR | 2 | 8 |
| MACD | 8 | 2 | earnings surprise (PEAD proxy) | 6 | 5 |
| 52w position (continuation) | 7 | 6 | promoter Δ4q (+1 if small cap) | 2 | 6 |
| volume trend | 5 | 1 | FII Δ4q | 4 | 5 |
| momentum 3m / 6m / 12m | 6/4/0 | 2/5/5 | DII Δ4q | 2 | 3 |
| support/resistance | 5 | 0 | dividend yield | 0 | 2 |

News: ±15 cap. Score = 100·Σ(dir·w)/Σ(w available) + news. Verdicts: ≥+50 Strong Bullish · +20 Bullish · ±19 Neutral · −20 Bearish · ≤−50 Strong Bearish. Confidence = 0.6·signal-agreement + 0.4·data-completeness (Low <0.45 / Medium ≤0.70 / High >0.70).
