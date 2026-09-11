Analyze the following stock using the momentum trading framework defined in the system instructions.

# STOCK

* Company: {company}
* Ticker: {ticker}
* Sector: {sector}
* Industry: {industry}
* Analysis Timeframe: medium_term
* Data As Of: {data_as_of}

# TECHNICAL DATA

## Price

| Metric        |           Value |
| ------------- | --------------: |
| Current Price | {current_price} |
| 1W Return     |     {return_1w} |
| 1M Return     |     {return_1m} |
| 3M Return     |     {return_3m} |
| 6M Return     |     {return_6m} |
| 1Y Return     |     {return_1y} |

## Moving Averages

| Indicator       |             Value |
| --------------- | ----------------: |
| EMA20           |          {ema_20} |
| EMA50           |          {ema_50} |
| EMA200          |         {ema_200} |
| SMA20           |          {sma_20} |
| SMA50           |          {sma_50} |
| SMA200          |         {sma_200} |
| Price vs EMA20  |  {price_vs_ema20} |
| Price vs EMA50  |  {price_vs_ema50} |
| Price vs EMA200 | {price_vs_ema200} |
| MA Alignment    |    {ma_alignment} |

## Momentum Indicators

| Indicator      |            Value |
| -------------- | ---------------: |
| RSI(14)        |            {rsi} |
| MACD           |           {macd} |
| MACD Signal    |    {macd_signal} |
| MACD Histogram | {macd_histogram} |
| ADX            |            {adx} |
| MFI            |            {mfi} |
| CCI            |            {cci} |
| ROC(21)        |         {roc_21} |
| Williams %R    |     {williams_r} |

## Relative Strength

| Benchmark      |      Stock Return |      Benchmark Return | Relative Performance |
| -------------- | ----------------: | --------------------: | -------------------- |
| {rs_benchmark} | {rs_stock_return} | {rs_benchmark_return} | {rs_performance}     |

## Breakout / Support / Resistance

| Level                    |                      Value |
| ------------------------ | -------------------------: |
| Resistance 1             |                       {r1} |
| Resistance 2             |                       {r2} |
| Resistance 3             |                       {r3} |
| Support 1                |                       {s1} |
| Support 2                |                       {s2} |
| Support 3                |                       {s3} |
| Pivot                    |                    {pivot} |
| Distance From Resistance | {distance_from_resistance} |
| Distance From Support    |    {distance_from_support} |

## Volatility

| Metric |         Value |
| ------ | ------------: |
| ATR    |         {atr} |
| ATR %  | {atr_percent} |

# TRADEVIEW CALCULATED LEVELS

The following levels and volume metrics are deterministic calculations produced by the TradeView data pipeline.

Treat these values as supplied input data.

Do NOT recalculate, modify, estimate, or override these values.

| Metric             |                       Value |
| ------------------ | --------------------------: |
| Entry Above        |     {tradeview_entry_above} |
| Stop Loss          |       {tradeview_stop_loss} |
| Target 1           |        {tradeview_target_1} |
| Conviction         |      {tradeview_conviction} |
| Recommendation     |  {tradeview_recommendation} |
| Volume Spike       |    {tradeview_volume_spike} |
| Volume Trend       |    {tradeview_volume_trend} |
| Average Volume 10D |  {tradeview_avg_volume_10d} |
| Average Volume 20D |  {tradeview_avg_volume_20d} |
| Current Volume     |  {tradeview_current_volume} |
| Level Reasoning    | {tradeview_level_reasoning} |

## TRADEVIEW DATA INTERPRETATION RULES

* Treat TradeView calculated levels as deterministic evidence supplied by the input.
* Do not independently calculate entry, stop-loss, targets, conviction, volume spike, or volume trend.
* Do not replace TradeView values with values inferred from other technical indicators.
* `Entry Above` represents the TradeView entry trigger and must not automatically be treated as a resistance level.
* Resistance 1/2/3 represent resistance levels and must be interpreted separately from the TradeView entry trigger.
* Do not assume that Entry Above equals Resistance 1 unless the supplied data explicitly indicates this relationship.
* Use TradeView levels as supporting technical evidence in the momentum analysis.
* The TradeView `recommendation` and `conviction` are inputs, not automatic final decisions.
* Do not blindly follow the TradeView recommendation.
* The final recommendation must still satisfy the momentum framework and decision rules defined in the system instructions.
* If TradeView evidence conflicts with other supplied technical evidence, explicitly identify the conflict and reduce confidence.
* If TradeView data is missing, treat it as unknown rather than neutral.
* When Current Price is below Entry Above, treat the TradeView setup as a pending/untriggered BUY setup unless other supplied data explicitly establishes that the entry condition has already been satisfied.
* Do not describe the TradeView entry as triggered when Current Price < Entry Above.
* Distinguish between the TradeView recommendation/setup, the entry trigger status, and the current momentum condition.
* Do not assume a target or stop-loss has been reached unless the supplied price data explicitly establishes it.
* Use the TradeView `level_reasoning` only as supporting evidence; do not treat its textual conclusion as independently verified fact.

# FUNDAMENTAL CONTEXT

Use fundamentals only as secondary context. Do not treat them as direct momentum evidence.

## Valuation & Profitability

| Metric         |           Value |
| -------------- | --------------: |
| Current Price  | {current_price} |
| Market Cap     | {market_cap} Cr |
| P/E            |            {pe} |
| ROE            |           {roe} |
| ROCE           |          {roce} |
| Book Value     |    {book_value} |
| Dividend Yield |     {div_yield} |

## Latest Financials

| Metric           | {latest_period} |
| ---------------- | --------------: |
| Sales            |      {sales} Cr |
| Operating Profit |  {op_profit} Cr |
| OPM              |           {opm} |
| Net Profit       | {net_profit} Cr |
| EPS              |           {eps} |
| Borrowings       | {borrowings} Cr |

# RECENT NEWS

The following are analyzed news articles for this stock.

{news_section}

# ANALYSIS REQUIREMENTS

* Use only the supplied data.
* Do not invent missing technical indicators.
* Give greater weight to recent momentum evidence.
* Fundamentals are secondary context and must not override technical momentum.
* Use the analyzed news only as secondary context to the technical setup.
* Use TradeView calculated levels as additional technical evidence, but do not blindly follow its recommendation.
* Do not recalculate any TradeView-derived values.
* If critical momentum data is missing, prefer HOLD and reduce confidence.
* Explicitly identify missing data.
* Explicitly identify any conflict between TradeView levels and the broader technical setup.
* If the TradeView recommendation agrees with the broader technical evidence, it may strengthen conviction.
* A TradeView BUY recommendation does not mean the entry has been triggered; determine trigger status separately using Current Price and Entry Above.
* If the TradeView recommendation conflicts with the broader technical evidence, the broader multi-factor momentum framework takes precedence.
* Keep the final recommendation evidence-based and independent of any single calculated signal.
