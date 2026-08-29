# Evidence base for the scoring model

Research performed 2026-08-27 during skill design. Each calibration decision in `scripts/score.py` traces to a finding here. Re-validate periodically — effects decay.

## 1. Momentum works in India at 3–9 month horizons

NSE studies find significant momentum profits for 3–9 month formation/holding periods, turning contrarian at ~3 years; P/E, P/B and **net FII inflows** are significant momentum drivers (VAR analysis). Physical-momentum portfolios on NSE 500 beat NIFTY 50 on return and risk (2014–2021).

- https://www.sciencedirect.com/science/article/pii/S0970389617301647
- https://arxiv.org/abs/2302.13245
- https://www.sciencedirect.com/science/article/abs/pii/S0927538X23002640

**→** `momentum_6m` LT weight 5, `momentum_12m` LT 5, `momentum_3m` ST 6; `fii_delta` raised to 4/5.

## 2. 52-week-high effect (George & Hwang, Journal of Finance 2004)

Nearness to the 52w high forecasts future returns **better than past-return momentum** and does not reverse long-run (anchoring underreaction). Profitable in 18 of 20 international markets.

- https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2004.00695.x
- https://www.sciencedirect.com/science/article/abs/pii/S0261560610001099
- https://quantpedia.com/strategies/52-weeks-high-effect-in-stocks

**→** `position_52w` weighted 7/6; within 5% of high scores **+1 (continuation)**, never "overbought"; near 52w low scores −1 (not "cheap").

## 3. Short-term reversal is conditional

One-month reversal exists but disappears — and flips to **momentum** — for high-turnover stocks near their 52w high. Reversal stems from liquidity demand; news-driven moves continue.

- https://www.sciencedirect.com/science/article/abs/pii/S0927539824000902
- https://www.sciencedirect.com/science/article/abs/pii/S0378426621000261
- https://quantpedia.com/strategies/short-term-reversal-in-stocks

**→** RSI ST weight cut to 5; RSI>70 near 52w high = neutral (not bearish); oversold bounce only +0.5 and only above SMA200.

## 4. Post-earnings-announcement drift (PEAD) confirmed in India

Multiple NSE studies (Sehgal & Jain 2015; Sen 2009; Singh et al. 2018; NSE-listed samples 2014–2018) confirm drift in the direction of earnings surprises persisting up to ~3 quarters; announcement-reaction (EAR) based drift is stronger than SUE and doesn't reverse.

- https://www.scirp.org/journal/paperinformation?paperid=88060
- https://www.researchgate.net/publication/352923666
- https://www.sciencedirect.com/science/article/pii/S2214635020303750

**→** `earnings_surprise` signal (latest-qtr net profit YoY) weighted 6/5 — meaningful in BOTH horizons; results news items deserve impact 2–3 in `news.json`.

## 5. Promoter/insider buying predicts returns in India, strongest for small caps

Insider purchases are followed by statistically significant positive abnormal returns; the effect is stronger for promoter trades and small-cap firms (information asymmetry).

- https://www.ijllr.com/post/do-insider-trades-predict-future-stock-returns-evidence-from-indian-stock-market
- https://nsearchives.nseindia.com/web/sites/default/files/inline-files/India_Ownership_Report_Jun2024.pdf

**→** `promoter_delta` 2/6 with a +1 weight amplifier (both horizons) when market cap < ₹20,000 Cr.

## 6. Value alone is a trap; value + quality works in India

Pure low-P/E portfolios are contaminated by deteriorating businesses; combining low P/E with high/improving ROE earned ~11.4% net CAGR over an 18-year NSE backtest (after costs/taxes). Quality and low-volatility factor indices have led Indian factor performance.

- https://backtestindia.com/blog/value-quality-investing-india-backtest
- https://www.business-standard.com/amp/finance/personal-finance/india-market-strategy-quality-and-low-volatility-factors-lead-the-way-124093000120_1.html

**→** `pe_vs_peers` is quality-gated: cheap (≤0.8× peer median) scores +1 **only if ROE or ROCE ≥ 15%**, else 0. ROE/ROCE thresholds: +1 at ≥20, +0.5 at ≥15.

## 7. Moving-average rule evidence on Indian indices is mixed

South Asian market studies find MA rules predictive vs buy-and-hold; more recent Nifty crossover studies find no statistically significant edge. Trend *state* is kept at moderate weight; fresh crossovers are annotated but not extra-weighted.

- https://www.researchgate.net/publication/325300340
- https://www.academia.edu/56764878
- https://mgmt.cmb.ac.lk/cbj/wp-content/uploads/2020/06/2.-Technical-trading-rules.pdf

**→** SMA-position signals 8/6/4 ST, cross state 5/5; no bonus for recent crossovers.

## Known limitations (stated in every report via the Disclaimer + Risks sections)

- No point-in-time fundamentals history: screener shows current data; backtest-grade validation of this exact model is future work (see jira/DOA-100 ASIL epic — the loop can eventually calibrate these weights empirically).
- Peer P/E medians use screener's peer set, which can mix conglomerates with pure-plays.
- News classification is LLM judgment; capped at ±15 points by design.
- Survivorship and small-sample effects apply to all cited backtests.
