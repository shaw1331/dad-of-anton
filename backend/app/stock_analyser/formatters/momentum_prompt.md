Analyze the following stock using the momentum trading framework defined in the system instructions.

# STOCK

- Company: {company}
- Ticker: {ticker}
- Sector: {sector}
- Industry: {industry}
- Analysis Timeframe: medium_term
- Data As Of: {data_as_of}

# TECHNICAL DATA

## Price

| Metric | Value |
|---|---:|
| Current Price | {current_price} |
| 1M Return | {return_1m} |
| 3M Return | {return_3m} |
| 6M Return | {return_6m} |
| 1Y Return | {return_1y} |

## Moving Averages

| Indicator | Value |
|---|---:|
| EMA20 | {ema_20} |
| EMA50 | {ema_50} |
| EMA200 | {ema_200} |
| SMA20 | {sma_20} |
| SMA50 | {sma_50} |
| SMA200 | {sma_200} |
| Price vs EMA20 | {price_vs_ema20} |
| Price vs EMA50 | {price_vs_ema50} |
| Price vs EMA200 | {price_vs_ema200} |
| MA Alignment | {ma_alignment} |

## Momentum Indicators

| Indicator | Value |
|---|---:|
| RSI(14) | {rsi} |
| MACD | {macd} |
| MACD Signal | {macd_signal} |
| MACD Histogram | {macd_histogram} |
| ADX | {adx} |
| MFI | {mfi} |
| CCI | {cci} |
| ROC(21) | {roc_21} |
| Williams %R | {williams_r} |

## Relative Strength

| Benchmark | Stock Return | Benchmark Return | Relative Performance |
|---|---:|---:|---|
| {rs_benchmark} | {rs_stock_return} | {rs_benchmark_return} | {rs_performance} |

## Breakout / Support / Resistance

| Level | Value |
|---|---:|
| Resistance 1 | {r1} |
| Resistance 2 | {r2} |
| Resistance 3 | {r3} |
| Support 1 | {s1} |
| Support 2 | {s2} |
| Support 3 | {s3} |
| Pivot | {pivot} |
| Distance From Resistance | {distance_from_resistance} |
| Distance From Support | {distance_from_support} |

## Volatility

| Metric | Value |
|---|---:|
| ATR | {atr} |

# FUNDAMENTAL CONTEXT

Use fundamentals only as secondary context. Do not treat them as direct momentum evidence.

## Valuation & Profitability

| Metric | Value |
|---|---:|
| Current Price | {current_price} |
| Market Cap | {market_cap} Cr |
| P/E | {pe} |
| ROE | {roe} |
| ROCE | {roce} |
| Book Value | {book_value} |
| Dividend Yield | {div_yield} |

## Latest Financials

| Metric | {latest_period} |
|---|---:|
| Sales | {sales} Cr |
| Operating Profit | {op_profit} Cr |
| OPM | {opm} |
| Net Profit | {net_profit} Cr |
| EPS | {eps} |
| Borrowings | {borrowings} Cr |

# RECENT NEWS

The following are analyzed news articles for this stock.

{news_section}
# ANALYSIS REQUIREMENTS

- Use only the supplied data.
- Do not invent missing technical indicators.
- Give greater weight to recent momentum evidence.
- Fundamentals are secondary context and must not override technical momentum.
- Use the analyzed news only as secondary context to the technical setup.
- If critical momentum data is missing, prefer HOLD and reduce confidence.
- Explicitly identify missing data.
